// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * RecuperarPage.ts — POM for /recuperar (frozen leads + Decidió no).
 *
 * vitalia-fase2-adrian-embudo — T-E2E-1
 * Covers:
 *   SC-freeze   auto-freeze → sale board → aparece en Recuperar
 *   F-8         Recuperar view: recién congelados + diagnose + Reactivar
 *   RN-13       auto-freeze (14d/2×SLA/30d)
 *
 * Route: /{tenantId}/adrian/recuperar
 *
 * downstream-regression-na: brand-local vitalia E2E POM
 * spec_anchor: 04-validators.yaml § poms_required
 */

import type { Page, Locator } from "@playwright/test";
import { expect } from "@playwright/test";

export class RecuperarPage {
  readonly page: Page;
  readonly tenantId: string;

  // ── Layout ─────────────────────────────────────────────────────────────────
  readonly recuperarView: Locator;

  // ── Sections ───────────────────────────────────────────────────────────────
  readonly recienCongeladosSection: Locator;
  readonly decidioNoSection: Locator;

  // ── Lead rows ──────────────────────────────────────────────────────────────
  readonly frozenLeadRows: Locator;
  readonly decidioNoRows: Locator;

  // ── Actions per row ────────────────────────────────────────────────────────
  readonly diagnoseButtons: Locator;
  readonly reactivarButtons: Locator;

  // ── Diagnosis result ────────────────────────────────────────────────────────
  readonly diagnosisPanel: Locator;
  readonly diagnosisRecommendation: Locator;
  readonly diagnosisSuggestedAction: Locator;

  // ── Toast ─────────────────────────────────────────────────────────────────
  readonly reactivarToast: Locator;
  readonly errorToast: Locator;

  // ── States ────────────────────────────────────────────────────────────────
  readonly emptyState: Locator;
  readonly loadingSkeleton: Locator;

  constructor(page: Page, tenantId: string) {
    this.page = page;
    this.tenantId = tenantId;

    // Layout
    this.recuperarView = page
      .locator('[data-testid="recuperar-view"]')
      .first();

    // Sections
    this.recienCongeladosSection = page
      .locator(
        '[data-testid="recien-congelados-section"], [aria-label*="congelados"]',
      )
      .first();
    this.decidioNoSection = page
      .locator(
        '[data-testid="decidio-no-section"], [aria-label*="Decidió no"]',
      )
      .first();

    // Rows
    this.frozenLeadRows = page.locator('[data-testid^="frozen-lead-row-"]');
    this.decidioNoRows = page.locator('[data-testid^="decidio-no-row-"]');

    // Actions
    this.diagnoseButtons = page.locator(
      '[data-testid^="diagnose-button-"], button[aria-label*="Diagnosticar"]',
    );
    this.reactivarButtons = page.locator(
      '[data-testid^="reactivar-button-"], button[aria-label*="Reactivar"]',
    );

    // Diagnosis result panel
    this.diagnosisPanel = page
      .locator('[data-testid="diagnosis-panel"]')
      .first();
    this.diagnosisRecommendation = page
      .locator('[data-testid="diagnosis-recommendation"]')
      .first();
    this.diagnosisSuggestedAction = page
      .locator('[data-testid="diagnosis-suggested-action"]')
      .first();

    // Toast
    this.reactivarToast = page
      .locator('[role="status"]')
      .filter({ hasText: /reactivad|volvió/i })
      .first();
    this.errorToast = page
      .locator('[role="alert"]')
      .filter({ hasText: /error/i })
      .first();

    // States
    this.emptyState = page
      .locator('[data-testid="recuperar-empty-state"]')
      .first();
    this.loadingSkeleton = page
      .locator('[data-testid="recuperar-skeleton"], [aria-busy="true"]')
      .first();
  }

  // ── Navigation ──────────────────────────────────────────────────────────────

  async goto(): Promise<void> {
    await this.page.goto(`/${this.tenantId}/adrian/recuperar`);
    await this.page.waitForLoadState("networkidle");
  }

  // ── State ───────────────────────────────────────────────────────────────────

  async waitForLoaded(): Promise<void> {
    await this.recuperarView.waitFor({ state: "visible", timeout: 12_000 });
  }

  getFrozenLeadRow(leadId: string): Locator {
    return this.page
      .locator(`[data-testid="frozen-lead-row-${leadId}"]`)
      .first();
  }

  getDiagnoseButton(leadId: string): Locator {
    return this.page
      .locator(
        `[data-testid="diagnose-button-${leadId}"], [aria-label*="Diagnosticar"][data-lead-id="${leadId}"]`,
      )
      .first();
  }

  getReactivarButton(leadId: string): Locator {
    return this.page
      .locator(
        `[data-testid="reactivar-button-${leadId}"], [aria-label*="Reactivar"][data-lead-id="${leadId}"]`,
      )
      .first();
  }

  // ── Actions ─────────────────────────────────────────────────────────────────

  async clickDiagnose(leadId: string): Promise<void> {
    await this.getDiagnoseButton(leadId).click();
  }

  async clickReactivar(leadId: string): Promise<void> {
    await this.getReactivarButton(leadId).click();
  }

  // ── Assertions ──────────────────────────────────────────────────────────────

  async expectRecuperarVisible(): Promise<void> {
    await expect(this.recuperarView).toBeVisible();
  }

  async expectFrozenLeadVisible(leadId: string): Promise<void> {
    await expect(this.getFrozenLeadRow(leadId)).toBeVisible();
  }

  async expectFrozenLeadCount(count: number): Promise<void> {
    await expect(this.frozenLeadRows).toHaveCount(count);
  }

  async expectDiagnosisPanelVisible(): Promise<void> {
    await expect(this.diagnosisPanel).toBeVisible({ timeout: 8_000 });
  }

  async expectReactivarToast(): Promise<void> {
    await expect(this.reactivarToast).toBeVisible({ timeout: 6_000 });
  }

  async expectEmptyState(): Promise<void> {
    await expect(this.emptyState).toBeVisible();
  }
}
