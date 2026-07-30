/**
 * shell-page.pom.ts — Page Object Model for routing-shell E2E specs.
 *
 * F1-S9 vitalia-fase1-routing-shell — T-6
 *
 * Provides ergonomic navigation + assertion methods for:
 *   - Tenant-validated shell navigation (SC-1..SC-5, SC-7, SC-8)
 *   - Not-found outer (SC-2) and inner (SC-3) assertions
 *   - Network error fallback assertions (SC-5)
 *   - Cross-tenant redirect assertions (SC-4)
 *   - Chrome presence/absence checks (not-found outer hides shell chrome)
 *
 * Route model: /{tenantId}/{agent}/{subtab}
 * Default landing: /{tenantId}/mateo/agenda (UPDATED v1.2 — paradigm-map-zones T-6 2026-05-30)
 *   Was: /{tenantId}/valeria/agenda (F1-S9 default — Chris 2026-05-25, pre T-5 migration)
 *
 * data-testid map:
 *   ribbon                → Ribbon organism
 *   sub-tabs-bar          → SubTabsBar organism
 *   not-found-shell       → outer not-found (invalid agent)
 *   not-found-agent       → inner not-found (invalid subtab)
 *   network-error-fallback → NetworkErrorFallback component
 *   network-error-retry   → Reintentar button inside NetworkErrorFallback
 *
 * spec_anchor: 04-validators.yaml § test_construction_plan.poms_required
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import type { Locator, Page, Response } from "@playwright/test";
import { expect } from "@playwright/test";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

// UPDATED v1.2 (paradigm-map-zones T-6): Mateo added to ribbon; Valeria is sidebar only.
export type AgentSlug =
  | "lisa"
  | "mateo"
  | "valeria"
  | "adrian"
  | "lucas"
  | "camila"
  | "config";

export interface ShellGotoOptions {
  tenantId: string;
  agent?: AgentSlug | string;
  subtab?: string;
}

// ---------------------------------------------------------------------------
// Default subtab per agent (mirrors RIBBON_SUBTABS first entry in agent-catalog.ts)
// ---------------------------------------------------------------------------

// UPDATED v1.2 (paradigm-map-zones T-6): Mateo defaultSubtab = "agenda".
const AGENT_DEFAULT_SUBTAB: Record<string, string> = {
  lisa: "marca",
  mateo: "agenda",
  valeria: "agenda",
  adrian: "inbox",
  lucas: "lanzar",
  camila: "voz",
  config: "cuenta",
};

// ---------------------------------------------------------------------------
// POM
// ---------------------------------------------------------------------------

export class ShellPage {
  constructor(private readonly page: Page) {}

  // ── Navigation (gotoTenantRoot / gotoAgentRoot / gotoSubtab) ──────────────

  /**
   * Navigate to tenant root and wait for redirect to default landing
   * /{tenantId}/mateo/agenda (UPDATED v1.2 — was /valeria/agenda pre paradigm-map-zones T-5).
   * SC-1 happy path start.
   */
  async gotoTenantRoot(tenantId: string): Promise<void> {
    await this.page.goto(`/${tenantId}`);
    // Root page redirects to /mateo/agenda (v1.2) — wait for Ribbon to confirm load
    await this.page
      .locator('[data-testid="ribbon"]')
      .waitFor({ state: "visible", timeout: 20_000 });
  }

  /**
   * Navigate to /{tenantId}/{agent} which redirects to /{tenantId}/{agent}/{defaultSubtab}.
   * Waits for Ribbon to be visible and active tab to reflect agent.
   */
  async gotoAgentRoot(
    tenantId: string,
    agent: AgentSlug | string,
  ): Promise<void> {
    await this.page.goto(`/${tenantId}/${agent}`);
    await this.page
      .locator('[data-testid="ribbon"]')
      .waitFor({ state: "visible", timeout: 15_000 });
  }

  /**
   * Navigate to /{tenantId}/{agent}/{subtab}.
   * Waits for both Ribbon and SubTabsBar to attach.
   */
  async gotoSubtab(
    tenantId: string,
    agent: AgentSlug | string,
    subtab: string,
  ): Promise<void> {
    const path = `/${tenantId}/${agent}/${subtab}`;
    await this.page.goto(path);
    await this.page
      .locator('[data-testid="ribbon"]')
      .waitFor({ state: "visible", timeout: 15_000 });
    await this.page
      .locator('[data-testid="sub-tabs-bar"]')
      .waitFor({ state: "attached", timeout: 10_000 });
  }

  /**
   * Navigate to an invalid agent slug to trigger outer not-found.
   * Does NOT wait for shell chrome — caller asserts 404 state.
   */
  async gotoInvalidAgent(
    tenantId: string,
    invalidAgent = "foo",
  ): Promise<Response | null> {
    const response = await this.page.goto(`/${tenantId}/${invalidAgent}`);
    await this.page.waitForLoadState("domcontentloaded");
    return response;
  }

  /**
   * Navigate to a valid agent + invalid subtab to trigger inner not-found.
   * Waits for Ribbon to confirm shell chrome is present.
   */
  async gotoInvalidSubtab(
    tenantId: string,
    agent: AgentSlug | string,
    invalidSubtab = "foo",
  ): Promise<Response | null> {
    const response = await this.page.goto(
      `/${tenantId}/${agent}/${invalidSubtab}`,
    );
    // Inner not-found renders shell chrome (Ribbon present)
    await this.page
      .locator('[data-testid="ribbon"]')
      .waitFor({ state: "visible", timeout: 15_000 });
    return response;
  }

  // ── Wait helpers ──────────────────────────────────────────────────────────

  /**
   * Wait for Ribbon to show a specific agent as active.
   * Uses aria-selected or data-active attribute on the tab button.
   */
  async waitForRibbonActive(agent: AgentSlug | string): Promise<void> {
    await expect(
      this.page.locator(
        `[data-testid="ribbon-tab-${agent}"][aria-selected="true"]`,
      ),
    ).toBeVisible({ timeout: 10_000 });
  }

  /**
   * Wait for SubTabsBar to show a specific subtab as active.
   * Uses data-active="true" on the tab button.
   */
  async waitForSubTabActive(subtabId: string): Promise<void> {
    await expect(
      this.page.locator(
        `[data-testid="sub-tab-${subtabId}"][data-active="true"]`,
      ),
    ).toBeVisible({ timeout: 10_000 });
  }

  // ── Ribbon locators + interaction ─────────────────────────────────────────

  /** The Ribbon organism locator. */
  getRibbon(): Locator {
    return this.page.locator('[data-testid="ribbon"]');
  }

  /** Get a specific Ribbon tab button by agent slug. */
  getRibbonTab(agent: AgentSlug | string): Locator {
    return this.page.locator(`[data-testid="ribbon-tab-${agent}"]`);
  }

  /** Click a Ribbon tab and wait for it to become active. */
  async clickRibbonTab(agent: AgentSlug | string): Promise<void> {
    await this.getRibbonTab(agent).click();
    await this.waitForRibbonActive(agent);
  }

  /**
   * Get the currently active Ribbon agent slug.
   * Returns the slug or null if none active.
   */
  async getRibbonActiveTab(): Promise<string | null> {
    await this.page.waitForTimeout(150);
    const active = this.page.locator(
      '[data-testid="ribbon"] [role="tab"][aria-selected="true"]',
    );
    const count = await active.count();
    if (count === 0) return null;
    const testid = await active.first().getAttribute("data-testid");
    if (!testid) return null;
    return testid.replace("ribbon-tab-", "");
  }

  // ── SubTabsBar locators + interaction ────────────────────────────────────

  /** The SubTabsBar organism locator. */
  getSubTabsBar(): Locator {
    return this.page.locator('[data-testid="sub-tabs-bar"]');
  }

  /** Get a specific SubTab button by id. */
  getSubTab(id: string): Locator {
    return this.page.locator(`[data-testid="sub-tab-${id}"]`);
  }

  /** Click a SubTab button. */
  async clickSubtab(id: string): Promise<void> {
    await this.getSubTab(id).click();
  }

  /**
   * Get the currently active SubTab id.
   * Returns null if none active.
   */
  async getSubtabActiveTab(): Promise<string | null> {
    await this.page.waitForTimeout(150);
    const active = this.page.locator(
      '[data-testid="sub-tabs-bar"] [role="tab"][data-active="true"]',
    );
    const count = await active.count();
    if (count === 0) return null;
    const testid = await active.first().getAttribute("data-testid");
    if (!testid) return null;
    return testid.replace("sub-tab-", "");
  }

  // ── Not-found locators ────────────────────────────────────────────────────

  /**
   * Locator for outer not-found element [data-testid=not-found-shell].
   * Visible when invalid agent slug used.
   */
  getNotFoundShell(): Locator {
    return this.page.locator('[data-testid="not-found-shell"]');
  }

  /**
   * Locator for inner not-found element [data-testid=not-found-agent].
   * Visible when valid agent + invalid subtab used.
   */
  getNotFoundAgent(): Locator {
    return this.page.locator('[data-testid="not-found-agent"]');
  }

  // ── Network error fallback ────────────────────────────────────────────────

  /**
   * Locator for NetworkErrorFallback [data-testid=network-error-fallback].
   */
  getNetworkErrorFallback(): Locator {
    return this.page.locator('[data-testid="network-error-fallback"]');
  }

  /**
   * Click the "Reintentar" button inside NetworkErrorFallback.
   */
  async clickRetry(): Promise<void> {
    await this.page.locator('[data-testid="network-error-retry"]').click();
  }

  // ── Document title ────────────────────────────────────────────────────────

  /**
   * Get the current document.title.
   */
  async getDocumentTitle(): Promise<string> {
    return await this.page.title();
  }

  // ── Assertions ────────────────────────────────────────────────────────────

  /**
   * Assert the page returned HTTP 404.
   * Pass the Response returned by goto/gotoInvalidAgent/gotoInvalidSubtab.
   */
  assertHttp404(response: Response | null): void {
    expect(response?.status()).toBe(404);
  }

  /**
   * Assert shell chrome (Ribbon + SubTabsBar) is NOT in the DOM.
   * Used for outer not-found (SC-2) and network error fallback (SC-5).
   */
  async assertNoChrome(): Promise<void> {
    await expect(this.getRibbon()).not.toBeAttached();
  }

  /**
   * Assert shell chrome (Ribbon + SubTabsBar) IS visible.
   * Used for inner not-found (SC-3) where chrome renders.
   */
  async assertChromeVisible(): Promise<void> {
    await expect(this.getRibbon()).toBeVisible({ timeout: 10_000 });
  }

  // ── Viewport + theme ─────────────────────────────────────────────────────

  /** Set viewport before navigation. */
  async setViewport(width: number, height: number): Promise<void> {
    await this.page.setViewportSize({ width, height });
  }

  /** Toggle theme via document class (call after navigation for golden diffs). */
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
}

// Re-export default subtab map for use in specs
export { AGENT_DEFAULT_SUBTAB };
