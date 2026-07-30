/**
 * vitalia-fase2-valeria-agenda.spec.ts — Visual goldens T-19
 *
 * F2-S1 vitalia-fase2-valeria-agenda
 * Ticket: T-19 — FE visual goldens (~14 snapshots) + cleanup AgendaPlaceholder
 *
 * 14 snapshots:
 *   Calendar (3 views × 2 themes = 6):
 *     1. agenda-day-light.png
 *     2. agenda-day-dark.png
 *     3. agenda-week-light.png
 *     4. agenda-week-dark.png
 *     5. agenda-month-light.png
 *     6. agenda-month-dark.png
 *   Drawer (2 themes = 2):
 *     7. drawer-detail-light.png
 *     8. drawer-detail-dark.png
 *   Subform Cobrar saldo (2 themes = 2):
 *     9. drawer-cobrar-saldo-light.png
 *    10. drawer-cobrar-saldo-dark.png
 *   Mobile (1):
 *    11. mobile-drawer-fullscreen.png
 *   Preset filters chip row (1):
 *    12. preset-filters.png
 *   Empty state (1):
 *    13. agenda-empty-state.png
 *   Crear cita dropdown (1):
 *    14. crear-cita-dropdown.png
 *
 * Threshold: maxDiffPixelRatio: 0.001 (0.1% tolerance)
 * Animations disabled (playwright.config.ts project=visual)
 * Tenant + clinic fixed: clinica-sonrisa-pe (PEN locale) — deterministic
 * DB seed: fixture MSW mock (deterministic, no live backend required)
 *
 * Snapshot output path (per snapshotPathTemplate):
 *   vitalia/frontend/e2e/__screenshots__/visual/vitalia-fase2-valeria-agenda.spec.ts/
 *   {name}-chromium.png
 *
 * Run to GENERATE baseline (first time — requires app running on E2E_BASE_URL):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/vitalia-fase2-valeria-agenda.spec.ts --project=visual --update-snapshots
 *
 * Run to VERIFY against baseline:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/vitalia-fase2-valeria-agenda.spec.ts --project=visual
 *
 * G5 pre-commit smoke gate (no running stack required):
 *   cd vitalia/frontend && npx tsc --noEmit
 *   npx eslint e2e/visual/vitalia-fase2-valeria-agenda.spec.ts --cache
 *   npx playwright test --list e2e/visual/vitalia-fase2-valeria-agenda.spec.ts
 *
 * downstream-regression-na: brand-local vitalia E2E visual spec F2-S1 T-19
 *
 * @see T-17-result.md — POMs + fixtures (dependency)
 * @see 06-tickets.yaml T-19 deliverables
 * @see vitalia/.claude/rules/shell-mockup-per-component.md — ratchet rule
 */

import { expect } from "@playwright/test";
import {
  test,
  VALERIA_AGENDA_FIXTURE,
  gotoAgenda,
} from "../regression/vitalia-fase2-valeria-agenda/fixtures/valeria-agenda.fixture";
import {
  setupAgendaGridMock,
  clearAgendaGridMock,
} from "../regression/vitalia-fase2-valeria-agenda/fixtures/__mocks__/agenda-grid";
import { setupPaymentAdapterMock } from "../regression/vitalia-fase2-valeria-agenda/fixtures/mock-payment-adapter";
import { AgendaViewPage } from "../regression/vitalia-fase2-valeria-agenda/poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "../regression/vitalia-fase2-valeria-agenda/poms/appointment-drawer-page.pom";
import { CobrarSaldoSubformPage } from "../regression/vitalia-fase2-valeria-agenda/poms/cobrar-saldo-subform-page.pom";
import { CrearCitaButtonPage } from "../regression/vitalia-fase2-valeria-agenda/poms/crear-cita-button-page.pom";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

/** 0.1% pixel diff tolerance for stable mocked data. */
const THRESHOLD = { maxDiffPixelRatio: 0.001 } as const;

/** Mask dynamic freshness indicator to avoid timestamp flakiness. */
const FRESHNESS_MASK = (page: import("@playwright/test").Page) => [
  page.locator('[data-testid="agenda-freshness-indicator"]'),
];

// ---------------------------------------------------------------------------
// Theme helpers
// ---------------------------------------------------------------------------

async function applyLightMode(
  page: import("@playwright/test").Page,
): Promise<void> {
  await page.evaluate(() => {
    document.documentElement.classList.remove("dark");
    document.documentElement.setAttribute("data-theme", "light");
  });
}

async function applyDarkMode(
  page: import("@playwright/test").Page,
): Promise<void> {
  await page.evaluate(() => {
    document.documentElement.classList.add("dark");
    document.documentElement.setAttribute("data-theme", "dark");
  });
}

// ---------------------------------------------------------------------------
// 1–6: Calendar 3 views × 2 themes
// ---------------------------------------------------------------------------

test.describe("Calendar views — light theme", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("agenda-day-light — día view, light mode", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await applyLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("agenda-day-light.png", {
      ...THRESHOLD,
      mask: FRESHNESS_MASK(agendaPage),
    });
  });

  test("agenda-week-light — semana view, light mode", async ({
    agendaPage,
  }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await applyLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("agenda-week-light.png", {
      ...THRESHOLD,
      mask: FRESHNESS_MASK(agendaPage),
    });
  });

  test("agenda-month-light — mes view, light mode", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "mes" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await applyLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("agenda-month-light.png", {
      ...THRESHOLD,
      mask: FRESHNESS_MASK(agendaPage),
    });
  });
});

test.describe("Calendar views — dark theme", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("agenda-day-dark — día view, dark mode", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await applyDarkMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("agenda-day-dark.png", {
      ...THRESHOLD,
      mask: FRESHNESS_MASK(agendaPage),
    });
  });

  test("agenda-week-dark — semana view, dark mode", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await applyDarkMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("agenda-week-dark.png", {
      ...THRESHOLD,
      mask: FRESHNESS_MASK(agendaPage),
    });
  });

  test("agenda-month-dark — mes view, dark mode", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "mes" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await applyDarkMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("agenda-month-dark.png", {
      ...THRESHOLD,
      mask: FRESHNESS_MASK(agendaPage),
    });
  });
});

// ---------------------------------------------------------------------------
// 7–8: Drawer detail (appointment open) × 2 themes
// ---------------------------------------------------------------------------

test.describe("Drawer detail — both themes", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("drawer-detail-light — drawer abierto, light mode", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await applyLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("drawer-detail-light.png", {
      ...THRESHOLD,
    });
  });

  test("drawer-detail-dark — drawer abierto, dark mode", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await applyDarkMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("drawer-detail-dark.png", {
      ...THRESHOLD,
    });
  });
});

// ---------------------------------------------------------------------------
// 9–10: Subform Cobrar saldo × 2 themes
// ---------------------------------------------------------------------------

test.describe("Cobrar saldo subform — both themes", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("drawer-cobrar-saldo-light — subform expandido, light mode", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();
    await subform.waitForVisible();
    await applyLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("drawer-cobrar-saldo-light.png", {
      ...THRESHOLD,
    });
  });

  test("drawer-cobrar-saldo-dark — subform expandido, dark mode", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();
    await subform.waitForVisible();
    await applyDarkMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("drawer-cobrar-saldo-dark.png", {
      ...THRESHOLD,
    });
  });
});

// ---------------------------------------------------------------------------
// 11: Mobile — drawer fullscreen (bottom-sheet 95vh en viewport 390×844)
// ---------------------------------------------------------------------------

test.describe("Mobile — drawer fullscreen", () => {
  test("mobile-drawer-fullscreen — bottom-sheet open, mobile viewport", async ({
    agendaPage,
  }) => {
    // Set mobile viewport (iPhone 13 equiv)
    await agendaPage.setViewportSize({ width: 390, height: 844 });
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await applyLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("mobile-drawer-fullscreen.png", {
      ...THRESHOLD,
      mask: FRESHNESS_MASK(agendaPage),
    });

    await clearAgendaGridMock(agendaPage);
  });
});

// ---------------------------------------------------------------------------
// 12: Preset filters chip row
// ---------------------------------------------------------------------------

test.describe("Preset filters chip row", () => {
  test("preset-filters — chip row con todos los filtros visibles", async ({
    agendaPage,
  }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await applyLightMode(agendaPage);

    // Capture only the preset filters strip (not full page) for precision
    const filtersLocator = agendaPage.locator(
      '[data-testid="agenda-preset-filters"]',
    );
    await expect(filtersLocator).toBeVisible();

    await expect(filtersLocator).toHaveScreenshot("preset-filters.png", {
      ...THRESHOLD,
    });

    await clearAgendaGridMock(agendaPage);
  });
});

// ---------------------------------------------------------------------------
// 13: Empty state — día sin slots
// ---------------------------------------------------------------------------

test.describe("Empty state", () => {
  test("agenda-empty-state — día sin turnos, empty state visible", async ({
    agendaPage,
  }) => {
    await setupAgendaGridMock(agendaPage, "empty");
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await applyLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("agenda-empty-state.png", {
      ...THRESHOLD,
    });

    await clearAgendaGridMock(agendaPage);
  });
});

// ---------------------------------------------------------------------------
// 14: Crear cita dropdown open
// ---------------------------------------------------------------------------

test.describe("Crear cita dropdown", () => {
  test("crear-cita-dropdown — dropdown con 3 opciones visible", async ({
    agendaPage,
  }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const crearCita = new CrearCitaButtonPage(agendaPage);

    await agendaView.waitForLoaded();
    await applyLightMode(agendaPage);

    // Open the dropdown to capture its visible state
    await crearCita.openDropdown();
    const dropdownLocator = agendaPage.locator(
      '[data-testid="crear-cita-dropdown"]',
    );
    await expect(dropdownLocator).toBeVisible();

    await expect(agendaPage).toHaveScreenshot("crear-cita-dropdown.png", {
      ...THRESHOLD,
    });

    await clearAgendaGridMock(agendaPage);
  });
});

// ---------------------------------------------------------------------------
// Supplemental: Payment adapter mock smoke (referenced by SC-1 gherkin)
// ---------------------------------------------------------------------------

test.describe("Visual — SC-1 cobrar saldo success (gherkin golden)", () => {
  test("drawer-cobrar-saldo after charge succeeded — slot updates (light)", async ({
    agendaPage,
  }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await setupPaymentAdapterMock(agendaPage, "success");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();
    await subform.waitForVisible();
    await subform.fillForm({ method: "tarjeta" });
    await subform.submit();
    // Success state: toast + slot status update
    await subform.waitForSuccessToast();
    await applyLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot(
      "drawer-cobrar-saldo-success-light.png",
      { ...THRESHOLD },
    );

    await clearAgendaGridMock(agendaPage);
  });
});
