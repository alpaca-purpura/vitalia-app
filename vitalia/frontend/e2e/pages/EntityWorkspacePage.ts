/**
 * EntityWorkspacePage.ts — POM for EntityWorkspaceLayout (@luana/ui-kit) N3 pattern.
 *
 * vitalia-shell-core-hardening — T-7
 *
 * Covers SC-11 (N3 staff + embudo EntityWorkspaceLayout core) and SC-12
 * (directory disabled without entity).
 *
 * EntityWorkspaceLayout testids (from @luana/ui-kit):
 *   - data-testid="entity-workspace-layout"   — root wrapper
 *   - data-testid="entity-sub-nav-skeleton"   — loading state
 *   - data-testid="entity-workspace-content"  — content slot
 *
 * EntitySubNavBar (inside EntityWorkspaceLayout) is a tablist with roving
 * tabindex. The "back to directory" item has aria-label matching "‹ {parentLabel}".
 *
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";

// ---------------------------------------------------------------------------
// EntityWorkspacePage — POM for N3 EntityWorkspaceLayout
// ---------------------------------------------------------------------------

export class EntityWorkspacePage {
  readonly page: Page;

  /** Root EntityWorkspaceLayout wrapper */
  readonly workspaceLayout: Locator;

  /** Content slot inside EntityWorkspaceLayout */
  readonly workspaceContent: Locator;

  /** EntitySubNavBar skeleton (loading state) */
  readonly subNavSkeleton: Locator;

  /** SubNavBar tablist (role="tablist") inside the workspace */
  readonly subNavTablist: Locator;

  constructor(page: Page) {
    this.page = page;
    this.workspaceLayout = page.getByTestId("entity-workspace-layout");
    this.workspaceContent = page.getByTestId("entity-workspace-content");
    this.subNavSkeleton = page.getByTestId("entity-sub-nav-skeleton");
    this.subNavTablist = page
      .getByTestId("entity-workspace-layout")
      .locator('[role="tablist"]')
      .first();
  }

  // ── Navigation helpers ──────────────────────────────────────────────────────

  /**
   * Navigate to the staff directory for a given tenant.
   */
  async gotoStaffDirectory(tenantId: string): Promise<void> {
    await this.page.goto(`/${tenantId}/lisa/staff`);
    await this.page.waitForLoadState("networkidle", { timeout: 30_000 });
  }

  /**
   * Navigate to the staff workspace for a specific doctor.
   */
  async gotoStaffWorkspace(tenantId: string, doctorId: string): Promise<void> {
    await this.page.goto(`/${tenantId}/lisa/staff/${doctorId}/perfil`);
    await this.workspaceLayout.waitFor({ state: "visible", timeout: 30_000 });
  }

  /**
   * Navigate to the embudo directory for a given tenant.
   */
  async gotoEmbudoDirectory(tenantId: string): Promise<void> {
    await this.page.goto(`/${tenantId}/adrian/embudo`);
    await this.page.waitForLoadState("networkidle", { timeout: 30_000 });
  }

  /**
   * Navigate to a lead workspace for a specific lead.
   */
  async gotoLeadWorkspace(tenantId: string, leadId: string): Promise<void> {
    await this.page.goto(`/${tenantId}/adrian/embudo/${leadId}/resumen`);
    await this.workspaceLayout.waitFor({ state: "visible", timeout: 30_000 });
  }

  // ── Visibility helpers ──────────────────────────────────────────────────────

  /**
   * Returns true if the EntityWorkspaceLayout is visible (mounted and rendered).
   */
  async isWorkspaceVisible(): Promise<boolean> {
    try {
      await this.workspaceLayout.waitFor({ state: "visible", timeout: 5_000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Returns true if currently in loading state (skeleton visible).
   */
  async isLoadingState(): Promise<boolean> {
    try {
      await this.subNavSkeleton.waitFor({ state: "visible", timeout: 2_000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Wait for EntityWorkspaceLayout to finish loading (skeleton gone, content visible).
   */
  async waitForWorkspaceReady(): Promise<void> {
    await this.workspaceLayout.waitFor({ state: "visible", timeout: 30_000 });
    // Also wait for content slot — skeleton may appear briefly
    await this.workspaceContent.waitFor({ state: "visible", timeout: 30_000 });
  }

  // ── SubNavBar helpers ───────────────────────────────────────────────────────

  /**
   * Get all tab labels in the EntitySubNavBar.
   */
  async getSubNavTabLabels(): Promise<string[]> {
    await this.subNavTablist.waitFor({ state: "visible", timeout: 10_000 });
    const tabs = await this.subNavTablist.locator('[role="tab"]').all();
    return Promise.all(tabs.map((t) => t.innerText()));
  }

  /**
   * Click a tab in the EntitySubNavBar by its accessible label.
   */
  async clickSubNavTab(label: string): Promise<void> {
    const tab = this.subNavTablist.locator(`[role="tab"]`, {
      hasText: label,
    });
    await tab.click();
    await this.workspaceContent.waitFor({ state: "visible", timeout: 10_000 });
  }

  /**
   * Click the "back to directory" navigation item in the SubNavBar.
   * EntitySubNavBar renders the parent link with aria-label containing "‹".
   */
  async clickBackToDirectory(): Promise<void> {
    const backLink = this.page
      .getByTestId("entity-workspace-layout")
      .locator('a[aria-label*="‹"], a[aria-label*="Embudo"], a[aria-label*="Staff"]')
      .first();
    await backLink.click();
    await this.page.waitForLoadState("networkidle", { timeout: 15_000 });
  }

  // ── Staff entity card helpers ───────────────────────────────────────────────

  /**
   * Get the count of entity cards in the directory (before entering workspace).
   * Uses entity-info-card testid pattern from @luana/ui-kit.
   */
  async getEntityCardCount(): Promise<number> {
    return await this.page
      .locator('[data-testid^="entity-info-card-"]')
      .count();
  }
}
