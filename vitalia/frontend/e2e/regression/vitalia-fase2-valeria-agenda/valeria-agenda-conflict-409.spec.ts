/**
 * valeria-agenda-conflict-409.spec.ts — SC-5 409 optimistic lock conflict
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   SC-5 "FE handles 409 conflict gracefully — banner + auto-collapse + query invalidate"
 *
 * Scenario coverage (04-validators.yaml):
 *   test_409_conflict_graceful_banner
 *
 * Project: smoke
 * Depends on: AgendaViewPage + AppointmentDrawerPage + CobrarSaldoSubformPage POMs
 *
 * Note: 409 Conflict is triggered by the BE optimistic lock (`balance_version` mismatch
 * via `SELECT ... FOR UPDATE`). This spec mocks the POST /api/v1/payments/charge endpoint
 * to return 409 and asserts the FE handles it gracefully:
 *   - Shows conflict banner (not a generic error)
 *   - Auto-invalidates React Query to fetch fresh data
 *   - Subform collapses (dirty state cleared)
 *   - Slot status unchanged until refresh confirms
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-conflict-409.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec F2-S1
 */

import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "./fixtures/valeria-agenda.fixture";
import { setupAgendaGridMock, clearAgendaGridMock } from "./fixtures/__mocks__/agenda-grid";
import {
  setupPaymentAdapterMock,
} from "./fixtures/mock-payment-adapter";
import { AgendaViewPage } from "./poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "./poms/appointment-drawer-page.pom";
import { CobrarSaldoSubformPage } from "./poms/cobrar-saldo-subform-page.pom";

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

// ── SC-5: 409 Conflict — graceful banner + auto-collapse ──────────────────

test.describe("SC-5 — 409 conflict shows graceful banner + auto-collapse", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await setupPaymentAdapterMock(agendaPage, "payment_409_conflict");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("409 conflict shows conflict banner (not generic error)", async ({
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

    // Submit — will return 409
    await subform.fillForm({ method: "tarjeta" });
    await subform.submit();

    // Conflict banner visible (specific to balance_version mismatch)
    const conflictBanner = subform.conflictBanner;
    await expect(conflictBanner).toBeVisible({ timeout: 8_000 });

    // Conflict message in Spanish neutro
    const conflictText = await subform.getConflictMessage();
    expect(conflictText).toMatch(/actualizado|actualizar|recarga|versión/i);
    expect(conflictText).not.toMatch(/\bpodés\b/i); // no voseo

    // Generic error alert must NOT be shown (different from 503)
    await expect(subform.errorAlert).not.toBeVisible();
  });

  test("409 conflict does NOT show success toast", async ({ agendaPage }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();
    await subform.waitForVisible();
    await subform.fillForm({ method: "efectivo" });
    await subform.submit();

    // Wait for conflict response to arrive
    await expect(subform.conflictBanner).toBeVisible({ timeout: 8_000 });

    // No success toast should appear
    await expect(subform.successToast).not.toBeVisible();
  });

  test("409 conflict slot border stays unchanged (not paid)", async ({
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
    await subform.fillForm({ method: "tarjeta" });
    await subform.submit();

    // Wait for conflict banner
    await expect(subform.conflictBanner).toBeVisible({ timeout: 8_000 });

    // Slot payment status must remain "deposit" (not "paid")
    const slot = agendaView.getSlot(sampleSlot.appointmentId);
    await expect(slot).toHaveAttribute("data-payment-status", "deposit");
  });

  test("409 conflict auto-collapses subform after brief delay", async ({
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
    await subform.fillForm({ method: "tarjeta" });
    await subform.submit();

    // After 409, subform should auto-collapse (React Query invalidates + refetches)
    // The conflict banner appears then the drawer refreshes with new data
    await expect(subform.conflictBanner).toBeVisible({ timeout: 8_000 });

    // Subform collapses after auto-invalidation and fresh fetch
    await subform.waitForCollapsed();
  });

  test("409 conflict auto-invalidates React Query (drawer refreshes)", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    const subform = new CobrarSaldoSubformPage(agendaPage);

    // Mock the appointment detail endpoint to return updated version after 409
    await agendaPage.route(
      `**/api/v1/scheduling/appointments/${sampleSlot.appointmentId}`,
      (route) => {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            appointmentId: sampleSlot.appointmentId,
            paymentStatus: "paid",
            totalAmount: 150,
            depositAmount: 70,
            balanceAmount: 0,
            balanceVersion: 2,
            updatedAt: new Date().toISOString(),
          }),
        }).catch(() => undefined);
      },
    );

    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();
    await drawer.expandSection("pago");
    await drawer.clickCobrarSaldo();
    await subform.waitForVisible();
    await subform.fillForm({ method: "tarjeta" });
    await subform.submit();

    // 409 triggers — conflict banner shown
    await expect(subform.conflictBanner).toBeVisible({ timeout: 8_000 });

    // After auto-invalidation, drawer refreshes with new payment status
    const paymentStatus = await drawer.getPaymentStatus();
    // After refresh, status should reflect the BE state (paid in our mock)
    expect(paymentStatus.toLowerCase()).toMatch(/pagado|paid|cobrado/);
  });
});
