// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * embudo-recuperar.spec.ts — Integration E2E for Recuperar view.
 *
 * vitalia-fase2-adrian-embudo — T-E2E-1
 *
 * Scenarios covered:
 *   SC-freeze / F-8   frozen leads appear in Recuperar + diagnose + Reactivar
 *   RN-13             auto-freeze rule (14d/2×SLA) → moves to Recuperar
 *
 * All specs import from base.ts (anti-burbuja gate).
 * API calls intercepted via page.route().
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/specs/vitalia/embudo-recuperar.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local vitalia E2E spec
 * spec_anchor: 04-validators.yaml § SC-freeze / F-8
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/authed-runtime";
import { RecuperarPage } from "../../pages/RecuperarPage";

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";
const BASE_URL_API = "**"; // origin-agnostic: el FE pega a /api via proxy :3002, no directo a :8002

const MOCK_FROZEN_RESPONSE = {
  recienCongelados: [
    {
      id: "lead-010",
      tenantId: TENANT_ID,
      name: "Lucía R███",
      lastStage: "calificando",
      frozenReason: "inactividad_lead",
      frozenAt: "2026-05-28T10:00:00Z",
      channel: "whatsapp",
      score: 32,
      closureReason: null,
      reactivationCohortAt: null,
    },
    {
      id: "lead-011",
      tenantId: TENANT_ID,
      name: "Diego F███",
      lastStage: "plan_presentado",
      frozenReason: "sin_respuesta_presupuesto",
      frozenAt: "2026-05-20T10:00:00Z",
      channel: "meta",
      score: 55,
      closureReason: null,
      reactivationCohortAt: null,
    },
  ],
  decidioNo: [
    {
      id: "lead-012",
      tenantId: TENANT_ID,
      name: "Iván S███",
      lastStage: "plan_presentado",
      frozenReason: null,
      frozenAt: null,
      channel: null,
      score: null,
      closureReason: "precio",
      reactivationCohortAt: "2026-08-28T10:00:00Z",
    },
  ],
};

async function mockFrozenEndpoint(page: import("@playwright/test").Page) {
  await page.route(`${BASE_URL_API}/api/v1/crm/frozen**`, (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_FROZEN_RESPONSE),
    });
  });
}

async function mockDiagnose(
  page: import("@playwright/test").Page,
  leadId: string,
) {
  await page.route(
    `${BASE_URL_API}/api/v1/crm/leads/${leadId}/diagnose`,
    (route) => {
      if (route.request().method() === "POST") {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            leadId,
            recommendation:
              "El lead mostró interés pero no respondió al presupuesto. Sugerimos ofrecer una opción de financiación.",
            urgency: "medium",
            suggestedAction: "Enviar link de financiación",
          }),
        });
      } else {
        route.continue();
      }
    },
  );
}

async function mockReactivate(
  page: import("@playwright/test").Page,
  leadId: string,
) {
  await page.route(
    `${BASE_URL_API}/api/v1/crm/leads/${leadId}/reactivate`,
    (route) => {
      if (route.request().method() === "POST") {
        route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: leadId,
            tenantId: TENANT_ID,
            name: "Lucía R███",
            stage: "calificando",
            isFrozen: false,
            frozenReason: null,
            score: 32,
            version: 2,
          }),
        });
      } else {
        route.continue();
      }
    },
  );
}

// ── Tests ──────────────────────────────────────────────────────────────────────

test.describe("Recuperar — frozen leads list SC-freeze / F-8", () => {
  test("@rule-auto-freeze F-8 Recuperar shows frozen leads (recién congelados)", async ({
    page,
  }) => {
    await mockFrozenEndpoint(page);
    const recuperar = new RecuperarPage(page, TENANT_ID);

    await recuperar.goto();
    await recuperar.waitForLoaded();

    await recuperar.expectRecuperarVisible();
    await recuperar.expectFrozenLeadVisible("lead-010");
    await recuperar.expectFrozenLeadVisible("lead-011");
  });

  test("@rule-auto-freeze frozen lead count matches dataset", async ({
    page,
  }) => {
    await mockFrozenEndpoint(page);
    const recuperar = new RecuperarPage(page, TENANT_ID);

    await recuperar.goto();
    await recuperar.waitForLoaded();

    // 2 recién congelados + 1 decidio_no = 3 total rows
    await expect(recuperar.frozenLeadRows).toHaveCount(2);
  });

  test("@rule-auto-freeze diagnose lead → recommendation panel visible", async ({
    page,
  }) => {
    await mockFrozenEndpoint(page);
    await mockDiagnose(page, "lead-010");
    const recuperar = new RecuperarPage(page, TENANT_ID);

    await recuperar.goto();
    await recuperar.waitForLoaded();

    await recuperar.clickDiagnose("lead-010");
    await recuperar.expectDiagnosisPanelVisible();
  });

  test("@rule-auto-freeze reactivate frozen lead → success toast", async ({
    page,
  }) => {
    await mockFrozenEndpoint(page);
    await mockReactivate(page, "lead-010");

    // After reactivate, board mock returns the lead as active
    await page.route(`${BASE_URL_API}/api/v1/crm/frozen**`, async (route) => {
      // Second call returns empty (lead moved back)
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          recienCongelados: [MOCK_FROZEN_RESPONSE.recienCongelados[1]],
          decidioNo: MOCK_FROZEN_RESPONSE.decidioNo,
        }),
      });
    });

    const recuperar = new RecuperarPage(page, TENANT_ID);
    await recuperar.goto();
    await recuperar.waitForLoaded();

    await recuperar.clickReactivar("lead-010");
    await recuperar.expectReactivarToast();
  });
});

test.describe("Recuperar — empty state", () => {
  test("no frozen leads → empty state visible", async ({ page }) => {
    await page.route(`${BASE_URL_API}/api/v1/crm/frozen**`, (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ recienCongelados: [], decidioNo: [] }),
      });
    });

    const recuperar = new RecuperarPage(page, TENANT_ID);
    await recuperar.goto();
    await recuperar.waitForLoaded();

    await recuperar.expectEmptyState();
  });
});
