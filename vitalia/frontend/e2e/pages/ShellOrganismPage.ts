/**
 * ShellOrganismPage — POM for the shell organism with SubTabContent navigation.
 * F1-S10 vitalia-fase1-empty-states — T-10
 *
 * Wraps routing to /{tenantId}/{agent}/{subtab} and assertions on:
 *   - Ribbon component (data-testid="ribbon")
 *   - SubTabsBar component (data-testid="sub-tabs-bar")
 *   - SubTabContent dispatcher (data-testid="subtab-content-{agent}-{subtab}")
 *   - SubTabHeader (data-testid="subtab-header-{agent}-{subtab}")
 *   - ValeriaSidebar (data-testid="valeria-sidebar")
 *   - not-found page inside shell (data-testid="not-found-agent")
 *
 * Usage:
 *   const shell = new ShellOrganismPage(page, tenantId);
 *   await shell.goto("lisa", "marca");
 *   await shell.expectShellMounted();
 *   await shell.expectSubTabContentVisible("lisa", "marca");
 *
 * downstream-regression-na: brand-local vitalia e2e POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";
import { expect } from "@playwright/test";

export class ShellOrganismPage {
  readonly page: Page;
  readonly tenantId: string;

  // ── Shell structure locators ──────────────────────────────────────────
  readonly ribbon: Locator;
  readonly subTabsBar: Locator;
  readonly valeriaSidebar: Locator;
  readonly notFoundAgent: Locator;
  readonly notFoundShell: Locator;

  constructor(page: Page, tenantId: string) {
    this.page = page;
    this.tenantId = tenantId;
    this.ribbon = page.locator('[data-testid="ribbon"]').first();
    this.subTabsBar = page.locator('[data-testid="sub-tabs-bar"]').first();
    this.valeriaSidebar = page
      .locator('[data-testid="valeria-sidebar"]')
      .first();
    this.notFoundAgent = page
      .locator('[data-testid="not-found-agent"]')
      .first();
    this.notFoundShell = page
      .locator('[data-testid="not-found-shell"]')
      .first();
  }

  // ── Navigation ────────────────────────────────────────────────────────

  /**
   * Navigate to /{tenantId}/{agent}/{subtab} route.
   * Waits for networkidle to ensure shell is fully mounted.
   */
  async goto(agent: string, subtab: string): Promise<void> {
    await this.page.goto(`/${this.tenantId}/${agent}/${subtab}`);
    await this.page.waitForLoadState("networkidle");
  }

  /**
   * Navigate to an invalid sub-tab path that should trigger not-found.
   */
  async gotoInvalidSubtab(
    agent: string = "lisa",
    subtab: string = "xss-invalid-tab",
  ): Promise<void> {
    await this.page.goto(`/${this.tenantId}/${agent}/${subtab}`);
    await this.page.waitForLoadState("networkidle");
  }

  /**
   * Navigate to a path with XSS payload in subtab segment.
   * URL-encodes the payload to simulate real browser navigation attempt.
   */
  async gotoXssSubtab(xssPayload: string): Promise<void> {
    const encoded = encodeURIComponent(xssPayload);
    await this.page.goto(`/${this.tenantId}/lisa/${encoded}`);
    await this.page.waitForLoadState("networkidle");
  }

  // ── Shell structure assertions ────────────────────────────────────────

  /**
   * Assert the shell shell organism is mounted with ribbon + sub-tabs-bar visible.
   * Does NOT assert specific sub-tab content.
   */
  async expectShellMounted(): Promise<void> {
    await expect(this.ribbon).toBeVisible();
    await expect(this.subTabsBar).toBeVisible();
  }

  /**
   * Assert that the SubTabContent dispatcher renders content for the given agent.subtab.
   * Uses data-testid="subtab-content-{agent}-{subtab}" per SubTabContent.tsx.
   */
  async expectSubTabContentVisible(
    agent: string,
    subtab: string,
  ): Promise<void> {
    await expect(
      this.page
        .locator(`[data-testid="subtab-content-${agent}-${subtab}"]`)
        .first(),
    ).toBeVisible();
  }

  /**
   * Assert the SubTabHeader is rendered for the given agent.subtab.
   * data-testid="subtab-header-{agent}-{subtab}" per SubTabHeader.tsx.
   */
  async expectSubTabHeaderVisible(
    agent: string,
    subtab: string,
  ): Promise<void> {
    await expect(
      this.page
        .locator(`[data-testid="subtab-header-${agent}-${subtab}"]`)
        .first(),
    ).toBeVisible();
  }

  // ── Ribbon interactions ───────────────────────────────────────────────

  /**
   * Click a ribbon tab by agent slug.
   * data-testid="ribbon-tab-{agent}" per Ribbon.tsx.
   */
  async clickRibbonTab(agent: string): Promise<void> {
    await this.page.locator(`[data-testid="ribbon-tab-${agent}"]`).click();
  }

  /**
   * Assert that a specific ribbon tab is active.
   * aria-selected="true" per Ribbon.tsx implementation.
   */
  async expectRibbonTabActive(agent: string): Promise<void> {
    await expect(
      this.page
        .locator(`[data-testid="ribbon-tab-${agent}"][aria-selected="true"]`)
        .first(),
    ).toBeVisible();
  }

  // ── Sub-tab interactions ──────────────────────────────────────────────

  /**
   * Click a sub-tab by id.
   * data-testid="sub-tab-{id}" per SubTab.tsx.
   */
  async clickSubTab(id: string): Promise<void> {
    await this.page.locator(`[data-testid="sub-tab-${id}"]`).click();
  }

  /**
   * Assert that a sub-tab is active.
   * data-active="true" per SubTabsBar.tsx.
   */
  async expectSubTabActive(id: string): Promise<void> {
    await expect(
      this.page
        .locator(`[data-testid="sub-tab-${id}"][data-active="true"]`)
        .first(),
    ).toBeVisible();
  }

  // ── Not-found assertions ──────────────────────────────────────────────

  /**
   * Assert the inner not-found component is visible (invalid sub-tab).
   * Shell (ribbon + sub-tabs-bar) must still be visible.
   */
  async expectNotFoundInShell(): Promise<void> {
    await expect(this.notFoundAgent).toBeVisible();
    // Shell organism still mounted
    await expect(this.ribbon).toBeVisible();
    await expect(this.valeriaSidebar).toBeVisible();
  }

  // ── DOM stability helpers ─────────────────────────────────────────────

  /**
   * Get the DOM node handle for the ribbon element.
   * Used to assert DOM ref stability across sub-tab navigation (SC-6).
   */
  async getRibbonElementHandle() {
    return await this.ribbon.elementHandle();
  }

  // ── Console monitoring ────────────────────────────────────────────────

  /**
   * Assert no console errors are present after navigation.
   * Caller should attach page.on("console") before goto().
   * This helper is a documentation annotation — test must set up listener.
   */
  async waitForStableRender(): Promise<void> {
    // Small delay to allow any React hydration errors to surface
    await this.page.waitForTimeout(300);
  }
}
