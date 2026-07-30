/**
 * valeria-agenda-empty.spec.ts — SC-8 empty day + CTA crear cita
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   SC-8 "empty day renders empty state with CTA crear cita"
 *
 * Scenario coverage (04-validators.yaml):
 *   test_empty_day_cta_crear_cita
 *
 * Project: smoke
 * Depends on: AgendaViewPage + CrearCitaButtonPage POMs
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-empty.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec F2-S1
 */

import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "./fixtures/valeria-agenda.fixture";
import { setupAgendaGridMock, clearAgendaGridMock } from "./fixtures/__mocks__/agenda-grid";
import { AgendaViewPage } from "./poms/agenda-view-page.pom";
import { CrearCitaButtonPage } from "./poms/crear-cita-button-page.pom";

const { tenantId } = VALERIA_AGENDA_FIXTURE;

// ── SC-8: Empty day → EmptyState + CTA crear cita ─────────────────────────

test.describe("SC-8 — empty day shows empty state with CTA crear cita", () => {
  test.beforeEach(async ({ agendaPage }) => {
    // Return empty grid for this day
    await setupAgendaGridMock(agendaPage, "empty");
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("empty day renders empty state component", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // Empty state component must be visible
    const emptyState = agendaView.getEmptyState();
    await expect(emptyState).toBeVisible({ timeout: 8_000 });

    // Empty state has correct data-variant (not error — just no appointments)
    await expect(emptyState).toHaveAttribute("data-variant", "no-appointments");
  });

  test("empty state shows CalendarOff icon", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // CalendarOff icon (lucide icon data-testid or aria-label)
    const icon = agendaPage.locator(
      '[data-testid="empty-state-icon"], [aria-label="Sin citas"]',
    );
    await expect(icon).toBeVisible({ timeout: 5_000 });
  });

  test("empty state shows CTA 'Crear cita' button", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // CTA button visible in empty state
    const ctaBtn = agendaPage.locator(
      '[data-testid="empty-state-crear-cita-cta"]',
    );
    await expect(ctaBtn).toBeVisible({ timeout: 5_000 });

    // CTA text in Spanish neutro
    const ctaText = await ctaBtn.textContent();
    expect(ctaText).toMatch(/Crear cita|Nueva cita/i);
  });

  test("CTA 'Crear cita' in empty state opens creation dropdown", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const crearCita = new CrearCitaButtonPage(agendaPage);

    await agendaView.waitForLoaded();

    // Click the empty state CTA
    await crearCita.emptyStateCta.click();

    // Dropdown should appear with creation options
    await crearCita.dropdown.waitFor({ state: "visible", timeout: 5_000 });
    await expect(crearCita.dropdown).toBeVisible();

    // Should have at least 2 options (walk-in + teléfono)
    const labels = await crearCita.getDropdownOptionLabels();
    expect(labels.length).toBeGreaterThanOrEqual(2);
  });

  test("empty state copy in Spanish neutro LatAm", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    const emptyState = agendaView.getEmptyState();
    const text = await emptyState.textContent();

    // Spanish neutro: no voseo forms
    expect(text).not.toMatch(/\btené[sn]\b/i);
    expect(text).not.toMatch(/\bpodés\b/i);
    expect(text).not.toMatch(/\bagregá\b/i);

    // Should have content in Spanish
    expect(text).toMatch(/[ÑñáéíóúÁÉÍÓÚ]|cita|agenda|día/i);
  });

  test("empty week view also renders empty state", async ({ agendaPage }) => {
    // Switch to semana view with empty data
    // UPDATED: paradigm-map-zones T-6 — route migrated to mateo/agenda
    await agendaPage.goto(`/${tenantId}/mateo/agenda?view=semana`);
    await agendaPage.waitForLoadState("domcontentloaded");

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    const emptyState = agendaView.getEmptyState();
    await expect(emptyState).toBeVisible({ timeout: 8_000 });
  });
});
