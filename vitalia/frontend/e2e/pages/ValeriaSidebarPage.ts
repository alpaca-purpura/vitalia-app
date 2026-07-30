/**
 * ValeriaSidebarPage.ts — Page Object Model para ValeriaSidebar organismo
 *
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8
 *
 * Locators: data-testid first, ARIA como fallback.
 * Sin assertions en métodos POM — solo acciones + locators.
 *
 * Cubre SC-1..SC-9 gherkin scenarios per 01-spec.md.
 *
 * localStorage keys (must stay in sync with shell-store.ts):
 *   SHELL_STORAGE_KEY = 'vitalia-shell-state'
 *
 * Test route: `/test-stack/shell-layout` (public, no Clerk auth required)
 *
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import type { Page, Locator } from "@playwright/test";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ValeriaState = "full" | "rail" | "collapsed";
export type ShellMode = "agentic" | "web";
export type ThemeValue = "light" | "dark" | "system";

export interface ValeriaSidebarStorageState {
  valeriaState?: ValeriaState;
  shellMode?: ShellMode;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SHELL_STORAGE_KEY = "vitalia-shell-state";

// ---------------------------------------------------------------------------
// ValeriaSidebarPage — POM
// ---------------------------------------------------------------------------

export class ValeriaSidebarPage {
  readonly page: Page;

  // ── Core locators ──────────────────────────────────────────────────────────

  /** The main ValeriaSidebar aside element (desktop + mobile drawer both share testid) */
  readonly sidebar: Locator;

  /** Top bar hamburger button (mobile — opens drawer) */
  readonly hamburger: Locator;

  /** History search input (searchbox role) */
  readonly historySearch: Locator;

  /** Empty state inline element (no results in history) */
  readonly emptyState: Locator;

  /** Mobile drawer backdrop */
  readonly drawerBackdrop: Locator;

  /** Mobile drawer close button (X button inside drawer header) */
  readonly drawerCloseBtn: Locator;

  /** Composer placeholder (receives Cmd+K focus) */
  readonly composer: Locator;

  /** Live region (role=status, announces state changes to screen readers) */
  readonly liveRegion: Locator;

  // ── TopBar locators ────────────────────────────────────────────────────────

  /** Fixed top navigation bar */
  readonly topBar: Locator;

  // ── Rail button locators ───────────────────────────────────────────────────

  /** Rail: toggle to full (PanelLeftOpen icon) */
  readonly railOpenHistoryBtn: Locator;

  /** Rail: new conversation (Plus icon) */
  readonly railNewConversationBtn: Locator;

  /** Rail: search / focus composer (Search icon) */
  readonly railSearchBtn: Locator;

  /** Rail: collapse to web mode (PanelLeftClose icon).
   *  Note: TooltipTrigger wraps button — use clickRailCollapseBtn() to dispatch
   *  a click event that triggers React's synthetic event handler correctly. */
  readonly railCollapseBtn: Locator;

  // ---------------------------------------------------------------------------

  constructor(page: Page) {
    this.page = page;

    this.topBar = page.locator('header[role="banner"]').first();
    this.sidebar = page.getByTestId("valeria-sidebar");
    this.hamburger = page.getByTestId("topbar-hamburger");
    this.historySearch = page.getByRole("searchbox", {
      name: /buscar conversaci[oó]n/i,
    });
    this.emptyState = page.getByTestId("history-empty-state");
    this.drawerBackdrop = page.getByTestId("valeria-drawer-backdrop");
    this.drawerCloseBtn = page.getByTestId("valeria-drawer-close");
    this.composer = page.locator("#valeria-composer-placeholder");
    this.liveRegion = page.getByRole("status").filter({ hasText: /Valeria/ });

    // Rail buttons — identified by aria-label (Spanish neutro)
    this.railOpenHistoryBtn = page.getByRole("button", {
      name: /historial/i,
    });
    this.railNewConversationBtn = page.getByRole("button", {
      name: /nueva conversaci[oó]n/i,
    });
    this.railSearchBtn = page.getByRole("button", {
      name: /buscar|cmd\+k/i,
    });
    this.railCollapseBtn = page.getByRole("button", {
      name: /cerrar valeria/i,
    });
  }

  // ── Navigation ─────────────────────────────────────────────────────────────

  /**
   * Navigate to the shell organism test route with pre-seeded localStorage state.
   * Uses addInitScript BEFORE navigation so Zustand hydrates from this state.
   *
   * @param valeriaState - initial Valeria panel state
   * @param shellMode - initial shell mode (agentic | web)
   * @param theme - initial theme (light | dark)
   */
  async goto(
    options: {
      valeriaState?: ValeriaState;
      shellMode?: ShellMode;
      theme?: ThemeValue;
    } = {},
  ): Promise<void> {
    const {
      valeriaState = "full",
      shellMode = "agentic",
      theme = "light",
    } = options;

    await this.page.addInitScript(
      ({
        key,
        statePayload,
        themeKey,
        themeValue,
      }: {
        key: string;
        statePayload: string;
        themeKey: string;
        themeValue: string;
      }) => {
        localStorage.setItem(key, statePayload);
        localStorage.setItem(themeKey, themeValue);
      },
      {
        key: SHELL_STORAGE_KEY,
        statePayload: JSON.stringify({
          state: { valeriaState, shellMode },
          version: 0,
        }),
        themeKey: "vitalia-theme",
        themeValue: theme,
      },
    );

    await this.page.goto("/test-stack/shell-layout");
    await this.sidebar.waitFor({ state: "attached", timeout: 10_000 });
  }

  // ── Keyboard interaction ───────────────────────────────────────────────────

  /**
   * Press a keyboard shortcut.
   * Supports bare keys (r, f, c, n, Escape) and modified keys (Cmd/Ctrl+K).
   *
   * @param key - key to press (e.g. 'r', 'f', 'Escape', 'k')
   * @param modifiers - optional modifiers
   */
  async pressShortcut(
    key: string,
    modifiers: { meta?: boolean; ctrl?: boolean } = {},
  ): Promise<void> {
    if (modifiers.meta) {
      await this.page.keyboard.press(`Meta+${key}`);
    } else if (modifiers.ctrl) {
      await this.page.keyboard.press(`Control+${key}`);
    } else {
      await this.page.keyboard.press(key);
    }
  }

  // ── Store state access ────────────────────────────────────────────────────

  /**
   * Read current valeriaState from localStorage.
   * Returns null if key absent or JSON parse fails.
   */
  async getValeriaState(): Promise<ValeriaState | null> {
    return await this.page.evaluate((key) => {
      try {
        const raw = localStorage.getItem(key);
        if (!raw) return null;
        const parsed = JSON.parse(raw) as {
          state?: { valeriaState?: string };
        };
        return (parsed.state?.valeriaState as ValeriaState) ?? null;
      } catch {
        return null;
      }
    }, SHELL_STORAGE_KEY);
  }

  /**
   * Read current shellMode from localStorage.
   * Returns null if key absent or JSON parse fails.
   */
  async getShellMode(): Promise<ShellMode | null> {
    return await this.page.evaluate((key) => {
      try {
        const raw = localStorage.getItem(key);
        if (!raw) return null;
        const parsed = JSON.parse(raw) as {
          state?: { shellMode?: string };
        };
        return (parsed.state?.shellMode as ShellMode) ?? null;
      } catch {
        return null;
      }
    }, SHELL_STORAGE_KEY);
  }

  /**
   * Read full parsed shell storage state.
   * Returns null if key absent or JSON parse fails.
   */
  async getStorageState(): Promise<ValeriaSidebarStorageState | null> {
    return await this.page.evaluate((key) => {
      try {
        const raw = localStorage.getItem(key);
        if (!raw) return null;
        const parsed = JSON.parse(raw) as {
          state?: ValeriaSidebarStorageState;
        };
        return parsed.state ?? null;
      } catch {
        return null;
      }
    }, SHELL_STORAGE_KEY);
  }

  // ── Rail button click helpers ─────────────────────────────────────────────

  /**
   * Click the collapse button on the Rail.
   * Uses dispatchEvent('click') to bypass the Next.js dev portal overlay
   * that intercepts pointer events in development mode.
   * This triggers React's onClick synthetic handler correctly.
   */
  async clickRailCollapseBtn(): Promise<void> {
    await this.railCollapseBtn.dispatchEvent("click");
  }

  // ── Reload without re-seeding ─────────────────────────────────────────────

  /**
   * Reload the page without re-seeding localStorage.
   * Zustand persist reads from the existing localStorage on mount.
   * Use this to verify persist behavior — distinct from goto() which seeds initScript.
   *
   * Note: addInitScript from a previous goto() call WILL re-fire on reload.
   * To test Zustand persist, read localStorage state BEFORE reload, then verify
   * the persisted value is what you set, rather than reloading and re-reading.
   */
  async reloadAndWait(): Promise<void> {
    await this.page.reload();
    await this.page.waitForLoadState("networkidle");
    await this.sidebar.waitFor({ state: "attached", timeout: 10_000 });
  }

  // ── Store manipulation ────────────────────────────────────────────────────

  /**
   * Set Zustand store state directly via window.useShellStore (adversarial / test helper).
   * Does NOT reload — mutation is live.
   *
   * @param stateOverride - partial state to inject into the store
   */
  async setStoreState(
    stateOverride: Partial<ValeriaSidebarStorageState>,
  ): Promise<void> {
    await this.page.evaluate(
      (override: Partial<ValeriaSidebarStorageState>) => {
        type ShellStoreWindow = Window & {
          useShellStore?: { setState: (s: unknown) => void };
        };
        const w = window as ShellStoreWindow;
        if (w.useShellStore) {
          w.useShellStore.setState(override);
        }
      },
      stateOverride,
    );
  }

  // ── IME simulation ────────────────────────────────────────────────────────

  /**
   * Simulate IME composition on the given element.
   * Dispatches compositionstart → keydown (isComposing=true) → compositionend.
   * Used to verify keyboard shortcut guard during IME input.
   *
   * @param elementHandle - selector for the element receiving IME events
   * @param keyDuringComposition - the key pressed during composition (e.g. 'r')
   */
  async simulateImeComposition(
    elementHandle: Locator,
    keyDuringComposition: string,
  ): Promise<void> {
    const elementId = await elementHandle.evaluate((el: Element) => {
      if (!el.id) el.id = `__ime_target_${Date.now()}`;
      return el.id;
    });

    await this.page.evaluate(
      ({ id, key }: { id: string; key: string }) => {
        const el = document.getElementById(id);
        if (!el) return;

        // 1. compositionstart
        el.dispatchEvent(
          new CompositionEvent("compositionstart", { bubbles: true }),
        );

        // 2. keydown with isComposing = true
        const keyEvent = new KeyboardEvent("keydown", {
          key,
          bubbles: true,
          cancelable: true,
          isComposing: true,
        });
        // Ensure isComposing is true (some browsers ignore the flag)
        Object.defineProperty(keyEvent, "isComposing", { get: () => true });
        el.dispatchEvent(keyEvent);

        // 3. compositionend
        el.dispatchEvent(
          new CompositionEvent("compositionend", { bubbles: true }),
        );
      },
      { id: elementId, key: keyDuringComposition },
    );
  }

  // ── Assertion helpers ─────────────────────────────────────────────────────

  /**
   * Assert that aria-expanded on the sidebar matches expected value.
   * Desktop sidebar sets aria-expanded; mobile drawer uses aria-modal instead.
   *
   * @param value - expected boolean value
   */
  async expectAriaExpanded(value: boolean): Promise<void> {
    await expect(this.sidebar).toHaveAttribute("aria-expanded", String(value));
  }

  /**
   * Wait for the live region to contain the expected text.
   * Useful for verifying state transitions announced to screen readers.
   *
   * @param text - expected text or regex
   */
  async waitForLiveRegionText(
    text: string | RegExp,
    timeout = 5_000,
  ): Promise<void> {
    await expect(
      this.page.getByRole("status").filter({ hasText: text }),
    ).toBeVisible({ timeout });
  }
}
