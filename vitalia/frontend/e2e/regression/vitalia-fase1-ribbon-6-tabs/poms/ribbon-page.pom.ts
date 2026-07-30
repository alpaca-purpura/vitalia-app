/**
 * ribbon-page.pom.ts — Page Object Model for Ribbon 6-tab navigation.
 *
 * F1-S7 vitalia-fase1-ribbon-6-tabs — T-5
 *
 * Provides ergonomic methods to drive Playwright specs against the Ribbon organism:
 *   - goto: navigate to a shell route and wait for ribbon to mount
 *   - getTab / clickTab: agent tab locators
 *   - pressKey: keyboard navigation helpers
 *   - getActiveSlug / getTabAriaSelected: assertion helpers
 *   - setViewport / setTheme: environment helpers
 *   - expectAvatarFallback: SC-9 avatar PNG 404 fallback assertion
 *
 * Route model: /{tenantId} → redirects to /{tenantId}/lisa/marca (shell root).
 * For deep-link specs, navigate directly to /{tenantId}/{agent}/{subtab}.
 * For XSS and invalid-agent specs, navigate via page.goto() with raw URL segment.
 *
 * spec_anchor: 04-validators.yaml § test_construction_plan poms_required
 *              01-spec.md § Gherkin SC-1..SC-9
 *              03-arch.md § 2.2 (RibbonPage POM contract)
 *
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import type { Locator, Page } from "@playwright/test";
import type { AgentSlug } from "@/lib/agent-catalog";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type RibbonTabSlug = AgentSlug | "config";

export interface GotoOptions {
  /** Tenant ID (injected via auth fixture / E2E_TENANT_ID env var). */
  tenantId: string;
  /**
   * Agent segment for the URL. Omit to use root redirect (→ lisa/marca).
   * Pass 'config' for ConfigTab state.
   * Pass an invalid string (e.g. 'foobar') to test invalid-agent scenario.
   */
  agent?: string;
  /** Sub-tab segment. Used only when agent is provided. Defaults to 'default'. */
  subtab?: string;
}

// ---------------------------------------------------------------------------
// POM
// ---------------------------------------------------------------------------

export class RibbonPage {
  constructor(private readonly page: Page) {}

  // ── Navigation ────────────────────────────────────────────────────────────

  /**
   * Navigate to a shell route and wait for the Ribbon to be attached.
   *
   * Route logic:
   *   - agent omitted → /{tenantId} (root, redirects to /{tenantId}/lisa/marca)
   *   - agent provided → /{tenantId}/{agent}/{subtab}
   *
   * Waits for [data-testid=ribbon] to be attached in DOM (not necessarily visible).
   * The ribbon mounts in the Client Component boundary — hydration may be brief.
   */
  async goto(opts: GotoOptions): Promise<void> {
    const { tenantId, agent, subtab = "default" } = opts;
    const path = agent ? `/${tenantId}/${agent}/${subtab}` : `/${tenantId}`;
    await this.page.goto(path);
    // Wait for the visible ribbon to mount (not just attached — multi-layout DOM has
    // hidden ribbon instances; we wait for the VISIBLE one).
    await this.page.waitForSelector('[data-testid="ribbon"]:visible', {
      timeout: 15_000,
    });
  }

  /**
   * Navigate via page.goto with a raw URL (for XSS / invalid-agent tests).
   * Does NOT wait for ribbon to be attached (ribbon may be idle or error state).
   */
  async gotoRaw(url: string): Promise<void> {
    await this.page.goto(url);
    // Short grace period for hydration without requiring ribbon to attach.
    await this.page.waitForTimeout(500);
  }

  // ── Ribbon root ───────────────────────────────────────────────────────────

  /**
   * The visible ribbon container element [data-testid=ribbon].
   *
   * Implementation note: ShellOrganismLayoutClient renders multiple
   * <AppPanelSlot> instances (agentic desktop + mobile layouts) for CSS-driven
   * visibility. At desktop viewports the mobile layout is CSS-hidden (md:hidden)
   * but still in DOM — causing duplicate data-testid="ribbon" elements.
   *
   * We scope to the VISIBLE ribbon only via `.visible()` filter. This ensures
   * Playwright strict mode doesn't fail on multi-ribbon DOM while still correctly
   * finding the interactive ribbon the user actually sees.
   */
  getRibbon(): Locator {
    return this.page
      .locator('[data-testid="ribbon"]')
      .filter({ visible: true })
      .first();
  }

  // ── Tab locators ──────────────────────────────────────────────────────────

  /**
   * Get locator for an agent tab button.
   * Scoped to the visible ribbon container to avoid strict-mode failures
   * when the DOM contains multiple ribbon instances (desktop + mobile layouts).
   * [data-testid=ribbon-tab-{slug}] for agent tabs.
   */
  getTab(slug: AgentSlug): Locator {
    return this.getRibbon().locator(`[data-testid="ribbon-tab-${slug}"]`);
  }

  /**
   * Get locator for the ConfigTab.
   * Scoped to the visible ribbon container.
   * [data-testid=ribbon-config-tab]
   */
  getConfigTab(): Locator {
    return this.getRibbon().locator('[data-testid="ribbon-config-tab"]');
  }

  /**
   * Get locator for any ribbon tab by slug (including 'config').
   * Convenience overload.
   */
  getTabBySlug(slug: RibbonTabSlug): Locator {
    return slug === "config" ? this.getConfigTab() : this.getTab(slug);
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  /**
   * Click an agent tab by slug.
   * Waits for click to register (default Playwright click timeout).
   */
  async clickTab(slug: AgentSlug): Promise<void> {
    await this.getTab(slug).click();
  }

  /** Click the ConfigTab. */
  async clickConfigTab(): Promise<void> {
    await this.getConfigTab().click();
  }

  /**
   * Press a keyboard key in the page context.
   * Used for roving tabindex WAI-ARIA navigation (Arrow, Home, End, Enter, Space).
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
   * Get the currently active ribbon tab slug.
   * Reads data-active="true" from ribbon tab buttons.
   * Returns null if no tab is active (idle state / invalid URL).
   *
   * Scoped to visible ribbon to avoid duplicates from multi-layout DOM.
   */
  async getActiveSlug(): Promise<string | null> {
    // Wait briefly for state to settle after navigation.
    await this.page.waitForTimeout(200);
    // Scope to visible ribbon container to avoid multi-layout duplicates
    const ribbon = this.getRibbon();
    const active = ribbon.locator(
      '[data-testid^="ribbon-tab-"][data-active="true"]',
    );
    const count = await active.count();
    if (count === 0) return null;
    const testid = await active.first().getAttribute("data-testid");
    if (!testid) return null;
    // Extract slug from "ribbon-tab-{slug}" or "ribbon-config-tab"
    if (testid === "ribbon-config-tab") return "config";
    return testid.replace("ribbon-tab-", "");
  }

  /**
   * Get the focused ribbon tab slug (via :focus-within or data-focused attr).
   * Returns the data-testid suffix of the focused tab, or null.
   */
  async getFocusedTabSlug(): Promise<string | null> {
    const focused = this.page.locator(
      '[data-testid^="ribbon-tab-"]:focus, [data-testid="ribbon-config-tab"]:focus',
    );
    const count = await focused.count();
    if (count === 0) return null;
    const testid = await focused.first().getAttribute("data-testid");
    if (!testid) return null;
    if (testid === "ribbon-config-tab") return "config";
    return testid.replace("ribbon-tab-", "");
  }

  /**
   * Get aria-selected value for a tab by slug.
   * Returns 'true', 'false', or null if attribute missing.
   */
  async getTabAriaSelected(slug: RibbonTabSlug): Promise<string | null> {
    return await this.getTabBySlug(slug).getAttribute("aria-selected");
  }

  /**
   * Get the tooltip text if a Radix tooltip is currently visible.
   * Returns null if no tooltip is visible.
   */
  async getTooltip(): Promise<string | null> {
    const tip = this.page.locator('[role="tooltip"]');
    const count = await tip.count();
    if (count === 0) return null;
    const visible = await tip.first().isVisible();
    if (!visible) return null;
    return await tip.first().textContent();
  }

  // ── Avatar fallback ───────────────────────────────────────────────────────

  /**
   * Assert that the AvatarFallback element is visible for a given agent tab.
   * Used in SC-9 (PNG 404 → initial letter fallback via Shadcn Avatar).
   */
  async expectAvatarFallback(slug: AgentSlug): Promise<void> {
    const tab = this.getTab(slug);
    // The AvatarFallback span is rendered by Radix when AvatarImage fails.
    // It carries the data-testid="avatar-fallback-{slug}" set in RibbonTab.
    const fallback = tab.locator(`[data-testid="avatar-fallback-${slug}"]`);
    await fallback.waitFor({ state: "visible", timeout: 5_000 });
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
   * Follows the vitalia-theme localStorage key pattern (next-themes).
   * Call AFTER page load; next-themes reads from localStorage on mount.
   */
  async setTheme(theme: "light" | "dark"): Promise<void> {
    await this.page.evaluate((t) => {
      if (t === "dark") {
        document.documentElement.classList.add("dark");
      } else {
        document.documentElement.classList.remove("dark");
      }
    }, theme);
    // Allow CSS to re-paint after class toggle.
    await this.page.waitForTimeout(100);
  }

  /**
   * Seed theme into localStorage BEFORE navigation.
   * Use via addInitScript pattern if needed per test.
   * This is a convenience helper for visual golden specs.
   */
  async seedThemeLocalstorage(theme: "light" | "dark"): Promise<void> {
    await this.page.addInitScript((t) => {
      localStorage.setItem("vitalia-theme", t);
    }, theme);
  }
}
