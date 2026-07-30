/**
 * valeria-chat-page.pom.ts — Page Object Model para ValeriaChat organismo
 *
 * F1-S6 vitalia-fase1-valeria-chat-skeleton — T-7
 *
 * spec_anchor: 04-validators.yaml § poms_required · 03-arch.md § 3.2 POM contract
 *
 * Locators: data-testid first, ARIA como fallback.
 * Sin assertions en métodos POM — solo acciones + locators.
 *
 * Cubre SC-1..SC-7 gherkin scenarios per 01-spec.md.
 *
 * Test route: `/test-stack/shell-layout` (public, no Clerk auth required)
 * Chat store seed: via `window.__chatStoreSeed__` addInitScript BEFORE navigation.
 *
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";
import type { ChatMessage } from "../../../src/stores/chat-store";

// ---------------------------------------------------------------------------
// ValeriaChatPage — POM
// ---------------------------------------------------------------------------

export class ValeriaChatPage {
  readonly page: Page;

  constructor(public readonly pageProp: Page) {
    this.page = pageProp;
  }

  // ── Navigation ─────────────────────────────────────────────────────────────

  /**
   * Seed the chat store with specific messages via `window.__chatStoreSeed__`.
   * MUST be called BEFORE `goto()` so addInitScript fires before page scripts.
   *
   * The chat-store reads `window.__chatStoreSeed__` on initialization (non-prod only).
   * Calling this after navigation has no effect.
   *
   * @param messages - array of ChatMessage to seed (use [] for empty state)
   */
  async seedChatStore(messages: ChatMessage[]): Promise<void> {
    await this.page.addInitScript((msgs: ChatMessage[]) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (window as any).__chatStoreSeed__ = msgs;
    }, messages as ChatMessage[]);
  }

  /**
   * Seed the chat store with empty messages array (empty state).
   * MUST be called BEFORE `goto()`.
   */
  async seedChatStoreEmpty(): Promise<void> {
    await this.seedChatStore([]);
  }

  /**
   * Navigate to the shell organism test route.
   * Pre-seed the shell state so Valeria panel is visible (full mode).
   *
   * @param tenantId - tenant ID for the URL param (default: 'tenant-vitalia-demo')
   */
  async goto(tenantId: string = "tenant-vitalia-demo"): Promise<void> {
    // Seed shell localStorage to ensure Valeria panel is in full/agentic mode
    await this.page.addInitScript(
      ({
        shellKey,
        shellStateStr,
        themeKey,
      }: {
        shellKey: string;
        shellStateStr: string;
        themeKey: string;
      }) => {
        localStorage.setItem(shellKey, shellStateStr);
        localStorage.setItem(themeKey, "light");
      },
      {
        shellKey: "vitalia-shell-state",
        shellStateStr: JSON.stringify({
          state: { shellMode: "agentic", valeriaState: "full" },
          version: 0,
        }),
        themeKey: "vitalia-theme",
      },
    );

    await this.page.goto(`/test-stack/shell-layout`);
    // Wait for the chat organism to be visible
    await this.page
      .locator('[data-testid="valeria-chat"]')
      .waitFor({ state: "visible", timeout: 15_000 });

    void tenantId; // suppress unused variable — URL is public test route
  }

  // ── Locators ───────────────────────────────────────────────────────────────

  /** Chat header container */
  getChatHeader(): Locator {
    return this.page.locator('[data-testid="chat-header"]');
  }

  /** Mode pill badge ("🤖 Modo agente") */
  getModePill(): Locator {
    return this.page.locator('[data-testid="chat-mode-pill"]');
  }

  /** Messages log container */
  getMessages(): Locator {
    return this.page.locator('[data-testid="chat-messages"]');
  }

  /**
   * Get nth message bubble (0-indexed).
   * Counts only `[data-testid=msg-bubble]` — does NOT include delegate/thinking markers.
   *
   * @param index - 0-based index of the bubble
   */
  getMessage(index: number): Locator {
    return this.page.locator('[data-testid="msg-bubble"]').nth(index);
  }

  /** All message bubbles (excludes delegate + thinking) */
  getAllBubbles(): Locator {
    return this.page.locator('[data-testid="msg-bubble"]');
  }

  /** Delegate marker ("→ delegando a [pill]") */
  getDelegateMarker(): Locator {
    return this.page.locator('[data-testid="msg-delegate"]');
  }

  /** Thinking indicator (agent typing bubble) */
  getThinkingIndicator(): Locator {
    return this.page.locator('[data-testid="msg-thinking"]');
  }

  /** Composer textarea */
  getComposer(): Locator {
    return this.page.locator('[data-testid="composer-input"]');
  }

  /** Send button ("Enviar") */
  getSendButton(): Locator {
    return this.page.locator('[data-testid="composer-send"]');
  }

  /**
   * Empty state heading locator ("Empieza una conversación").
   * Only visible when messages array is empty.
   */
  getEmptyState(): Locator {
    return this.page.getByText("Empieza una conversación");
  }

  // ── Actions ────────────────────────────────────────────────────────────────

  /**
   * Type a message in the composer and press Enter to send.
   * Waits for a new msg-bubble to appear after send.
   *
   * @param text - message text to send
   */
  async sendMessage(text: string): Promise<void> {
    const composer = this.getComposer();
    await composer.click();
    await composer.fill(text);
    const beforeCount = await this.getAllBubbles().count();
    await composer.press("Enter");
    // Wait for new bubble to appear (user message)
    await this.page
      .locator('[data-testid="msg-bubble"]')
      .nth(beforeCount)
      .waitFor({ state: "visible", timeout: 5_000 });
  }

  /**
   * Press Shift+Enter in the composer (inserts newline without sending).
   */
  async pressShiftEnter(): Promise<void> {
    await this.getComposer().press("Shift+Enter");
  }

  /**
   * Press Enter in the composer (sends message).
   */
  async pressEnter(): Promise<void> {
    await this.getComposer().press("Enter");
  }

  /**
   * Get current message bubble count.
   */
  async getMessageCount(): Promise<number> {
    return await this.getAllBubbles().count();
  }

  /**
   * Wait for the chat store status to reach a specific value.
   * Uses `window.__chatStore__` if exposed, otherwise polls the DOM.
   *
   * @param status - expected status value
   */
  async waitForStatus(status: "idle" | "thinking"): Promise<void> {
    await this.page.waitForFunction(
      (s: string) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const store = (window as any).__chatStore__;
        if (store && typeof store.getState === "function") {
          return store.getState().status === s;
        }
        // Fallback: check DOM for thinking indicator presence/absence
        const thinking = document.querySelector('[data-testid="msg-thinking"]');
        return s === "thinking" ? !!thinking : !thinking;
      },
      status,
      { timeout: 5_000 },
    );
  }

  /**
   * Get the active agent from the chat store via window evaluation.
   * Returns null if store not accessible.
   */
  async getActiveAgent(): Promise<string | null> {
    return await this.page.evaluate(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const store = (window as any).__chatStore__;
      if (store && typeof store.getState === "function") {
        return store.getState().activeAgent as string;
      }
      return null;
    });
  }

  /**
   * Clear all messages via store.getState().clearMessages().
   * No-op if store not accessible via window.
   */
  async clearMessages(): Promise<void> {
    await this.page.evaluate(() => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const store = (window as any).__chatStore__;
      if (store && typeof store.getState === "function") {
        store.getState().clearMessages();
      }
    });
  }

  // ── Viewport / theme helpers ───────────────────────────────────────────────

  /**
   * Set viewport to specified dimensions.
   *
   * @param width - viewport width in pixels
   * @param height - viewport height in pixels
   */
  async setViewport(width: number, height: number): Promise<void> {
    await this.page.setViewportSize({ width, height });
  }

  /**
   * Set the theme (light | dark | system) via localStorage + reload.
   * Note: addInitScript cannot be called after navigation — use this for
   * switching theme after initial navigation.
   *
   * @param theme - target theme value
   */
  async setTheme(theme: "light" | "dark" | "system"): Promise<void> {
    await this.page.evaluate((t: string) => {
      localStorage.setItem("vitalia-theme", t);
      // Trigger next-themes to pick up the change
      document.documentElement.classList.toggle("dark", t === "dark");
      // Dispatch storage event so next-themes reacts (cross-tab simulation)
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: "vitalia-theme",
          newValue: t,
        }),
      );
    }, theme);
  }
}
