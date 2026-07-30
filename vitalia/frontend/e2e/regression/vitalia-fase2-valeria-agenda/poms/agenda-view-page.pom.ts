/**
 * agenda-view-page.pom.ts — AgendaViewPage POM
 *
 * Page Object Model for the Valeria Agenda calendar view.
 * Encapsulates locators + actions for the main calendar grid.
 *
 * Methods per 04-validators.yaml test_construction_plan step 5:
 *   getViewToggle, clickView, getDatePicker, getChipPreset,
 *   getSlot, getCrearCitaButton, getFreshnessIndicator, waitForLoaded
 *
 * Locators: data-testid first, ARIA as fallback (per playwright-expert SSoT).
 * No assertions in POM methods — only actions + locators.
 *
 * downstream-regression-na: brand-local vitalia E2E POM F2-S1
 *
 * @see 04-validators.yaml § poms_required[0]: AgendaViewPage
 * @see 03-arch.md § 3 (calendar grid component spec)
 */

import type { Page, Locator } from "@playwright/test";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type AgendaView = "semana" | "dia" | "mes";
export type PresetFilter =
  | "hoy"
  | "por-confirmar"
  | "re-agendar"
  | "no-shows"
  | "saldos";

// ---------------------------------------------------------------------------
// AgendaViewPage POM
// ---------------------------------------------------------------------------

export class AgendaViewPage {
  readonly page: Page;
  readonly tenantId: string;

  // ── Main container ────────────────────────────────────────────────────────

  /** Full agenda container */
  readonly container: Locator;
  /** Calendar grid (week/day/month) */
  readonly calendarGrid: Locator;
  /** Toolbar with view toggle + date nav + create button */
  readonly toolbar: Locator;
  /** Chip filters row */
  readonly filtersRow: Locator;
  /** Freshness indicator ("Actualizado hace Xs") */
  readonly freshnessIndicator: Locator;
  /** Loading skeleton */
  readonly skeleton: Locator;
  /** Empty state component */
  readonly emptyState: Locator;

  constructor(page: Page, tenantId: string) {
    this.page = page;
    this.tenantId = tenantId;

    this.container = page.locator('[data-testid="valeria-agenda-root"]');
    this.calendarGrid = page.locator('[data-testid="agenda-calendar-grid"]');
    this.toolbar = page.locator('[data-testid="agenda-toolbar"]').first();
    this.filtersRow = page.locator('[data-testid="agenda-filters-row"]');
    this.freshnessIndicator = page.locator(
      '[data-testid="agenda-freshness-indicator"]',
    );
    this.skeleton = page.locator('[data-testid="agenda-skeleton"]');
    this.emptyState = page.locator('[data-testid="agenda-empty-state"]');
  }

  // ── Navigation ────────────────────────────────────────────────────────────

  /**
   * Navigate to the agenda route.
   * @param view - optional view to set via URL param
   * @param date - optional date (YYYY-MM-DD) to set via URL param
   */
  async goto(
    view?: AgendaView,
    date?: string,
  ): Promise<void> {
    const params = new URLSearchParams();
    if (view) params.set("view", view);
    if (date) params.set("date", date);
    const qs = params.toString() ? `?${params.toString()}` : "";
    // UPDATED: paradigm-map-zones T-6 (2026-05-30) — route migrated to mateo/agenda.
    // Was: /${this.tenantId}/valeria/agenda (pre paradigm-map-zones T-5)
    await this.page.goto(`/${this.tenantId}/mateo/agenda${qs}`);
    await this.page.waitForLoadState("domcontentloaded");
  }

  // ── View controls ─────────────────────────────────────────────────────────

  /**
   * Get the view toggle button for a specific view.
   */
  getViewToggle(view: AgendaView): Locator {
    return this.page.locator(
      `[data-testid="agenda-view-toggle-${view}"]`,
    );
  }

  /**
   * Click the view toggle to switch calendar view.
   * Waits for the grid to re-render after switching.
   */
  async clickView(view: AgendaView): Promise<void> {
    await this.getViewToggle(view).click();
    await this.waitForLoaded();
  }

  // ── Date navigation ───────────────────────────────────────────────────────

  /**
   * Get the date picker/header showing the current period.
   */
  getDatePicker(): Locator {
    return this.page.locator('[data-testid="agenda-date-picker"]');
  }

  /**
   * Click the "previous period" navigation arrow.
   */
  async clickPrevPeriod(): Promise<void> {
    await this.page
      .locator('[data-testid="agenda-prev-period"]')
      .click();
    await this.waitForLoaded();
  }

  /**
   * Click the "next period" navigation arrow.
   */
  async clickNextPeriod(): Promise<void> {
    await this.page
      .locator('[data-testid="agenda-next-period"]')
      .click();
    await this.waitForLoaded();
  }

  /**
   * Click "Hoy" to navigate to the current period.
   */
  async clickHoy(): Promise<void> {
    await this.page.locator('[data-testid="agenda-today-btn"]').click();
    await this.waitForLoaded();
  }

  // ── Preset chip filters ───────────────────────────────────────────────────

  /**
   * Get a preset filter chip by slug.
   */
  getChipPreset(preset: PresetFilter): Locator {
    return this.page.locator(
      `[data-testid="agenda-chip-${preset}"]`,
    );
  }

  /**
   * Click a preset filter chip.
   */
  async filterByPreset(preset: PresetFilter): Promise<void> {
    await this.getChipPreset(preset).click();
    await this.waitForLoaded();
  }

  // ── Slot locators ─────────────────────────────────────────────────────────

  /**
   * Get an agenda slot by patient masked name.
   * Matches aria-label containing the masked patient name.
   */
  getSlotByPatient(maskedName: string): Locator {
    return this.page
      .locator(`[data-testid="agenda-slot"]`)
      .filter({ hasText: maskedName })
      .first();
  }

  /**
   * Get a slot by its appointment ID.
   */
  getSlot(appointmentId: string): Locator {
    return this.page.locator(
      `[data-testid="agenda-slot-${appointmentId}"]`,
    );
  }

  /**
   * Get the count of visible slots in the current view.
   */
  async getRowCount(): Promise<number> {
    return await this.page.locator('[data-testid="agenda-slot"]').count();
  }

  /**
   * Click a slot by appointment ID to open the drawer.
   */
  async clickSlot(appointmentId: string): Promise<void> {
    await this.getSlot(appointmentId).click();
  }

  // ── + Crear cita button ───────────────────────────────────────────────────

  /**
   * Get the "+ Crear cita" button/dropdown trigger.
   */
  getCrearCitaButton(): Locator {
    return this.page.locator('[data-testid="agenda-crear-cita-btn"]');
  }

  // ── Freshness indicator ───────────────────────────────────────────────────

  /**
   * Get the freshness indicator with its current text.
   */
  getFreshnessIndicator(): Locator {
    return this.freshnessIndicator;
  }

  /**
   * Wait for the freshness indicator to show a timestamp ≤ {seconds} seconds old.
   * Polls until the text matches "Actualizado hace Xs" where X ≤ seconds.
   */
  async waitForFreshness(maxAgeSeconds: number): Promise<void> {
    await this.page.waitForFunction(
      (maxAge: number) => {
        const el = document.querySelector(
          '[data-testid="agenda-freshness-indicator"]',
        );
        if (!el) return false;
        const text = el.textContent ?? "";
        const match = text.match(/Actualizado hace (\d+)s/);
        if (!match) return false;
        return parseInt(match[1], 10) <= maxAge;
      },
      maxAgeSeconds,
      { timeout: (maxAgeSeconds + 5) * 1000 },
    );
  }

  // ── Loading / error states ────────────────────────────────────────────────

  /**
   * Wait for the calendar grid to finish loading.
   * Waits for skeleton to disappear + grid to appear.
   */
  async waitForLoaded(): Promise<void> {
    // Wait for skeleton to disappear (or not appear at all)
    await this.page
      .waitForSelector('[data-testid="agenda-skeleton"]', {
        state: "detached",
        timeout: 10_000,
      })
      .catch(() => {
        // skeleton may never appear for fast loads — that's fine
      });
    // Wait for grid or empty state
    await this.page.waitForSelector(
      '[data-testid="agenda-calendar-grid"], [data-testid="agenda-empty-state"]',
      { timeout: 15_000 },
    );
  }

  /**
   * Get the empty state component (if visible).
   */
  getEmptyState(): Locator {
    return this.emptyState;
  }

  /**
   * Get the manual retry button inside an error empty state.
   */
  getRetryButton(): Locator {
    return this.page.locator('[data-testid="agenda-retry-btn"]');
  }
}
