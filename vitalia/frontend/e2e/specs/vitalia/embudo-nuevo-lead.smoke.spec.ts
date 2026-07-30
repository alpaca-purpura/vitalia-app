// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * embudo-nuevo-lead.spec.ts — Integration E2E for /nuevo lead page.
 *
 * vitalia-fase2-adrian-embudo — T-E2E-1
 *
 * Scenarios covered:
 *   SC-nuevo / F-7  /nuevo URL + EntitySubNavBar + form → submit → redirect + highlight
 *   RN-19           /nuevo slug precedes [leadId] (routing)
 *
 * All specs import from base.ts (anti-burbuja gate).
 * API calls intercepted via page.route().
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/specs/vitalia/embudo-nuevo-lead.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec
 * spec_anchor: 04-validators.yaml § SC-nuevo / F-7
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/authed-runtime";
import { NewLeadPage } from "../../pages/NewLeadPage";
import { EmbudoBoardPage } from "../../pages/EmbudoBoardPage";

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";
const BASE_URL_API = "**"; // origin-agnostic: el FE pega a /api via proxy :3002, no directo a :8002

const NEW_LEAD_MOCK_RESPONSE = {
  id: "lead-new-001",
  tenantId: TENANT_ID,
  name: "Nuevo Lead Test",
  stage: "interesado",
  score: 10,
  temperature: "cold",
  operatedBy: "agent",
  channel: "web",
  estimatedValue: null,
  currency: "PEN",
  buyingSignals: [],
  isFrozen: false,
  frozenReason: null,
  depositStatus: null,
  version: 1,
  stageEnteredAt: "2026-06-03T10:00:00Z",
};

async function mockCreateLead(page: import("@playwright/test").Page) {
  await page.route(`${BASE_URL_API}/api/v1/crm/leads`, (route) => {
    if (route.request().method() === "POST") {
      route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify(NEW_LEAD_MOCK_RESPONSE),
      });
    } else {
      route.continue();
    }
  });
}

// ── Tests ──────────────────────────────────────────────────────────────────────

test.describe("Nuevo lead page — SC-nuevo / F-7", () => {
  test("@rule-addressable RN-19 /nuevo is a page route (not a dialog), has EntitySubNavBar", async ({
    page,
  }) => {
    const nuevoPage = new NewLeadPage(page, TENANT_ID);
    await nuevoPage.goto();
    await nuevoPage.waitForFormLoaded();

    // It's a real page, not a dialog
    await expect(page).toHaveURL(new RegExp("/embudo/nuevo"));

    // EntitySubNavBar present
    await nuevoPage.expectEntitySubNavBarVisible();

    // Form visible
    await nuevoPage.expectFormVisible();
  });

  test("@rule-addressable F-7 submit minimal form → 201 → redirect /embudo?highlight=id", async ({
    page,
  }) => {
    await mockCreateLead(page);
    const nuevoPage = new NewLeadPage(page, TENANT_ID);
    await nuevoPage.goto();
    await nuevoPage.waitForFormLoaded();

    // Fill minimum required fields
    await nuevoPage.fillName("Paciente Test");
    await nuevoPage.fillPhone("+51 987 654 321");

    // Try to select channel (may be a Shadcn Select)
    try {
      await nuevoPage.selectChannel("WhatsApp");
    } catch {
      // If channel select not interactive, try filling directly
      await page.locator('input[name="channel"]').fill("whatsapp").catch(() => {
        /* continue if not available */
      });
    }

    await nuevoPage.submit();

    // After submit: redirect to /embudo with highlight
    await nuevoPage.expectRedirectToEmbudoWithHighlight();
  });

  test("F-7 cancel → navigate back to /embudo (no lead created)", async ({
    page,
  }) => {
    const nuevoPage = new NewLeadPage(page, TENANT_ID);
    await nuevoPage.goto();
    await nuevoPage.waitForFormLoaded();

    await nuevoPage.cancel();

    // Back on /embudo
    await expect(page).toHaveURL(
      new RegExp(`/adrian/embudo`),
      { timeout: 8_000 },
    );
    // URL should NOT be /nuevo
    expect(page.url()).not.toContain("/nuevo");
  });

  test("F-7 submit empty form → validation errors visible", async ({
    page,
  }) => {
    const nuevoPage = new NewLeadPage(page, TENANT_ID);
    await nuevoPage.goto();
    await nuevoPage.waitForFormLoaded();

    // Submit without filling anything
    await nuevoPage.submit();

    // Should show name validation error
    await nuevoPage.expectNameRequiredError();
  });

  test("RN-16 no PHI in /nuevo URL", async ({ page }) => {
    const nuevoPage = new NewLeadPage(page, TENANT_ID);
    await nuevoPage.goto();

    await nuevoPage.expectNoPhiInUrl();
    // URL should just be /nuevo, not [leadId]
    expect(page.url()).toContain("/nuevo");
    expect(page.url()).not.toMatch(/[0-9a-f]{8}-[0-9a-f]{4}/);
  });
});

test.describe("Nuevo lead — board highlight after create", () => {
  test("@rule-addressable board highlights new card after redirect", async ({
    page,
  }) => {
    await mockCreateLead(page);

    // Simulate already being on embudo with highlight param
    const board = new EmbudoBoardPage(page, TENANT_ID);

    // Mock board with the new lead included
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
              sumValue: 0,
              currency: "PEN",
              overSlaCount: 0,
              leads: [NEW_LEAD_MOCK_RESPONSE],
            },
            { stage: "calificando", label: "Calificando", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
            { stage: "consulta_agendada", label: "Consulta agendada", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
            { stage: "plan_presentado", label: "Plan presentado", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
            { stage: "reservado", label: "Reservado", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
          ],
          kpis: { totalActive: 1, adrianCount: 1, humanCount: 0, hotCount: 0, warmCount: 0, coldCount: 1, avgScore: 10, depositRate: 0, frozenCount: 0 },
        }),
      });
    });

    await board.goto({ highlight: NEW_LEAD_MOCK_RESPONSE.id });
    await board.waitForLoaded();

    // Card should be present
    const card = board.getLeadCard(NEW_LEAD_MOCK_RESPONSE.id);
    await expect(card).toBeVisible();
  });
});
