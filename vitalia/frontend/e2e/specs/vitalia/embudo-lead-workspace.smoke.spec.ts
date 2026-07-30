// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * embudo-lead-workspace.spec.ts — Integration E2E for Lead Workspace.
 *
 * vitalia-fase2-adrian-embudo — T-E2E-1
 *
 * Scenarios covered:
 *   SC-detalle / F-6   click lead → /resumen URL + EntitySubNavBar + blocks
 *   SC-deeplink        refresh /historial → renders
 *   RN-2               PHI firewall — historial no renders datos clínicos
 *   RN-16              leadId = UUID (no PHI in URL)
 *   RN-19              /nuevo slug precedes [leadId] (routing guard)
 *
 * All specs import from base.ts (anti-burbuja gate).
 * API calls intercepted via page.route().
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/specs/vitalia/embudo-lead-workspace.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec
 * spec_anchor: 04-validators.yaml § SC-detalle / SC-deeplink
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/authed-runtime";
import { EmbudoBoardPage } from "../../pages/EmbudoBoardPage";
import { LeadWorkspacePage } from "../../pages/LeadWorkspacePage";

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";
const BASE_URL_API = "**"; // origin-agnostic: el FE pega a /api via proxy :3002, no directo a :8002
const LEAD_ID = "lead-001";

// ── Mock helpers ──────────────────────────────────────────────────────────────

async function mockLeadDetail(page: import("@playwright/test").Page) {
  await page.route(
    `${BASE_URL_API}/api/v1/crm/leads/${LEAD_ID}/detail`,
    (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          lead: {
            id: LEAD_ID,
            tenantId: TENANT_ID,
            name: "María G███",
            stage: "interesado",
            stageEnteredAt: "2026-06-01T10:00:00Z",
            score: 48,
            temperature: "warm",
            operatedBy: "agent",
            channel: "whatsapp",
            estimatedValue: 7000,
            currency: "PEN",
            buyingSignals: ["pregunto_precio"],
            isFrozen: false,
            frozenReason: null,
            depositStatus: null,
            closureReason: null,
            reactivationCohortAt: null,
            serviceInterest: "Ortodoncia",
            assignedDoctorId: null,
            version: 1,
            isBlacklisted: false,
            lastActivityDescription: "Adrián saludó",
            lastActivityAt: "2026-06-03T10:00:00Z",
          },
          scoreBreakdown: [
            { label: "Preguntó precio", delta: 25, icon: null },
            { label: "Respondió rápido", delta: 15, icon: null },
            { label: "Sin agendar 2d", delta: -2, icon: null },
          ],
          autonomy: {
            canDo: ["mover etapa", "agendar", "enviar info"],
            needsApproval: ["cobrar", "descuentos", "clínico"],
            currentMode: "autonomous",
          },
        }),
      });
    },
  );
}

async function mockLeadTransitions(page: import("@playwright/test").Page) {
  await page.route(
    `${BASE_URL_API}/api/v1/crm/leads/${LEAD_ID}/transitions`,
    (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          events: [
            {
              id: "ev-001",
              kind: "stage_move",
              actor: "agent",
              descriptionEs: "Adrián movió a interesado",
              occurredAt: "2026-06-01T10:00:00Z",
            },
            {
              id: "ev-002",
              kind: "message",
              actor: "lead",
              descriptionEs: "Preguntó por el precio del tratamiento",
              occurredAt: "2026-06-02T10:00:00Z",
            },
          ],
        }),
      });
    },
  );
}

async function mockBoardForClick(page: import("@playwright/test").Page) {
  await page.route(`${BASE_URL_API}/api/v1/crm/board**`, (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        columns: [
          {
            stage: "interesado",
            label: "Interesado",
            count: 1,
            sumValue: 7000,
            currency: "PEN",
            overSlaCount: 0,
            leads: [
              {
                id: LEAD_ID,
                tenantId: TENANT_ID,
                name: "María G███",
                stage: "interesado",
                stageEnteredAt: "2026-06-01T10:00:00Z",
                score: 48,
                temperature: "warm",
                operatedBy: "agent",
                channel: "whatsapp",
                estimatedValue: 7000,
                currency: "PEN",
                buyingSignals: ["pregunto_precio"],
                isFrozen: false,
                frozenReason: null,
                depositStatus: null,
                closureReason: null,
                reactivationCohortAt: null,
                serviceInterest: "Ortodoncia",
                assignedDoctorId: null,
                version: 1,
                isBlacklisted: false,
                lastActivityDescription: "Adrián saludó",
                lastActivityAt: "2026-06-03T10:00:00Z",
              },
            ],
          },
          { stage: "calificando", label: "Calificando", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
          { stage: "consulta_agendada", label: "Consulta agendada", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
          { stage: "plan_presentado", label: "Plan presentado", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
          { stage: "reservado", label: "Reservado", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
        ],
        kpis: { totalActive: 1, adrianCount: 1, humanCount: 0, hotCount: 0, warmCount: 1, coldCount: 0, avgScore: 48, depositRate: 0, frozenCount: 0 },
      }),
    });
  });
}

// ── Tests ──────────────────────────────────────────────────────────────────────

test.describe("Lead workspace — SC-detalle deep-link + EntitySubNavBar", () => {
  test("@rule-addressable F-6 navigate to /resumen from board click → URL + EntitySubNavBar", async ({
    page,
  }) => {
    await mockBoardForClick(page);
    await mockLeadDetail(page);
    await mockLeadTransitions(page);

    const board = new EmbudoBoardPage(page, TENANT_ID);
    const workspace = new LeadWorkspacePage(page, TENANT_ID, LEAD_ID);

    await board.goto();
    await board.waitForLoaded();

    // Click the lead card
    await board.clickLeadCard(LEAD_ID);

    // Wait for navigation to /resumen
    await expect(page).toHaveURL(
      new RegExp(`/adrian/embudo/${LEAD_ID}/resumen`),
      { timeout: 10_000 },
    );

    // EntitySubNavBar visible
    await workspace.expectEntitySubNavBarVisible();
  });

  test("@rule-addressable F-6 deep-link /resumen → renders Datos + Score blocks", async ({
    page,
  }) => {
    await mockLeadDetail(page);
    await mockLeadTransitions(page);

    const workspace = new LeadWorkspacePage(page, TENANT_ID, LEAD_ID);
    await workspace.gotoResumen();
    await workspace.waitForResumenLoaded();

    // Both main blocks visible
    await workspace.expectDatosBlockVisible();
    await workspace.expectScoreDonutVisible();
    // Score has numeric value visible (not just color — a11y RN-2)
    await workspace.expectScoreNumberVisible();
  });

  test("@rule-phi-firewall RN-2 historial NO renders clinical data", async ({
    page,
  }) => {
    await mockLeadDetail(page);
    await mockLeadTransitions(page);

    const workspace = new LeadWorkspacePage(page, TENANT_ID, LEAD_ID);
    await workspace.gotoHistorial();
    await workspace.waitForHistorialLoaded();

    await workspace.expectNoPhiDataInHistorial();
  });

  test("SC-deeplink refresh /historial → renders", async ({ page }) => {
    await mockLeadDetail(page);
    await mockLeadTransitions(page);

    const workspace = new LeadWorkspacePage(page, TENANT_ID, LEAD_ID);

    // Direct navigation to /historial (deep-link / hard refresh)
    await workspace.gotoHistorial();
    await workspace.waitForHistorialLoaded();

    // EntitySubNavBar with tabs visible
    await workspace.expectEntitySubNavBarVisible();
    await workspace.expectHistorialView();
  });

  test("@rule-addressable RN-16 leadId not PHI in URL", async ({ page }) => {
    await mockLeadDetail(page);
    await mockLeadTransitions(page);

    const workspace = new LeadWorkspacePage(page, TENANT_ID, LEAD_ID);
    await workspace.gotoResumen();

    await workspace.expectNoPhiInUrl();
  });

  test("tabs: click Historial → /historial URL; click Resumen → /resumen URL", async ({
    page,
  }) => {
    await mockLeadDetail(page);
    await mockLeadTransitions(page);

    const workspace = new LeadWorkspacePage(page, TENANT_ID, LEAD_ID);
    await workspace.gotoResumen();
    await workspace.waitForResumenLoaded();

    // Switch to Historial
    await workspace.clickHistorialTab();
    await expect(page).toHaveURL(
      new RegExp(`/${LEAD_ID}/historial`),
    );

    // Switch back to Resumen
    await workspace.clickResumenTab();
    await expect(page).toHaveURL(
      new RegExp(`/${LEAD_ID}/resumen`),
    );
  });

  test("EntitySubNavBar tabs have tablist role (SC-10 a11y)", async ({
    page,
  }) => {
    await mockLeadDetail(page);
    await mockLeadTransitions(page);

    const workspace = new LeadWorkspacePage(page, TENANT_ID, LEAD_ID);
    await workspace.gotoResumen();
    await workspace.waitForResumenLoaded();

    await workspace.expectTablistRole();
  });
});
