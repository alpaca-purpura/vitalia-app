/**
 * valeria-agenda-mobile.spec.ts — mobile responsive (day only + bottom-sheet)
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   <md responsive: day only + bottom-sheet 95vh + chip carousel + FAB
 *
 * Scenario coverage (04-validators.yaml):
 *   test_mobile_responsive_bottom_sheet_fab
 *
 * Project: mobile (Playwright mobile project — iPhone 14 Pro via device emulation)
 * Also runs on: smoke with viewport override for CI coverage
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-mobile.spec.ts \
 *     --project=mobile
 *
 * downstream-regression-na: brand-local vitalia E2E spec F2-S1
 */

import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "./fixtures/valeria-agenda.fixture";
import { setupAgendaGridMock, clearAgendaGridMock } from "./fixtures/__mocks__/agenda-grid";
import { AgendaViewPage } from "./poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "./poms/appointment-drawer-page.pom";
import { CrearCitaButtonPage } from "./poms/crear-cita-button-page.pom";

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

// Mobile viewport helper
async function setMobileViewport(page: import("@playwright/test").Page) {
  await page.setViewportSize({ width: 390, height: 844 }); // iPhone 14 Pro
}

// ── Mobile responsive tests ────────────────────────────────────────────────

test.describe("Mobile responsive — bottom-sheet + FAB + chip carousel", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await setMobileViewport(agendaPage);
    // Mobile: day view only (week/month not available on <md)
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("mobile shows day view only (week toggle hidden on small screens)", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // Semana toggle should be hidden on mobile (< md breakpoint)
    const semanaToggle = agendaView.getViewToggle("semana");
    await expect(semanaToggle).not.toBeVisible({ timeout: 3_000 });

    // Dia toggle may or may not be visible depending on mobile UI design —
    // what matters is the grid renders day view
    await expect(agendaView.calendarGrid).toBeVisible();
  });

  test("appointment slot opens bottom sheet (95vh) on mobile", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();

    // On mobile, drawer is a bottom sheet (95vh height)
    const drawerHeight = await agendaPage.evaluate(() => {
      const panel = document.querySelector('[data-testid="appointment-drawer"]');
      if (!panel) return 0;
      return panel.getBoundingClientRect().height;
    });

    const viewportHeight = 844; // iPhone 14 Pro
    const expectedMinHeight = viewportHeight * 0.85; // allow 85-100% range

    // Bottom sheet should occupy ≥ 85% of viewport height
    expect(drawerHeight).toBeGreaterThan(expectedMinHeight);
  });

  test("FAB '+ Crear cita' visible on mobile day view", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const crearCita = new CrearCitaButtonPage(agendaPage);

    await agendaView.waitForLoaded();

    // FAB should be visible on mobile (toolbar button may be hidden)
    await expect(crearCita.fabButton).toBeVisible({ timeout: 5_000 });
  });

  test("FAB opens creation dropdown on mobile", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const crearCita = new CrearCitaButtonPage(agendaPage);

    await agendaView.waitForLoaded();
    await crearCita.openDropdownFromFab();

    // Dropdown visible with options
    await expect(crearCita.dropdown).toBeVisible();
    const labels = await crearCita.getDropdownOptionLabels();
    expect(labels.length).toBeGreaterThanOrEqual(2);
  });

  test("chip filters row scrollable horizontally on mobile", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // Chips row should be visible (carousel / horizontal scroll)
    await expect(agendaView.filtersRow).toBeVisible({ timeout: 5_000 });

    // Row should be scrollable (overflow-x: auto or scroll)
    const isScrollable = await agendaPage.evaluate(() => {
      const row = document.querySelector('[data-testid="agenda-filters-row"]');
      if (!row) return false;
      const style = window.getComputedStyle(row);
      return (
        style.overflowX === "auto" ||
        style.overflowX === "scroll" ||
        // OR the scroll width exceeds client width (actually has overflow)
        row.scrollWidth > row.clientWidth
      );
    });

    expect(isScrollable).toBe(true);
  });

  test("bottom sheet drawer closes on swipe down (or Escape)", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();

    // Close with Escape (keyboard) — swipe gestures not supported in all Playwright contexts
    await drawer.closeWithEscape();
    await expect(drawer.panel).not.toBeVisible({ timeout: 5_000 });
  });

  test("mobile layout does not expose PHI in DOM attributes", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // Check that no data attribute on slots contains raw DNI patterns
    const slots = agendaPage.locator('[data-testid^="agenda-slot-"]');
    const count = await slots.count();

    for (let i = 0; i < Math.min(count, 5); i++) {
      const slot = slots.nth(i);
      const attributes = await slot.evaluate((el) => {
        const result: Record<string, string> = {};
        for (const attr of el.attributes) {
          result[attr.name] = attr.value;
        }
        return result;
      });

      // No attribute value should be an 8-digit DNI
      for (const [, value] of Object.entries(attributes)) {
        expect(value).not.toMatch(/^\d{8}$/);
      }
    }
  });
});
