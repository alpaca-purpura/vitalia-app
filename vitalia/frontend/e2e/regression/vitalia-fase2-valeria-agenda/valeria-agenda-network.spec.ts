/**
 * valeria-agenda-network.spec.ts — SC-7 grid timeout + retries
 *
 * F2-S1 vitalia-fase2-valeria-agenda — T-17
 * Gherkin:
 *   SC-7 "grid timeout 3 retries then EmptyState error + manual retry"
 *
 * Scenario coverage (04-validators.yaml):
 *   test_grid_3_retries_then_empty_state_error
 *
 * Project: smoke
 * Depends on: AgendaViewPage POM + network-failure fixture
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase2-valeria-agenda/valeria-agenda-network.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec F2-S1
 */

import { expect } from "@playwright/test";
import { test, VALERIA_AGENDA_FIXTURE, gotoAgenda } from "./fixtures/valeria-agenda.fixture";
import {
  setupGridNetworkFailure,
  setupTransientNetworkFailure,
  clearNetworkFailure,
} from "./fixtures/network-failure";
import { setupAgendaGridMock } from "./fixtures/__mocks__/agenda-grid";
import { AgendaViewPage } from "./poms/agenda-view-page.pom";

const { tenantId } = VALERIA_AGENDA_FIXTURE;

// ── SC-7: Grid timeout — 3 retries → EmptyState error + manual retry ──────

test.describe("SC-7 — grid timeout retries then error empty state", () => {
  test("3 retries then shows EmptyState with error variant + Reintentar button", async ({
    agendaPage,
  }) => {
    // Abort ALL grid requests → React Query will exhaust retries
    await setupGridNetworkFailure(agendaPage);

    // Navigate — grid will fail immediately
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);

    // Wait for skeleton to disappear and error state to appear
    // React Query retryDelay is exponential — max 3 retries = ~7s total
    await agendaPage.waitForSelector(
      '[data-testid="agenda-empty-state"]',
      { timeout: 20_000 },
    );

    const emptyState = agendaView.getEmptyState();
    await expect(emptyState).toBeVisible();

    // EmptyState shows error variant (not empty-data variant)
    await expect(emptyState).toHaveAttribute("data-variant", "error");

    // "Reintentar" manual retry button visible
    const retryBtn = agendaView.getRetryButton();
    await expect(retryBtn).toBeVisible();

    await clearNetworkFailure(agendaPage);
  });

  test("manual retry recovers from network error", async ({ agendaPage }) => {
    // First: fail grid
    await setupGridNetworkFailure(agendaPage);
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);

    // Wait for error empty state
    await agendaPage.waitForSelector('[data-testid="agenda-empty-state"]', {
      timeout: 20_000,
    });

    // Clear the network failure and register success mock
    await clearNetworkFailure(agendaPage);
    await setupAgendaGridMock(agendaPage, "with_seed");

    // Click manual retry
    await agendaView.getRetryButton().click();

    // Grid should load successfully now
    await agendaView.waitForLoaded();

    // Calendar grid visible
    await expect(agendaView.calendarGrid).toBeVisible({ timeout: 10_000 });
  });

  test("transient network failure — recovers before max retries", async ({
    agendaPage,
  }) => {
    // Fail first 2 requests, then succeed on 3rd
    await setupTransientNetworkFailure(agendaPage, 2);
    await setupAgendaGridMock(agendaPage, "with_seed");

    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    const agendaView = new AgendaViewPage(agendaPage, tenantId);

    // Should eventually load (React Query retries transparently)
    await agendaView.waitForLoaded();

    // Grid loaded — not error state
    await expect(agendaView.calendarGrid).toBeVisible({ timeout: 15_000 });
    await expect(agendaView.emptyState).not.toBeVisible();

    await clearNetworkFailure(agendaPage);
  });

  test("network error does not leak PHI in URL", async ({ agendaPage }) => {
    await setupGridNetworkFailure(agendaPage);
    await gotoAgenda(agendaPage, tenantId, { view: "semana" });

    // Wait for error state
    await agendaPage.waitForSelector('[data-testid="agenda-empty-state"]', {
      timeout: 20_000,
    });

    // URL must NOT contain any PHI-like patterns (8-digit DNI)
    const url = agendaPage.url();
    expect(url).not.toMatch(/\d{8}/);
    // No raw patient names in URL
    expect(url).not.toMatch(/patient[_=-]/i);
    expect(url).not.toMatch(/dni[_=-]/i);

    await clearNetworkFailure(agendaPage);
  });
});
