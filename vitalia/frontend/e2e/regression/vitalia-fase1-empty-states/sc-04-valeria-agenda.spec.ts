/**
 * sc-04-valeria-agenda.spec.ts — SC-4 · Agenda enriquecida (ruta mateo/agenda post T-5 migration)
 * F1-S10 vitalia-fase1-empty-states — T-10
 * UPDATED: paradigm-map-zones T-6 (2026-05-30) — agenda migrada a mateo/agenda.
 *   ValeriaAgendaPage POM sigue usable pero navegando a /mateo/agenda.
 *   Valeria ya NO es tab del ribbon (supervisor sidebar only v1.2).
 *
 * Assertions:
 *   - AgendaPlaceholder mounts at /mateo/agenda (migrated from /valeria/agenda T-5)
 *   - AgendaToolbar visible (period nav + today btn + CTA crear-cita + period toggle)
 *   - AgendaFilters visible
 *   - 6 day headers: Lun 26 through Sáb 31 (from DAYS mock data)
 *   - ≥8 AgendaSlot rendered (10 mock slots in spec)
 *   - 6 lunch cells (one per day column) with aria-label="Horario de almuerzo"
 *   - AgendaSummaryFooter visible with summary text
 *   - CTA dropdown opens on click (3 origin options: walk-in / phone / outbound)
 *
 * Uses: ValeriaAgendaPage POM (overriding goto to mateo/agenda) + empty-states.fixture
 *
 * SC-4 validator: val-fe-e2e-sc04-valeria-agenda
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { ValeriaAgendaPage } from "../../pages/ValeriaAgendaPage";

// Day numbers from DAYS mock array in AgendaPlaceholder.tsx: Lun26..Sáb31
const EXPECTED_DAY_NUMS = [26, 27, 28, 29, 30, 31] as const;

/**
 * Navigate to the migrated agenda route: mateo/agenda (was valeria/agenda pre T-5).
 * ValeriaAgendaPage.goto() still navigates to valeria/agenda — override here.
 */
async function gotoMateoAgenda(
  page: import("@playwright/test").Page,
  tenantId: string,
): Promise<void> {
  // UPDATED: paradigm-map-zones T-6 — agenda moved to mateo/agenda in T-5
  await page.goto(`/${tenantId}/mateo/agenda`);
  await page.waitForLoadState("networkidle");
}

test.describe("SC-4 · Agenda enriquecida (mateo/agenda — migrada de valeria/agenda)", () => {
  test.beforeEach(async ({ shellPage, tenantId }) => {
    // UPDATED: navigate to mateo/agenda instead of valeria/agenda (paradigm-map-zones T-6)
    await gotoMateoAgenda(shellPage, tenantId);
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    await agenda.expectAgendaMounted();
  });

  test("AgendaPlaceholder monta con data-testid 'valeria-agenda-placeholder' (ruta mateo/agenda)", async ({
    shellPage,
  }) => {
    // NOTE: data-testid remains "valeria-agenda-placeholder" (component kept original testid).
    // Route changed: mateo/agenda (paradigm-map-zones T-6).
    await expect(
      shellPage.locator('[data-testid="valeria-agenda-placeholder"]').first(),
    ).toBeVisible();
  });

  test("AgendaToolbar visible con navegación de período", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    await expect(agenda.agendaToolbar).toBeVisible();
    await expect(agenda.prevPeriodButton).toBeVisible();
    await expect(agenda.nextPeriodButton).toBeVisible();
    await expect(agenda.todayButton).toBeVisible();
  });

  test("6 day headers visibles Lun26–Sáb31", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    await agenda.expectDayHeadersVisible([...EXPECTED_DAY_NUMS]);
  });

  test("≥8 AgendaSlots visibles en la grilla", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    const slotsCount = await agenda.getAgendaSlots().count();
    expect(slotsCount).toBeGreaterThanOrEqual(8);
  });

  test("6 celdas lunch Horario de almuerzo visibles", async ({ shellPage }) => {
    // One lunch cell per day column
    await expect(
      shellPage.locator('[aria-label="Horario de almuerzo"]').first(),
    ).toHaveCount(6);
  });

  test("AgendaFilters visible con controles de búsqueda", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    await agenda.expectFiltersVisible();
  });

  test("AgendaSummaryFooter visible con texto de resumen", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    await agenda.expectSummaryFooterVisible();
  });

  test("CTA Crear cita visible y dropdown abre al click", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    await expect(agenda.ctaCrearCita).toBeVisible();
    await agenda.ctaCrearCita.click();
    // Dropdown with origin options should appear
    await expect(agenda.ctaDropdown).toBeVisible();
  });

  test("period toggle semana|dia visible", async ({ shellPage }) => {
    await expect(
      shellPage.locator('[data-testid="period-toggle-semana"]').first(),
    ).toBeVisible();
    await expect(
      shellPage.locator('[data-testid="period-toggle-dia"]').first(),
    ).toBeVisible();
  });

  test("AgendaSlot confirmed tiene slot-pill-confirmed", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    // At least one confirmed slot in mock data
    await expect(agenda.getSlotPill("confirmed").first()).toBeVisible();
  });

  test("visual week-default · grilla completa Lun26 + 10 slots + footer", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);
    // Full visual state check
    await agenda.expectAgendaMounted();
    await agenda.expectDayHeadersVisible([...EXPECTED_DAY_NUMS]);
    const slotsCount = await agenda.getAgendaSlots().count();
    expect(slotsCount).toBeGreaterThanOrEqual(8);
    await agenda.expectSummaryFooterVisible();
  });

  test("responsive · agenda visible en 3 breakpoints (ruta mateo/agenda)", async ({
    shellPage,
    tenantId,
  }) => {
    const agenda = new ValeriaAgendaPage(shellPage, tenantId);

    // Mobile 375px — UPDATED: gotoMateoAgenda (was agenda.goto() → valeria/agenda)
    await shellPage.setViewportSize({ width: 375, height: 812 });
    await gotoMateoAgenda(shellPage, tenantId);
    await expect(agenda.agendaPlaceholder).toBeVisible();

    // Tablet 768px
    await shellPage.setViewportSize({ width: 768, height: 1024 });
    await gotoMateoAgenda(shellPage, tenantId);
    await expect(agenda.agendaPlaceholder).toBeVisible();

    // Desktop 1280px
    await shellPage.setViewportSize({ width: 1280, height: 800 });
    await gotoMateoAgenda(shellPage, tenantId);
    await expect(agenda.agendaPlaceholder).toBeVisible();
  });
});
