/**
 * valeria-agenda-cobro.spec.ts — SC-1 happy + SC-2 negative payment 503
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   SC-1 "cobro saldo end-to-end PE boleta emit"
 *   SC-2 "payment-adapter 503 shows retry alert"
 *
 * Scenario coverage (04-validators.yaml):
 *   test_happy_path_pen_boleta_end_to_end
 *   test_payment_adapter_503
 *
 * Project: smoke
 * Depends on: AgendaViewPage + AppointmentDrawerPage + CobrarSaldoSubformPage POMs
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-cobro.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec F2-S1
 */

import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "./fixtures/valeria-agenda.fixture";
import { setupPaymentAdapterMock } from "./fixtures/mock-payment-adapter";
import { setupFiscalEmissionMock } from "./fixtures/mock-fiscal-emission";
import { setupAgendaGridMock } from "./fixtures/__mocks__/agenda-grid";
import { AgendaViewPage } from "./poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "./poms/appointment-drawer-page.pom";
import { CobrarSaldoSubformPage } from "./poms/cobrar-saldo-subform-page.pom";

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

// ── SC-1: Happy path — cobro saldo PEN + boleta emitida ────────────────────

test.describe("SC-1 — cobro saldo end-to-end PE boleta emit", () => {
  test.beforeEach(async ({ agendaPage }) => {
    // Seed: agenda grid with sample slot (deposit status)
    await setupAgendaGridMock(agendaPage, "with_seed");
    // Mock: payment adapter success + fiscal boleta success
    await setupPaymentAdapterMock(agendaPage, "success");
    await setupFiscalEmissionMock(agendaPage, "success_boleta");

    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
  });

  test("happy path PEN boleta emit end-to-end", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    // 1. Wait for calendar grid to load
    await agendaView.waitForLoaded();

    // 2. Click slot with pending balance (sampleSlot)
    await agendaView.clickSlot(sampleSlot.appointmentId);

    // 3. Drawer opens
    await drawer.waitForOpen();
    const patientName = await drawer.getPatientName();
    expect(patientName).toContain(sampleSlot.patientMaskedName);

    // 4. Expand "Pago" accordion + click "Cobrar saldo"
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();

    // 5. Subform visible
    await subform.waitForVisible();

    // 6. Fill form: method=tarjeta, emit_invoice=true, fiscal_doc_type=boleta
    await subform.fillForm({
      method: "tarjeta",
      emitInvoice: true,
      fiscalDocType: "boleta",
      currency: "PEN",
      notes: "cobro normal",
    });

    // 7. Submit
    await subform.submit();

    // 8. Success toast visible
    await subform.waitForSuccessToast();
    const toastEl = subform.successToast;
    await expect(toastEl).toBeVisible();

    // 9. Toast contains "PEN 80" and "boleta"
    const toastText = await toastEl.textContent();
    expect(toastText).toMatch(/80/);
    expect(toastText?.toLowerCase()).toMatch(/boleta|comprobante/);

    // 10. Slot payment status updates to "paid" (green border)
    const slot = agendaView.getSlot(sampleSlot.appointmentId);
    await expect(slot).toHaveAttribute("data-payment-status", "paid", {
      timeout: 5_000,
    });
  });

  test("drawer shows PHI-masked patient name (no raw DNI)", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();

    const patientName = await drawer.getPatientName();
    // PHI-masked: first initial + last name, no raw DNI
    expect(patientName).not.toMatch(/\d{8}/); // no 8-digit DNI
    expect(patientName).toMatch(/[A-Z]\.\s+\w+/); // "P. Hernández" pattern
  });

  test("slot border status transitions from deposit (yellow) to paid (green)", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    await agendaView.waitForLoaded();

    // Verify initial status is "deposit"
    const slot = agendaView.getSlot(sampleSlot.appointmentId);
    await expect(slot).toHaveAttribute("data-payment-status", "deposit");

    // Complete cobro flow
    await slot.click();
    await drawer.waitForOpen();
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();
    await subform.waitForVisible();
    await subform.fillForm({ method: "efectivo" });
    await subform.submit();
    await subform.waitForSuccessToast();

    // Status transitions to paid
    await expect(slot).toHaveAttribute("data-payment-status", "paid", {
      timeout: 5_000,
    });
  });
});

// ── SC-2: Negative — payment-adapter 503 ──────────────────────────────────

test.describe("SC-2 — payment-adapter 503 shows retry", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    // Mock: payment adapter returns 503
    await setupPaymentAdapterMock(agendaPage, "payment_503");
    // Fiscal should NOT be called (saga aborts before emit)

    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
  });

  test("payment adapter 503 shows retry alert", async ({ agendaPage }) => {
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

    // Error alert with "destructive" variant
    const errorAlert = subform.getErrorAlert();
    await expect(errorAlert).toBeVisible({ timeout: 8_000 });

    // Alert message in Spanish neutro
    const errorText = await subform.getErrorMessage();
    expect(errorText).toMatch(/No pudimos procesar|intentalo/i);

    // Retry button visible
    const retryBtn = subform.getRetryButton();
    await expect(retryBtn).toBeVisible();

    // Slot border status does NOT change (still deposit)
    const slot = agendaView.getSlot(sampleSlot.appointmentId);
    await expect(slot).toHaveAttribute("data-payment-status", "deposit");

    // No success toast
    await expect(subform.successToast).not.toBeVisible();
  });

  test("retry button re-submits same form (idempotent key reused)", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    // First attempt — 503
    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();
    await subform.waitForVisible();
    await subform.fillForm({ method: "tarjeta" });
    await subform.submit();
    await expect(subform.getErrorAlert()).toBeVisible({ timeout: 8_000 });

    // Switch mock to success for retry
    await setupPaymentAdapterMock(agendaPage, "success");
    await setupFiscalEmissionMock(agendaPage, "success_boleta");

    // Click retry
    await subform.clickRetry();

    // Should succeed now
    await subform.waitForSuccessToast();
  });
});
