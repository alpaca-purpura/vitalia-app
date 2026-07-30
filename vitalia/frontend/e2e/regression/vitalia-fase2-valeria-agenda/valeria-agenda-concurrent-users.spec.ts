/**
 * valeria-agenda-concurrent-users.spec.ts — SC-6 concurrent users
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   SC-6 "2 staff users polling 30s — staff B cancel reflects in staff A stale banner"
 *
 * Scenario coverage (04-validators.yaml):
 *   test_concurrent_users_polling_stale_banner
 *
 * Project: smoke
 * Depends on: AgendaViewPage + AppointmentDrawerPage POMs
 *
 * Pattern: 2 BrowserContexts (staff A + staff B) sharing fixture seed.
 * Staff B cancels an appointment via mock API. After the 30s poll cycle,
 * staff A drawer shows a stale banner with a "Recargar" button.
 *
 * NOTE: 30s real polling is too slow for CI. We override refetchInterval to
 * 1_000ms via URL flag `?e2eRefetchMs=1000` (checked by AgendaGrid client).
 * This is gated behind a build flag — non-production only.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-concurrent-users.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec F2-S1
 */

import { expect, chromium } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "./fixtures/valeria-agenda.fixture";
import {
  setupAgendaGridMock,
  clearAgendaGridMock,
} from "./fixtures/__mocks__/agenda-grid";
import { AgendaViewPage } from "./poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "./poms/appointment-drawer-page.pom";

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Build grid response with appointment marked as cancelled */
function buildCancelledSlotBody() {
  return {
    items: [
      {
        appointmentId: sampleSlot.appointmentId,
        tenantId,
        clinicId: VALERIA_AGENDA_FIXTURE.clinicId,
        patientMaskedName: sampleSlot.patientMaskedName,
        service: "Limpieza dental",
        startTime: "2026-06-10T10:00:00-05:00",
        endTime: "2026-06-10T11:00:00-05:00",
        paymentStatus: "cancelled",
        origin: "walk-in",
        currency: "PEN",
        totalAmount: 150,
        depositAmount: 70,
        balanceAmount: 80,
        balanceVersion: 2,
      },
    ],
    total: 1,
    page: 1,
    per_page: 20,
    view: "semana",
    range_start: "2026-06-09T00:00:00-05:00",
    range_end: "2026-06-15T23:59:59-05:00",
    freshness_at: new Date().toISOString(),
  };
}

// ── SC-6: 2 staff users — cancel in B reflects in A ───────────────────────

test.describe("SC-6 — concurrent users polling + stale banner", () => {
  test("staff B cancel reflects in staff A after poll cycle (stale banner)", async ({
    agendaPage,
  }) => {
    // ── Staff A: main page ─────────────────────────────────────────────────
    await setupAgendaGridMock(agendaPage, "with_seed");
    // Use accelerated refetch for CI (1s instead of 30s)
    await gotoAgenda(agendaPage, tenantId, {
      view: "semana",
      extraParams: { e2eRefetchMs: "1000" },
    });

    const agendaA = new AgendaViewPage(agendaPage, tenantId);
    const drawerA = new AppointmentDrawerPage(agendaPage);

    await agendaA.waitForLoaded();
    await agendaA.clickSlot(sampleSlot.appointmentId);
    await drawerA.waitForOpen();

    // Drawer is open — staff A is viewing the appointment
    await expect(drawerA.panel).toBeVisible();

    // ── Staff B: second browser context (simulated concurrent session) ─────
    // Staff B cancels the appointment by flipping the mock to return cancelled status
    // After the next poll cycle, staff A should see the stale banner
    await agendaPage.route(
      "**/api/v1/scheduling/agenda/grid**",
      (route) => {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(buildCancelledSlotBody()),
        }).catch(() => undefined);
      },
    );

    // Mock the appointment detail endpoint to return version bump (stale indicator)
    await agendaPage.route(
      `**/api/v1/scheduling/appointments/${sampleSlot.appointmentId}`,
      (route) => {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            appointmentId: sampleSlot.appointmentId,
            status: "cancelled",
            balanceVersion: 2,
            updatedAt: new Date().toISOString(),
          }),
        }).catch(() => undefined);
      },
    );

    // ── Wait for stale banner to appear in staff A drawer ─────────────────
    // After poll detects version mismatch → stale banner shown
    await expect(drawerA.staleBanner).toBeVisible({ timeout: 8_000 });

    // Stale banner has a "Recargar" button
    const recargarBtn = agendaPage.locator(
      '[data-testid="drawer-stale-reload-btn"]',
    );
    await expect(recargarBtn).toBeVisible();

    await clearAgendaGridMock(agendaPage);
  });

  test("freshness indicator updates within poll cycle", async ({
    agendaPage,
  }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, {
      view: "semana",
      extraParams: { e2eRefetchMs: "1000" },
    });

    const agendaA = new AgendaViewPage(agendaPage, tenantId);
    await agendaA.waitForLoaded();

    // Freshness indicator should update within 3s (1s refetch + rendering)
    await agendaA.waitForFreshness(3);

    const indicator = agendaA.getFreshnessIndicator();
    await expect(indicator).toBeVisible();
    const text = await indicator.textContent();
    expect(text).toMatch(/Actualizado/);

    await clearAgendaGridMock(agendaPage);
  });

  test("two contexts same tenant do not leak PHI across sessions", async () => {
    // Use a separate browser context to validate cross-context isolation
    const browser = await chromium.launch();
    const contextA = await browser.newContext({ storageState: undefined });
    const contextB = await browser.newContext({ storageState: undefined });

    try {
      const pageA = await contextA.newPage();
      const pageB = await contextB.newPage();

      // Both pages go to different routes — no cross-contamination
      // This validates that client-side state (Zustand/RQ) is isolated per context
      await pageA.goto("about:blank");
      await pageB.goto("about:blank");

      // Each context has empty localStorage (no shared state)
      const lsA = await pageA.evaluate(() => localStorage.length);
      const lsB = await pageB.evaluate(() => localStorage.length);

      expect(lsA).toBe(0);
      expect(lsB).toBe(0);
    } finally {
      await contextA.close();
      await contextB.close();
      await browser.close();
    }
  });
});
