/**
 * valeria-agenda-tenant-switch.spec.ts — SC-3 tenant switch invalidate
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   SC-3 "tenant switch invalidates drawer + cache clear"
 *
 * Scenario coverage (04-validators.yaml):
 *   test_tenant_switch_invalidates_drawer
 *
 * Project: smoke
 * Depends on: AgendaViewPage + AppointmentDrawerPage POMs
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-tenant-switch.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec F2-S1
 */

import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "./fixtures/valeria-agenda.fixture";
import { setupAgendaGridMock, clearAgendaGridMock } from "./fixtures/__mocks__/agenda-grid";
import { AgendaViewPage } from "./poms/agenda-view-page.pom";
import { AppointmentDrawerPage } from "./poms/appointment-drawer-page.pom";

const { tenantId, sampleSlot } = VALERIA_AGENDA_FIXTURE;
const TENANT_B_ID = "clinica-esperanza-ar-test";

// ── SC-3: Tenant switch invalidates drawer + cache ─────────────────────────

test.describe("SC-3 — tenant switch invalidates drawer + cache", () => {
  test.beforeEach(async ({ agendaPage }) => {
    await setupAgendaGridMock(agendaPage, "with_seed");
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });
  });

  test.afterEach(async ({ agendaPage }) => {
    await clearAgendaGridMock(agendaPage);
  });

  test("tenant switch closes drawer and fetches new tenant agenda", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    const drawer = new AppointmentDrawerPage(agendaPage);

    // 1. Open appointment drawer
    await agendaView.waitForLoaded();
    await agendaView.clickSlot(sampleSlot.appointmentId);
    await drawer.waitForOpen();

    // 2. Confirm drawer is open
    await expect(drawer.panel).toBeVisible();

    // 3. Switch to tenant B
    await setupAgendaGridMock(agendaPage, "tenant_b");
    // UPDATED: paradigm-map-zones T-6 — route migrated to mateo/agenda
    await agendaPage.goto(`/${TENANT_B_ID}/mateo/agenda?view=semana`);
    await agendaPage.waitForLoadState("domcontentloaded");

    // 4. Drawer must be closed after navigation (Zustand reset on tenant switch)
    await expect(drawer.panel).not.toBeVisible({ timeout: 5_000 });

    // 5. Agenda fetched for tenant B
    const agendaViewB = new AgendaViewPage(agendaPage, TENANT_B_ID);
    await agendaViewB.waitForLoaded();

    // 6. Slot from tenant A NOT visible in tenant B calendar
    const tenantASlot = agendaView.getSlot(sampleSlot.appointmentId);
    await expect(tenantASlot).not.toBeVisible({ timeout: 3_000 });
  });

  test("localStorage agenda state updated on tenant switch", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // Capture initial localStorage state
    const initialKey = await agendaPage.evaluate(() =>
      localStorage.getItem("valeria-agenda-tenant"),
    );
    expect(initialKey).toBeTruthy();

    // Switch tenant
    await setupAgendaGridMock(agendaPage, "tenant_b");
    // UPDATED: paradigm-map-zones T-6 — route migrated to mateo/agenda
    await agendaPage.goto(`/${TENANT_B_ID}/mateo/agenda`);
    await agendaPage.waitForLoadState("domcontentloaded");

    // localStorage updated to tenant B
    const updatedKey = await agendaPage.evaluate(() =>
      localStorage.getItem("valeria-agenda-tenant"),
    );
    // Key should differ from tenant A OR reflect new tenant context
    expect(updatedKey).not.toBe(initialKey);
  });

  test("React Query cache cleared on tenant switch (no stale tenant A data)", async ({
    agendaPage,
  }) => {
    const agendaView = new AgendaViewPage(agendaPage, tenantId);
    await agendaView.waitForLoaded();

    // Open drawer with tenant A appointment
    await agendaView.clickSlot(sampleSlot.appointmentId);
    const drawer = new AppointmentDrawerPage(agendaPage);
    await drawer.waitForOpen();

    // Switch tenant while drawer is open
    await setupAgendaGridMock(agendaPage, "tenant_b");
    await agendaPage.evaluate((newTenantId: string) => {
      // Simulate tenant switch via Clerk / app navigation
      // UPDATED: paradigm-map-zones T-6 — route migrated to mateo/agenda
      window.location.href = `/${newTenantId}/mateo/agenda`;
    }, TENANT_B_ID);
    await agendaPage.waitForLoadState("domcontentloaded");

    // Tenant A appointment data MUST NOT appear in the grid
    const agendaViewB = new AgendaViewPage(agendaPage, TENANT_B_ID);
    await agendaViewB.waitForLoaded();

    const tenantASlotPatient = agendaPage.locator(
      `text=${sampleSlot.patientMaskedName}`,
    );
    await expect(tenantASlotPatient).not.toBeVisible({ timeout: 3_000 });
  });
});
