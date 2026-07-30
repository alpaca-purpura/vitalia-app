/**
 * valeria-agenda-visual.spec.ts — Visual goldens: 3 views × 2 themes + drawer states
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   Visual goldens: 3 views × 2 themes + drawer states + subform states + mobile = ~14 snapshots
 *
 * Scenario coverage (04-validators.yaml):
 *   test_visual_goldens_agenda
 *
 * Project: visual (Desktop Chrome, --update-snapshots for baseline generation)
 * Depends on: valeria-agenda-cobro.spec.ts (step 9) + valeria-agenda-tenant-switch.spec.ts (step 10)
 *
 * IMPORTANT: Visual goldens require a RUNNING app at E2E_BASE_URL.
 * First run: --update-snapshots to generate baseline PNGs.
 * Subsequent runs: compare against baseline.
 *
 * Snapshots (~14 PNGs):
 *   01-week-view-light.png
 *   02-week-view-dark.png
 *   03-day-view-light.png
 *   04-day-view-dark.png
 *   05-month-view-light.png
 *   06-month-view-dark.png
 *   07-drawer-open-light.png
 *   08-drawer-open-dark.png
 *   09-subform-visible-light.png
 *   10-subform-error-light.png
 *   11-subform-fiscal-warning-light.png
 *   12-empty-state-light.png
 *   13-mobile-day-view-light.png
 *   14-mobile-bottom-sheet-light.png
 *
 * Run to GENERATE baseline (first time — requires app running):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/valeria-agenda-visual.spec.ts --update-snapshots
 *
 * Run to VERIFY against baseline:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/valeria-agenda-visual.spec.ts --project=visual
 *
 * NOTE: T-19 (visual goldens polish) will refine these snapshots post-feature implementation.
 * This spec establishes the structure and naming conventions.
 *
 * downstream-regression-na: brand-local vitalia E2E visual spec F2-S1
 */

import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "../regression/vitalia-fase2-valeria-agenda/fixtures/valeria-agenda.fixture";
import { setupAgendaGridMock, clearAgendaGridMock } from "../regression/vitalia-fase2-valeria-agenda/fixtures/__mocks__/agenda-grid";
import { setupPaymentAdapterMock } from "../regression/vitalia-fase2-valeria-agenda/fixtures/mock-payment-adapter";
import { AgendaViewPage } from "../regression/vitalia-fase2-valeria-agenda/poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "../regression/vitalia-fase2-valeria-agenda/poms/appointment-drawer-page.pom";
import { CobrarSaldoSubformPage } from "../regression/vitalia-fase2-valeria-agenda/poms/cobrar-saldo-subform-page.pom";

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

// Threshold: 0.1% pixel diff tolerance (stable mocked data)
const THRESHOLD = { maxDiffPixelRatio: 0.001 };

// ---------------------------------------------------------------------------
// Theme helpers
// ---------------------------------------------------------------------------

async function setLightMode(page: import("@playwright/test").Page) {
  await page.evaluate(() => {
    document.documentElement.classList.remove("dark");
    document.documentElement.setAttribute("data-theme", "light");
  });
}

async function setDarkMode(page: import("@playwright/test").Page) {
  await page.evaluate(() => {
    document.documentElement.classList.add("dark");
    document.documentElement.setAttribute("data-theme", "dark");
  });
}

// ---------------------------------------------------------------------------
// Visual goldens — calendar views × themes
// ---------------------------------------------------------------------------

test.describe("Visual goldens — calendar views × themes", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("01 week view light", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await setLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("01-week-view-light.png", {
      ...THRESHOLD,
      mask: [
        agendaPage.locator('[data-testid="agenda-freshness-indicator"]'),
      ],
    });
  });

  test("02 week view dark", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await setDarkMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("02-week-view-dark.png", {
      ...THRESHOLD,
      mask: [
        agendaPage.locator('[data-testid="agenda-freshness-indicator"]'),
      ],
    });
  });

  test("03 day view light", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await setLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("03-day-view-light.png", {
      ...THRESHOLD,
      mask: [
        agendaPage.locator('[data-testid="agenda-freshness-indicator"]'),
      ],
    });
  });

  test("04 day view dark", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await setDarkMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("04-day-view-dark.png", {
      ...THRESHOLD,
      mask: [
        agendaPage.locator('[data-testid="agenda-freshness-indicator"]'),
      ],
    });
  });

  test("05 month view light", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "mes" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await setLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("05-month-view-light.png", {
      ...THRESHOLD,
      mask: [
        agendaPage.locator('[data-testid="agenda-freshness-indicator"]'),
      ],
    });
  });

  test("06 month view dark", async ({ agendaPage }) => {
    await gotoAgenda(agendaPage, tenantId, { view: "mes" });
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await setDarkMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("06-month-view-dark.png", {
      ...THRESHOLD,
      mask: [
        agendaPage.locator('[data-testid="agenda-freshness-indicator"]'),
      ],
    });
  });
});

// ---------------------------------------------------------------------------
// Visual goldens — drawer states
// ---------------------------------------------------------------------------

test.describe("Visual goldens — drawer states", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("07 drawer open light", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await setLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("07-drawer-open-light.png", {
      ...THRESHOLD,
    });
  });

  test("08 drawer open dark", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await setDarkMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("08-drawer-open-dark.png", {
      ...THRESHOLD,
    });
  });
});

// ---------------------------------------------------------------------------
// Visual goldens — subform states
// ---------------------------------------------------------------------------

test.describe("Visual goldens — subform states", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("09 subform visible light", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();
    await subform.waitForVisible();
    await setLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("09-subform-visible-light.png", {
      ...THRESHOLD,
    });
  });

  test("10 subform error state light (503)", async ({ agendaPage }) => {
    await setupPaymentAdapterMock(agendaPage, "payment_503");

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

    await expect(subform.errorAlert).toBeVisible({ timeout: 8_000 });
    await setLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("10-subform-error-light.png", {
      ...THRESHOLD,
    });
  });
});

// ---------------------------------------------------------------------------
// Visual goldens — empty state + mobile
// ---------------------------------------------------------------------------

test.describe("Visual goldens — empty state + mobile", () => {
  test("12 empty state light", async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "empty");
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await setLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("12-empty-state-light.png", {
      ...THRESHOLD,
    });

    await clearAgendaGridMock(agendaPage);
  });

  test("13 mobile day view light", async ({ agendaPage }) => {
    await agendaPage.setViewportSize({ width: 390, height: 844 });
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();
    await setLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("13-mobile-day-view-light.png", {
      ...THRESHOLD,
      mask: [
        agendaPage.locator('[data-testid="agenda-freshness-indicator"]'),
      ],
    });

    await clearAgendaGridMock(agendaPage);
  });

  test("14 mobile bottom sheet light", async ({ agendaPage }) => {
    await agendaPage.setViewportSize({ width: 390, height: 844 });
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "dia" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await setLightMode(agendaPage);

    await expect(agendaPage).toHaveScreenshot("14-mobile-bottom-sheet-light.png", {
      ...THRESHOLD,
    });

    await clearAgendaGridMock(agendaPage);
  });
});
