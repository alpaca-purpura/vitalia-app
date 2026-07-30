/**
 * marketing.page.ts — Page Object Model para /marketing
 *
 * Validator IDs: e2e_smoke_marketing, visual_a11y_axe
 * Story: vitalia-slice-1-marketing
 * Ticket: T-mk-fe-7
 *
 * Locators basados en atributos ARIA/semánticos (ARIA-first, sin XPath ni CSS frágil):
 *   - bowtieSvg        → figure[aria-label="Embudo de conversión"] svg
 *   - stageTabs        → role="tablist" con 5 role="tab" hijos
 *   - lucasCardsSection → aria-label que contenga "Recomendaciones de Lucas"
 *   - attributionMatrix → encabezado "Matriz de atribución" (section reservation)
 *   - approvalModalTitle → id="approval-modal-title" dentro de role="dialog"
 *
 * Métodos de acción:
 *   - goto()                     → navega a /marketing
 *   - waitForReady()             → espera a que Bowtie SVG sea visible
 *   - clickStageTab(slug)        → hace clic en tab de etapa por aria-controls pattern
 *   - clickFirstLucasCardDetail() → abre modal de detalle del primer ítem Lucas
 *   - closeApprovalModal()       → cierra el modal de aprobación/detalle
 *
 * Network: requiere stack vitalia corriendo (E2E_BASE_URL=http://localhost:3002)
 *   o puede usarse con page.route() mocks en specs que lo necesiten.
 *
 * downstream-regression-na: brand-local E2E POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";

// Slugs válidos de etapas del embudo (sync con RecommendationStage en types)
export type MarketingStageSlug =
  | "attraction"
  | "qualification"
  | "reservation"
  | "adoption"
  | "expansion";

export class MarketingPage {
  readonly page: Page;

  // ─── Locators principales ──────────────────────────────────────────────────

  /** SVG del embudo Bowtie (figure > svg role="img") */
  readonly bowtieSvg: Locator;

  /**
   * Lista de tabs del embudo (5 tabs en total).
   * Uso: await expect(mp.stageTabs).toHaveCount(5)
   */
  readonly stageTabs: Locator;

  /**
   * Sección de recomendaciones Lucas (busca el header h3 "Recomendaciones de Lucas"
   * o el contenedor con aria-label de carga).
   */
  readonly lucasCardsSection: Locator;

  /**
   * Widget de Matriz de atribución (visible en etapa "reservation").
   * Localizado por el heading "Matriz de atribución" dentro del panel.
   */
  readonly attributionMatrix: Locator;

  /**
   * Título del modal de aprobación (h2#approval-modal-title dentro de role="dialog").
   * Presente tanto en LucasRecommendationDetailModal como en LucasApprovalModal.
   */
  readonly approvalModalTitle: Locator;

  // ─── Locators de soporte ───────────────────────────────────────────────────

  /** Contenedor sticky del Bowtie (data-testid="bowtie-sticky-container") */
  readonly bowtieContainer: Locator;

  /** Nav tablist de etapas */
  readonly stageTablist: Locator;

  /** Overlay oscuro del modal (clic cierra) */
  readonly modalOverlay: Locator;

  /** Botón "Cerrar" en modal de detalle (aria-label="Cerrar") */
  readonly modalCloseButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // Bowtie: figura SVG con aria-label "Embudo de conversión"
    this.bowtieContainer = page.locator(
      '[data-testid="bowtie-sticky-container"]',
    );
    this.bowtieSvg = page.locator(
      'figure[aria-label="Embudo de conversión"] svg[role="img"]',
    );

    // Stage tabs: todos los role="tab" dentro del role="tablist"
    this.stageTablist = page.getByRole("tablist", {
      name: "Etapas del embudo",
    });
    this.stageTabs = this.stageTablist.getByRole("tab");

    // Sección Lucas: el heading h3 "Recomendaciones de Lucas"
    // El componente LucasStageRecommendationsCard emite aria-busy cuando carga
    // y muestra el h3 cuando tiene datos. Usamos el heading o el aria-label del loading.
    this.lucasCardsSection = page.locator(
      'h3:has-text("Recomendaciones de Lucas"), [aria-label="Cargando recomendaciones..."]',
    );

    // Attribution matrix: encabezado h3 "Matriz de atribución"
    this.attributionMatrix = page.locator(
      'h3:has-text("Matriz de atribución")',
    );

    // Modal de aprobación/detalle: h2 con id "approval-modal-title" o "detail-modal-title"
    this.approvalModalTitle = page.locator(
      '[role="dialog"] h2#approval-modal-title, [role="dialog"] h2#detail-modal-title',
    );

    // Modal overlay + botón cierre
    this.modalOverlay = page
      .locator('[role="dialog"] + div[aria-hidden="true"]')
      .first();
    this.modalCloseButton = page.getByRole("button", { name: "Cerrar" });
  }

  // ─── Acciones ──────────────────────────────────────────────────────────────

  /**
   * Navega a /marketing y espera a que la página cargue.
   * Usa E2E_BASE_URL definido en playwright.config.ts (por defecto http://localhost:3002).
   */
  async goto(): Promise<void> {
    await this.page.goto("/marketing");
    await this.page.waitForLoadState("domcontentloaded");
  }

  /**
   * Espera a que el Bowtie SVG sea visible (estado "listo para interactuar").
   * El SVG carga en cuanto useBowtieSummary resuelve (mock o real).
   */
  async waitForReady(): Promise<void> {
    await this.bowtieContainer.waitFor({ state: "visible", timeout: 15_000 });
  }

  /**
   * Hace clic en el tab de una etapa del embudo por slug.
   * El tab está identificado por aria-controls="stage-panel-{slug}".
   *
   * @param slug - etapa del embudo a activar
   */
  async clickStageTab(slug: MarketingStageSlug): Promise<void> {
    const tab = this.stageTablist.locator(
      `[aria-controls="stage-panel-${slug}"]`,
    );
    await tab.click();
    // Esperar a que el tabpanel correspondiente sea visible
    await this.page
      .locator(`[role="tabpanel"][id="stage-panel-${slug}"]`)
      .waitFor({ state: "visible", timeout: 10_000 });
  }

  /**
   * Hace clic en el botón "Ver detalle" del primer ítem de recomendaciones Lucas visible.
   * El botón tiene aria-label="Ver detalle: {rec.title}".
   * Requiere que haya al menos un ítem Lucas en la lista.
   */
  async clickFirstLucasCardDetail(): Promise<void> {
    const firstCard = this.page
      .getByRole("button", { name: /^Ver detalle:/i })
      .first();
    await firstCard.waitFor({ state: "visible", timeout: 10_000 });
    await firstCard.click();
    // Esperar a que el modal aparezca
    await this.page
      .locator('[role="dialog"]')
      .waitFor({ state: "visible", timeout: 10_000 });
  }

  /**
   * Cierra el modal de aprobación o detalle.
   * Estrategia: busca botón "Cancelar" (ApprovalModal) o "Cerrar" (DetailModal).
   * Si ninguno visible, usa la tecla Escape como fallback.
   */
  async closeApprovalModal(): Promise<void> {
    // ApprovalModal tiene botón "Cancelar"; DetailModal tiene botón "Cerrar"
    const cancelBtn = this.page.getByRole("button", { name: "Cancelar" });
    const closeBtn = this.page.getByRole("button", { name: "Cerrar" });

    if (await cancelBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await cancelBtn.click();
    } else if (
      await closeBtn.isVisible({ timeout: 2_000 }).catch(() => false)
    ) {
      await closeBtn.click();
    } else {
      // Fallback: ESC key (todos los modales honran handleKeyDown Escape)
      await this.page.keyboard.press("Escape");
    }

    // Esperar a que el modal desaparezca
    await this.page
      .locator('[role="dialog"]')
      .waitFor({ state: "hidden", timeout: 10_000 });
  }

  // ─── Locators helpers ──────────────────────────────────────────────────────

  /**
   * Retorna el tabpanel de una etapa específica.
   */
  stagePanel(slug: MarketingStageSlug): Locator {
    return this.page.locator(`[role="tabpanel"][id="stage-panel-${slug}"]`);
  }

  /**
   * Retorna el tab button de una etapa específica.
   */
  stageTab(slug: MarketingStageSlug): Locator {
    return this.stageTablist.locator(`[aria-controls="stage-panel-${slug}"]`);
  }
}
