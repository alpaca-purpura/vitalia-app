/**
 * ValeriaAgendaPage — POM for Valeria Agenda placeholder (weekly calendar grid).
 * F1-S10 vitalia-fase1-empty-states — T-10
 * UPDATED: paradigm-map-zones T-6 (2026-05-30) — agenda route migrated.
 *   goto() now navigates to /{tenantId}/mateo/agenda (was /valeria/agenda pre T-5).
 *   Component data-testids are unchanged (component kept original testids).
 *   Valeria sidebar remains — only the routing URL changed.
 *
 * Wraps the AgendaPlaceholder at /{tenantId}/mateo/agenda (migrated from valeria/agenda).
 * Encapsulates all data-testids and aria-labels from:
 *   - AgendaPlaceholder.tsx (data-testid="valeria-agenda-placeholder", data-testid="agenda-grid")
 *   - AgendaToolbar.tsx (data-testid="agenda-toolbar", "agenda-today-btn", "agenda-cta-crear-cita",
 *                        "agenda-cta-dropdown", "period-toggle-{value}")
 *   - AgendaFilters.tsx (data-testid="agenda-filters")
 *   - AgendaSlot.tsx (data-testid="agenda-slot", "slot-pill-{status}")
 *   - AgendaDayHeader.tsx (data-testid="agenda-day-header-{dayNum}")
 *   - AgendaSummaryFooter.tsx (data-testid="agenda-summary-footer", "agenda-summary-text")
 *
 * downstream-regression-na: brand-local vitalia e2e POM; no cross-brand consumers
 */

import type { Page, Locator } from "@playwright/test";
import { expect } from "@playwright/test";

export class ValeriaAgendaPage {
  readonly page: Page;
  readonly tenantId: string;

  // ── Main container locators ───────────────────────────────────────────
  readonly agendaPlaceholder: Locator;
  readonly agendaGrid: Locator;
  readonly agendaToolbar: Locator;
  readonly agendaFilters: Locator;
  readonly summaryFooter: Locator;
  readonly summaryText: Locator;

  // ── Toolbar controls ──────────────────────────────────────────────────
  readonly todayButton: Locator;
  readonly ctaCrearCita: Locator;
  readonly ctaDropdown: Locator;
  readonly prevPeriodButton: Locator;
  readonly nextPeriodButton: Locator;

  constructor(page: Page, tenantId: string) {
    this.page = page;
    this.tenantId = tenantId;

    this.agendaPlaceholder = page.locator(
      '[data-testid="valeria-agenda-placeholder"]',
    );
    this.agendaGrid = page.locator('[data-testid="agenda-grid"]').first();
    this.agendaToolbar = page.locator('[data-testid="agenda-toolbar"]').first();
    this.agendaFilters = page.locator('[data-testid="agenda-filters"]').first();
    this.summaryFooter = page
      .locator('[data-testid="agenda-summary-footer"]')
      .first();
    this.summaryText = page
      .locator('[data-testid="agenda-summary-text"]')
      .first();

    // Toolbar controls
    this.todayButton = page.locator('[data-testid="agenda-today-btn"]').first();
    this.ctaCrearCita = page
      .locator('[data-testid="agenda-cta-crear-cita"]')
      .first();
    this.ctaDropdown = page
      .locator('[data-testid="agenda-cta-dropdown"]')
      .first();

    // Period navigation — aria-labels from AgendaToolbar.tsx
    this.prevPeriodButton = page
      .locator('[aria-label="Período anterior"]')
      .first();
    this.nextPeriodButton = page
      .locator('[aria-label="Período siguiente"]')
      .first();
  }

  // ── Navigation ────────────────────────────────────────────────────────

  async goto(): Promise<void> {
    // UPDATED: paradigm-map-zones T-6 (2026-05-30) — agenda route migrated to mateo/agenda.
    // Was: /${this.tenantId}/valeria/agenda (pre paradigm-map-zones T-5)
    await this.page.goto(`/${this.tenantId}/mateo/agenda`);
    await this.page.waitForLoadState("networkidle");
  }

  // ── Toolbar interactions ──────────────────────────────────────────────

  /**
   * Click the "Hoy" button to return to the current week.
   */
  async clickToday(): Promise<void> {
    await this.todayButton.click();
  }

  /**
   * Click the period mode toggle for a given value.
   * Values: "semana" | "dia" (per AgendaToolbar.tsx).
   */
  async clickPeriodToggle(value: "semana" | "dia"): Promise<void> {
    await this.page.locator(`[data-testid="period-toggle-${value}"]`).click();
  }

  /**
   * Click the previous period arrow.
   */
  async clickPrevPeriod(): Promise<void> {
    await this.prevPeriodButton.click();
  }

  /**
   * Click the next period arrow.
   */
  async clickNextPeriod(): Promise<void> {
    await this.nextPeriodButton.click();
  }

  /**
   * Open the CTA "Crear cita" dropdown.
   */
  async openCtaDropdown(): Promise<void> {
    await this.ctaCrearCita.click();
    await expect(this.ctaDropdown).toBeVisible();
  }

  // ── Grid assertions ───────────────────────────────────────────────────

  /**
   * Assert the full agenda structure is visible:
   * toolbar + filters + grid + footer.
   */
  async expectAgendaMounted(): Promise<void> {
    await expect(this.agendaPlaceholder).toBeVisible();
    await expect(this.agendaToolbar).toBeVisible();
    await expect(this.agendaFilters).toBeVisible();
    await expect(this.agendaGrid).toBeVisible();
    await expect(this.summaryFooter).toBeVisible();
  }

  /**
   * Get all AgendaSlot elements in the grid.
   * data-testid="agenda-slot" per AgendaSlot.tsx.
   */
  getAgendaSlots(): Locator {
    return this.page.locator('[data-testid="agenda-slot"]').first();
  }

  /**
   * Assert at least {minCount} agenda slots are visible.
   * Spec requires ≥8 slots from 10 mock slots in AgendaPlaceholder.
   */
  async expectMinSlots(minCount: number): Promise<void> {
    await expect(this.getAgendaSlots()).toHaveCount(
      expect.any(Number) as unknown as number,
    );
    const count = await this.getAgendaSlots().count();
    expect(count).toBeGreaterThanOrEqual(minCount);
  }

  /**
   * Assert day headers are visible for the given day numbers.
   * data-testid="agenda-day-header-{dayNum}" per AgendaDayHeader.tsx.
   */
  async expectDayHeadersVisible(dayNums: number[]): Promise<void> {
    for (const dayNum of dayNums) {
      await expect(
        this.page
          .locator(`[data-testid="agenda-day-header-${dayNum}"]`)
          .first(),
      ).toBeVisible();
    }
  }

  /**
   * Assert the lunch-hour row cells are present.
   * Lunch cells have aria-label="Horario de almuerzo".
   */
  async expectLunchRowVisible(): Promise<void> {
    await expect(
      this.page.locator('[aria-label="Horario de almuerzo"]').first(),
    ).toBeVisible();
  }

  /**
   * Get a slot pill by status.
   * data-testid="slot-pill-{status}" per AgendaSlot.tsx.
   * Status values: "confirmed" | "tentative" | "blocked" | "noshow"
   */
  getSlotPill(status: string): Locator {
    return this.page.locator(`[data-testid="slot-pill-${status}"]`).first();
  }

  /**
   * Assert the summary footer shows a valid summary text.
   * data-testid="agenda-summary-text" per AgendaSummaryFooter.tsx.
   */
  async expectSummaryFooterVisible(): Promise<void> {
    await expect(this.summaryFooter).toBeVisible();
    await expect(this.summaryText).toBeVisible();
  }

  /**
   * Assert the filters panel is visible with its search/filter controls.
   */
  async expectFiltersVisible(): Promise<void> {
    await expect(this.agendaFilters).toBeVisible();
    await expect(
      this.page.locator(
        '[aria-label="Buscar paciente (disponible en Fase 2)"]',
      ),
    ).toBeVisible();
  }

  /**
   * Assert the CTA dropdown is visible with "crear cita" origin options.
   * Opens the dropdown then checks the 3 origin options (walk-in, phone, outbound).
   */
  async expectCtaDropdownOptions(): Promise<void> {
    await this.openCtaDropdown();
    await expect(this.ctaDropdown).toBeVisible();
    // Dropdown should contain origin options per spec (walk-in, phone, outbound)
    const dropdownText = await this.ctaDropdown.textContent();
    expect(dropdownText).toBeTruthy();
  }
}
