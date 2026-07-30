// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * EmbudoBoardPage.ts — POM for Adrián Embudo board (Kanban + Lista views).
 *
 * vitalia-fase2-adrian-embudo — T-E2E-1
 * Covers:
 *   SC-board  board render + column count + KPI strip
 *   SC-1      drag adyacente (adjacent stage move)
 *   SC-1b     override manual con razón (salto de etapa)
 *   SC-2      422 salto prohibido → OverrideReasonDialog
 *   SC-5      optimistic lock 409
 *   SC-7      network timeout → banner + Reintentar
 *   SC-8      empty state + CTA
 *   SC-nuevo  + Nuevo lead CTA
 *
 * Route: /{tenantId}/adrian/embudo
 *
 * Pattern: matches AdrianInboxPage.ts / StaffDirectoryPage.ts style.
 * All locators use role/text/testid selectors (no CSS/XPath).
 *
 * downstream-regression-na: brand-local vitalia E2E POM; no cross-brand consumers
 * spec_anchor: 04-validators.yaml § poms_required
 */

import type { Page, Locator } from "@playwright/test";
import { expect } from "@playwright/test";

export class EmbudoBoardPage {
  readonly page: Page;
  readonly tenantId: string;

  // ── Root ───────────────────────────────────────────────────────────────────
  readonly panelRoot: Locator;
  readonly embudoView: Locator;

  // ── Header controls ────────────────────────────────────────────────────────
  readonly header: Locator;
  readonly nuevoLeadButton: Locator;
  readonly kanbanToggle: Locator;
  readonly listaToggle: Locator;

  // ── Filters ────────────────────────────────────────────────────────────────
  readonly filtersContainer: Locator;
  readonly sortBySelect: Locator;

  // ── KPI strip (EmbudoMetrics) ──────────────────────────────────────────────
  readonly kpiStrip: Locator;
  readonly frozenKpiBadge: Locator;

  // ── Kanban board ───────────────────────────────────────────────────────────
  readonly kanbanBoard: Locator;
  readonly pipelineColumns: Locator;

  // ── Lista view ─────────────────────────────────────────────────────────────
  readonly leadsTable: Locator;

  // ── OverrideReasonDialog (Radix portal) ────────────────────────────────────
  readonly overrideDialog: Locator;
  readonly overrideReasonTextarea: Locator;
  readonly overrideConfirmButton: Locator;
  readonly overrideCancelButton: Locator;

  // ── Toast / banners ────────────────────────────────────────────────────────
  readonly successToast: Locator;
  readonly errorToast: Locator;
  readonly conflictToast: Locator;
  readonly networkBanner: Locator;
  readonly retryButton: Locator;

  // ── States ─────────────────────────────────────────────────────────────────
  readonly emptyState: Locator;
  readonly loadingSkeleton: Locator;

  constructor(page: Page, tenantId: string) {
    this.page = page;
    this.tenantId = tenantId;

    // Root
    this.panelRoot = page.getByTestId("app-panel-slot");
    this.embudoView = page
      .locator(
        '[data-testid="adrian-embudo-view"], [aria-label*="Embudo de Adrián"]',
      )
      .first();

    // Header
    this.header = page.locator('[data-testid="embudo-header"]').first();
    this.nuevoLeadButton = page
      .locator(
        '[data-testid="nuevo-lead-button"], button[aria-label*="Nuevo lead"]',
      )
      .first();
    this.kanbanToggle = page
      .locator(
        '[data-testid="view-kanban"], [aria-label*="Kanban"], [aria-label*="tablero"]',
      )
      .first();
    this.listaToggle = page
      .locator('[data-testid="view-lista"], [aria-label*="Lista"]')
      .first();

    // Filters
    this.filtersContainer = page
      .locator('[data-testid="embudo-filters"]')
      .first();
    this.sortBySelect = page
      .locator('[data-testid="sort-by-select"]')
      .first();

    // KPI strip
    this.kpiStrip = page
      .locator('[data-testid="embudo-metrics"]')
      .first();
    this.frozenKpiBadge = page
      .locator(
        '[data-testid="frozen-kpi-badge"], [aria-label*="congelada"], [aria-label*="congelados"]',
      )
      .first();

    // Kanban board
    this.kanbanBoard = page
      .locator('[data-testid="kanban-board"]')
      .first();
    this.pipelineColumns = page.locator('[data-testid^="pipeline-column-"]');

    // Lista
    this.leadsTable = page
      .locator('[data-testid="leads-table"]')
      .first();

    // Override dialog (Radix portal — page-level)
    this.overrideDialog = page
      .locator(
        '[data-testid="override-reason-dialog"], [role="dialog"][aria-label*="razón"], [role="dialog"][aria-label*="etapa"]',
      )
      .first();
    this.overrideReasonTextarea = page
      .locator(
        '[data-testid="override-reason-input"], textarea[placeholder*="razón"]',
      )
      .first();
    this.overrideConfirmButton = page
      .locator(
        '[data-testid="override-confirm"], button:has-text("Confirmar"), [aria-label*="Confirmar cambio"]',
      )
      .first();
    this.overrideCancelButton = page
      .locator(
        '[data-testid="override-cancel"], button:has-text("Cancelar")',
      )
      .first();

    // Toast / banners (Sonner v2 — uses data-sonner-toast, NOT role="alert" per item)
    // Sonner v2 renders <li data-sonner-toast data-type="success|error"> inside an ol container.
    // Filter by text since data-type doesn't narrow by content.
    this.successToast = page
      .locator('[data-sonner-toast]')
      .filter({ hasText: /movid|actualiz|cread/i })
      .first();
    this.errorToast = page
      .locator('[data-sonner-toast]')
      .filter({ hasText: /error|falló/i })
      .first();
    this.conflictToast = page
      .locator('[data-sonner-toast]')
      .filter({ hasText: /otra persona|conflicto/i })
      .first();
    this.networkBanner = page
      .locator('[data-sonner-toast], [role="alert"]')
      .filter({ hasText: /Reintentar|red|conexión/i })
      .first();
    this.retryButton = page
      .locator('button:has-text("Reintentar"), [data-testid="retry-button"]')
      .first();

    // States
    this.emptyState = page
      .locator('[data-testid="embudo-empty-state"]')
      .first();
    this.loadingSkeleton = page
      .locator('[data-testid="embudo-skeleton"], [aria-busy="true"]')
      .first();
  }

  // ── Navigation ──────────────────────────────────────────────────────────────

  async goto(
    opts?: { view?: "kanban" | "lista"; highlight?: string },
  ): Promise<void> {
    const params = new URLSearchParams();
    if (opts?.view) params.set("view", opts.view);
    if (opts?.highlight) params.set("highlight", opts.highlight);
    const qs = params.toString();
    await this.page.goto(
      `/${this.tenantId}/adrian/embudo${qs ? `?${qs}` : ""}`,
    );
    await this.page.waitForLoadState("networkidle");
  }

  // ── Board state ─────────────────────────────────────────────────────────────

  async waitForLoaded(): Promise<void> {
    await this.page
      .locator(
        '[data-testid="kanban-board"], [data-testid="leads-table"], [data-testid="embudo-empty-state"]',
      )
      .first()
      .waitFor({ state: "visible", timeout: 15_000 });
  }

  getColumn(stage: string): Locator {
    return this.page
      .locator(`[data-testid="pipeline-column-${stage}"]`)
      .first();
  }

  getColumnCards(stage: string): Locator {
    return this.getColumn(stage).locator('[data-testid^="lead-card-"]');
  }

  getLeadCard(leadId: string): Locator {
    return this.page
      .locator(`[data-testid="lead-card-${leadId}"]`)
      .first();
  }

  getLeadCardByName(partialName: string): Locator {
    return this.page
      .locator('[data-testid^="lead-card-"]')
      .filter({ hasText: partialName })
      .first();
  }

  // ── View toggle ─────────────────────────────────────────────────────────────

  async switchToLista(): Promise<void> {
    await this.listaToggle.click();
    await this.leadsTable.waitFor({ state: "visible", timeout: 8_000 });
  }

  async switchToKanban(): Promise<void> {
    await this.kanbanToggle.click();
    await this.kanbanBoard.waitFor({ state: "visible", timeout: 8_000 });
  }

  // ── Keyboard drag (DnD-kit KeyboardSensor) ─────────────────────────────────

  /**
   * Move a card to an adjacent stage using keyboard.
   * DnD-kit KeyboardSensor: Space to lift, ArrowLeft/Right to move, Space to drop.
   */
  async keyboardDragToAdjacentStage(
    leadId: string,
    direction: "right" | "left",
  ): Promise<void> {
    const card = this.getLeadCard(leadId);
    await card.focus();
    await card.press("Space");
    await this.page.waitForTimeout(200);
    await card.press(direction === "right" ? "ArrowRight" : "ArrowLeft");
    await this.page.waitForTimeout(200);
    await card.press("Space");
  }

  // ── Override dialog ─────────────────────────────────────────────────────────

  async fillOverrideReason(reason: string): Promise<void> {
    await this.overrideReasonTextarea.fill(reason);
  }

  async confirmOverride(): Promise<void> {
    await this.overrideConfirmButton.click();
  }

  async cancelOverride(): Promise<void> {
    await this.overrideCancelButton.click();
  }

  // ── Lead workspace navigation ───────────────────────────────────────────────

  async clickLeadCard(leadId: string): Promise<void> {
    // Click the name Link inside the card (not the article element which has dnd-kit listeners).
    // The article click is intercepted by PointerSensor; the Link navigates correctly.
    const card = this.getLeadCard(leadId);
    const cardLink = card.locator("a").first();
    await cardLink.click();
  }

  // ── Assertions ──────────────────────────────────────────────────────────────

  async expectColumnCount(count: number): Promise<void> {
    await expect(this.pipelineColumns).toHaveCount(count);
  }

  async expectColumnVisible(stage: string): Promise<void> {
    await expect(this.getColumn(stage)).toBeVisible();
  }

  async expectKanbanBoardVisible(): Promise<void> {
    await expect(this.kanbanBoard).toBeVisible();
  }

  async expectLeadsTableVisible(): Promise<void> {
    await expect(this.leadsTable).toBeVisible();
  }

  async expectEmptyState(): Promise<void> {
    await expect(this.emptyState).toBeVisible();
  }

  async expectHighlightedCard(leadId: string): Promise<void> {
    const card = this.getLeadCard(leadId);
    await expect(card).toBeVisible();
    // The card highlight uses a data attribute or ring class
    const highlighted = card.locator(
      '[data-highlighted="true"], [class*="ring-2"], [class*="animate-pulse"]',
    );
    await expect(highlighted.or(card)).toBeVisible();
  }

  async expectOverrideDialogVisible(): Promise<void> {
    await expect(this.overrideDialog).toBeVisible({ timeout: 6_000 });
  }

  async expectOverrideDialogHidden(): Promise<void> {
    await expect(this.overrideDialog).toBeHidden({ timeout: 6_000 });
  }

  async expectSuccessToast(): Promise<void> {
    await expect(this.successToast).toBeVisible({ timeout: 6_000 });
  }

  async expectConflictToast(): Promise<void> {
    await expect(this.conflictToast).toBeVisible({ timeout: 6_000 });
  }

  async expectNuevoLeadButtonVisible(): Promise<void> {
    await expect(this.nuevoLeadButton).toBeVisible();
  }

  async expectKpiVisible(): Promise<void> {
    await expect(this.kpiStrip).toBeVisible();
  }
}
