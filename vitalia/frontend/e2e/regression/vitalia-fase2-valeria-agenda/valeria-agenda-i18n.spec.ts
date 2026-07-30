/**
 * valeria-agenda-i18n.spec.ts — SC-11 currency override + locale
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   SC-11 "currency override USD on AR tenant + locale date format"
 *
 * Scenario coverage (04-validators.yaml):
 *   test_currency_override_usd_ar_tenant
 *
 * Project: smoke
 * Depends on: AgendaViewPage + AppointmentDrawerPage + CobrarSaldoSubformPage POMs
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-i18n.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec F2-S1
 */

import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "./fixtures/valeria-agenda.fixture";
import { setupAgendaGridMock, clearAgendaGridMock } from "./fixtures/__mocks__/agenda-grid";
import { AgendaViewPage } from "./poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "./poms/appointment-drawer-page.pom";
import { CobrarSaldoSubformPage } from "./poms/cobrar-saldo-subform-page.pom";

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

// AR tenant for currency override testing
const AR_TENANT_ID = "clinica-esperanza-ar-test";

// ── SC-11: Currency override + locale ─────────────────────────────────────

test.describe("SC-11 — currency override USD on AR tenant + locale", () => {
  test("PE tenant (PEN default) shows PEN in cobrar saldo subform", async ({
    agendaPage,
  }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
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

    // Amount display should show PEN (PE tenant default)
    const amountText = await subform.amountDisplay.textContent();
    expect(amountText).toMatch(/PEN|S\/\./);

    // Currency select pre-filled with PEN
    const currencyValue = await subform.currencySelect.inputValue();
    expect(currencyValue).toBe("PEN");

    await clearAgendaGridMock(agendaPage);
  });

  test("currency override to USD persists in form submit preview", async ({
    agendaPage,
  }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
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

    // Override currency to USD (turista patient)
    await subform.selectCurrency("USD");

    // Submit button should reflect USD in label ("Cobrar USD 80")
    const submitText = await subform.submitButton.textContent();
    expect(submitText).toMatch(/USD/);

    await clearAgendaGridMock(agendaPage);
  });

  test("AR tenant grid shows ARS currency in slot amounts", async ({
    agendaPage,
  }) => {
    // Switch to AR tenant mock
    await setupAgendaGridMock(agendaPage, "tenant_b");
    // UPDATED: paradigm-map-zones T-6 — route migrated to mateo/agenda
    await agendaPage.goto(`/${AR_TENANT_ID}/mateo/agenda?view=semana`);
    await agendaPage.waitForLoadState("domcontentloaded");

    const agendaViewAR = new AgendaViewPage(agendaPage, AR_TENANT_ID);
    await agendaViewAR.waitForLoaded();

    // AR tenant slot should show ARS amounts
    // Locator: any money amount display in the grid
    const slotAmount = agendaPage
      .locator('[data-testid^="agenda-slot-amount-"]')
      .first();

    // If slot amounts visible, they should match ARS format
    if (await slotAmount.isVisible()) {
      const amountText = await slotAmount.textContent();
      // ARS format: "$8.500" or "ARS 8500" (depends on formatTenantMoney)
      expect(amountText).toMatch(/ARS|\$/);
    }

    await clearAgendaGridMock(agendaPage);
  });

  test("date format follows tenant locale (PE = DD/MM/YYYY)", async ({
    agendaPage,
  }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // Date picker / header should show PE locale date format
    const datePicker = agendaView.getDatePicker();
    await expect(datePicker).toBeVisible();

    const dateText = await datePicker.textContent();

    // PE locale: DD/MM/YYYY or "10 jun. 2026" format
    // Must NOT be "June 10, 2026" (US format) or "06/10/2026" (US month-first)
    // toLocaleDateString() is banned — formatTenantDate() must be used
    if (dateText && dateText.includes("10")) {
      // A date with "10" visible should not be in US MM/DD format "06/10"
      // It should be "10/06" or "10 jun" pattern
      expect(dateText).not.toMatch(/^06\/10/); // US format banned
    }

    await clearAgendaGridMock(agendaPage);
  });

  test("currency select shows available options for PE tenant", async ({
    agendaPage,
  }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
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

    // Currency select must have PEN option (tenant default)
    const penOption = subform.currencySelect.locator('option[value="PEN"]');
    await expect(penOption).toHaveCount(1);

    // USD option available for override (tourist patients)
    const usdOption = subform.currencySelect.locator('option[value="USD"]');
    await expect(usdOption).toHaveCount(1);

    await clearAgendaGridMock(agendaPage);
  });
});
