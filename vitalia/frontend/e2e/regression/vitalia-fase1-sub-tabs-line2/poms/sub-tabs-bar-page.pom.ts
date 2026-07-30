/**
 * sub-tabs-bar-page.pom.ts — Page Object Model for SubTabsBar line-2 navigation.
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * Provides ergonomic methods to drive Playwright specs against the SubTabsBar organism:
 *   - goto / gotoRaw: navigation helpers
 *   - getSubTabsBar: locator for the nav[data-testid=sub-tabs-bar]
 *   - getSubTab / clickSubTab: sub-tab button locators
 *   - getActiveSubTabId / getSubTabAriaSelected: assertion helpers
 *   - pressKey: keyboard navigation helpers (roving tabindex)
 *   - setViewport / setTheme: environment helpers
 *
 * Route model: /{tenantId}/{agent}/{subtab}
 *
 * SubTabsBar renders when: activeAgent is a valid slug + RIBBON_SUBTABS[agent].length > 0.
 * SubTabsBar returns null when: agent is invalid (extractAgentFromPath → null) OR subtabs.length === 0.
 *
 * spec_anchor: 01-spec.md § Gherkin SC-1..SC-9 · 03-arch.md § 2.4 (SubTabsBar POM contract)
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import type { Locator, Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AgentSlug =
  | "lisa"
  | "lucas"
  | "adrian"
  | "valeria"
  | "camila"
  | "mateo";
export type SubTabsBarSlug = AgentSlug | "config";

export interface SubTabsGotoOptions {
  /** Tenant ID (injected via auth fixture / E2E_TENANT_ID env var). */
  tenantId: string;
  /** Agent segment. */
  agent: string;
  /** Sub-tab segment. Defaults to first sub-tab of agent. */
  subtab?: string;
}

// ---------------------------------------------------------------------------
// Default subtab per agent (matches RIBBON_SUBTABS first entry)
// ---------------------------------------------------------------------------

const AGENT_DEFAULT_SUBTAB: Record<string, string> = {
  lisa: "marca",
  lucas: "lanzar",
  adrian: "inbox",
  valeria: "agenda",
  camila: "voz",
  config: "cuenta",
};

// ---------------------------------------------------------------------------
// POM
// ---------------------------------------------------------------------------

export class SubTabsBarPage {
  constructor(private readonly page: Page) {}

  // ── Navigation ────────────────────────────────────────────────────────────

  /**
   * Navigate to a shell route and wait for SubTabsBar to mount.
   * Waits for [data-testid=sub-tabs-bar] to be attached in DOM.
   * Use for valid agent scenarios (SC-1..SC-3, SC-5, SC-6, SC-8, SC-9).
   */
  async goto(opts: SubTabsGotoOptions): Promise<void> {
    const {
      tenantId,
      agent,
      subtab = AGENT_DEFAULT_SUBTAB[agent] ?? "default",
    } = opts;
    const path = `/${tenantId}/${agent}/${subtab}`;
    await this.page.goto(path);
    // Wait for ribbon first (mounted before sub-tabs), then sub-tabs
    await this.page.waitForSelector('[data-testid="ribbon"]:visible', {
      timeout: 15_000,
    });
    // Sub-tabs mount immediately after ribbon; wait for attachment
    await this.page.waitForSelector('[data-testid="sub-tabs-bar"]', {
      state: "attached",
      timeout: 10_000,
    });
  }

  /**
   * Navigate via page.goto with a raw URL (for null-agent / XSS / invalid-agent tests).
   * Does NOT wait for sub-tabs-bar to attach — caller asserts null state.
   */
  async gotoRaw(url: string): Promise<void> {
    await this.page.goto(url);
    // Short grace period for hydration without requiring sub-tabs-bar.
    await this.page.waitForTimeout(500);
  }

  // ── SubTabsBar root ───────────────────────────────────────────────────────

  /**
   * The visible SubTabsBar container element [data-testid=sub-tabs-bar].
   * Note: may return null if SubTabsBar returned null (invalid agent / mateo).
   */
  getSubTabsBar(): Locator {
    return this.page.locator('[data-testid="sub-tabs-bar"]').first();
  }

  /**
   * Check whether SubTabsBar is present in DOM (returns false if component returned null).
   */
  async isPresent(): Promise<boolean> {
    return this.page
      .locator('[data-testid="sub-tabs-bar"]')
      .isVisible()
      .catch(() => false);
  }

  // ── Sub-tab locators ──────────────────────────────────────────────────────

  /**
   * Get locator for a sub-tab button by id.
   * [data-testid=sub-tab-{id}]
   */
  getSubTab(id: string): Locator {
    return this.page.locator(`[data-testid="sub-tab-${id}"]`);
  }

  /**
   * Get all sub-tab buttons within the visible SubTabsBar.
   */
  getAllSubTabs(): Locator {
    return this.getSubTabsBar().locator('[role="tab"]');
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  /**
   * Click a sub-tab by its id.
   */
  async clickSubTab(id: string): Promise<void> {
    await this.getSubTab(id).click();
  }

  /**
   * Press a keyboard key in the page context.
   * Used for roving tabindex WAI-ARIA navigation.
   */
  async pressKey(
    key:
      | "ArrowRight"
      | "ArrowLeft"
      | "Home"
      | "End"
      | "Enter"
      | "Space"
      | "Tab"
      | "Escape",
  ): Promise<void> {
    await this.page.keyboard.press(key);
  }

  // ── State inspection ─────────────────────────────────────────────────────

  /**
   * Get the currently active sub-tab id.
   * Returns null if no sub-tab is active.
   */
  async getActiveSubTabId(): Promise<string | null> {
    await this.page.waitForTimeout(150);
    const active = this.getSubTabsBar().locator(
      '[role="tab"][data-active="true"]',
    );
    const count = await active.count();
    if (count === 0) return null;
    const testid = await active.first().getAttribute("data-testid");
    if (!testid) return null;
    return testid.replace("sub-tab-", "");
  }

  /**
   * Get aria-selected value for a sub-tab by id.
   * Returns 'true', 'false', or null if attribute missing.
   */
  async getSubTabAriaSelected(id: string): Promise<string | null> {
    return await this.getSubTab(id).getAttribute("aria-selected");
  }

  /**
   * Get aria-label of the SubTabsBar nav element.
   */
  async getAriaLabel(): Promise<string | null> {
    return await this.getSubTabsBar().getAttribute("aria-label");
  }

  /**
   * Get count of sub-tab buttons in the SubTabsBar.
   */
  async getSubTabCount(): Promise<number> {
    return await this.getAllSubTabs().count();
  }

  /**
   * Get the focused sub-tab id (via :focus selector).
   * Returns null if no sub-tab is focused.
   */
  async getFocusedSubTabId(): Promise<string | null> {
    const focused = this.getSubTabsBar().locator('[role="tab"]:focus');
    const count = await focused.count();
    if (count === 0) return null;
    const testid = await focused.first().getAttribute("data-testid");
    if (!testid) return null;
    return testid.replace("sub-tab-", "");
  }

  // ── Viewport & theme ─────────────────────────────────────────────────────

  /**
   * Set the page viewport size.
   * Call BEFORE navigation for deterministic rendering.
   */
  async setViewport(width: number, height: number): Promise<void> {
    await this.page.setViewportSize({ width, height });
  }

  /**
   * Toggle dark/light theme via document.documentElement class.
   */
  async setTheme(theme: "light" | "dark"): Promise<void> {
    await this.page.evaluate((t) => {
      if (t === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    }, theme);
    await this.page.waitForTimeout(100);
  }

  /**
   * Seed theme into localStorage BEFORE navigation.
   * Use via addInitScript pattern for visual golden specs.
   */
  async seedThemeLocalstorage(theme: "light" | "dark"): Promise<void> {
    await this.page.addInitScript((t) => {
      localStorage.setItem("vitalia-theme", t);
    }, theme);
  }
}
