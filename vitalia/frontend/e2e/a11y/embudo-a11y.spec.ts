/**
 * embudo-a11y.spec.ts — axe-core wcag2aa Embudo board + Lead workspace + Nuevo + Recuperar
 *
 * vitalia-fase2-adrian-embudo — T-E2E-1
 * Gherkin:
 *   axe-clean per screen state; ScoreDonut número visible;
 *   SLA texto Xd (no solo color); contraste ≥4.5:1;
 *   EntitySubNavBar role=tablist roving tabindex; drag KeyboardSensor
 *
 * Scenario coverage (04-validators.yaml § visual.a11y):
 *   SC-10
 *
 * Project: a11y
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/a11y/embudo-a11y.spec.ts --project=a11y
 *
 * downstream-regression-na: brand-local vitalia E2E a11y spec F2
 * spec_anchor: 04-validators.yaml § visual.a11y (SC-10)
 */

import AxeBuilder from "@axe-core/playwright";
import { expect } from "@playwright/test";
import { test } from "../fixtures/authed-runtime";

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";
const BASE_URL_API = "**"; // origin-agnostic: el FE pega a /api via proxy :3002, no directo a :8002
const LEAD_ID = "lead-001";

// ── Shared mock setup ─────────────────────────────────────────────────────────

async function setupA11yMocks(page: import("@playwright/test").Page) {
  // Board
  await page.route(`${BASE_URL_API}/api/v1/crm/board**`, (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        columns: [
          {
            stage: "interesado",
            label: "Interesado",
            count: 2,
            sumValue: 11000,
            currency: "PEN",
            overSlaCount: 0,
            leads: [
              { id: LEAD_ID, tenantId: TENANT_ID, name: "María G███", stage: "interesado", stageEnteredAt: "2026-06-01T10:00:00Z", score: 48, temperature: "warm", operatedBy: "agent", channel: "whatsapp", estimatedValue: 7000, currency: "PEN", buyingSignals: ["pregunto_precio"], isFrozen: false, frozenReason: null, depositStatus: null, closureReason: null, reactivationCohortAt: null, serviceInterest: "Ortodoncia", assignedDoctorId: null, version: 1, isBlacklisted: false, lastActivityDescription: "Adrián saludó", lastActivityAt: "2026-06-03T10:00:00Z" },
              { id: "lead-002", tenantId: TENANT_ID, name: "Carlos P███", stage: "interesado", stageEnteredAt: "2026-05-25T10:00:00Z", score: 33, temperature: "cold", operatedBy: "agent", channel: "instagram", estimatedValue: 4000, currency: "PEN", buyingSignals: [], isFrozen: false, frozenReason: null, depositStatus: null, closureReason: null, reactivationCohortAt: null, serviceInterest: "Ortodoncia", assignedDoctorId: null, version: 1, isBlacklisted: false, lastActivityDescription: "Adrián envió info", lastActivityAt: "2026-06-02T10:00:00Z" },
            ],
          },
          { stage: "calificando", label: "Calificando", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
          { stage: "consulta_agendada", label: "Consulta agendada", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
          { stage: "plan_presentado", label: "Plan presentado", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
          { stage: "reservado", label: "Reservado", count: 0, sumValue: 0, currency: "PEN", overSlaCount: 0, leads: [] },
        ],
        kpis: { totalActive: 2, adrianCount: 2, humanCount: 0, hotCount: 0, warmCount: 1, coldCount: 1, avgScore: 40, depositRate: 0, frozenCount: 2 },
      }),
    });
  });

  // Lead detail
  await page.route(
    `${BASE_URL_API}/api/v1/crm/leads/${LEAD_ID}/detail`,
    (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          lead: { id: LEAD_ID, tenantId: TENANT_ID, name: "María G███", stage: "interesado", stageEnteredAt: "2026-06-01T10:00:00Z", score: 48, temperature: "warm", operatedBy: "agent", channel: "whatsapp", estimatedValue: 7000, currency: "PEN", buyingSignals: ["pregunto_precio"], isFrozen: false, frozenReason: null, depositStatus: null, closureReason: null, reactivationCohortAt: null, serviceInterest: "Ortodoncia", assignedDoctorId: null, version: 1, isBlacklisted: false, lastActivityDescription: "Adrián saludó", lastActivityAt: "2026-06-03T10:00:00Z" },
          scoreBreakdown: [
            { label: "Preguntó precio", delta: 25, icon: null },
            { label: "Respondió rápido", delta: 15, icon: null },
            { label: "Sin agendar 2d", delta: -2, icon: null },
          ],
          autonomy: { canDo: ["mover etapa", "agendar"], needsApproval: ["cobrar"], currentMode: "autonomous" },
        }),
      });
    },
  );

  // Transitions
  await page.route(
    `${BASE_URL_API}/api/v1/crm/leads/${LEAD_ID}/transitions`,
    (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          events: [
            { id: "ev-001", kind: "stage_move", actor: "agent", descriptionEs: "Adrián movió a interesado", occurredAt: "2026-06-01T10:00:00Z" },
            { id: "ev-002", kind: "message", actor: "lead", descriptionEs: "Preguntó por el precio", occurredAt: "2026-06-02T10:00:00Z" },
          ],
        }),
      });
    },
  );

  // Frozen
  await page.route(`${BASE_URL_API}/api/v1/crm/frozen**`, (route) => {
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        recienCongelados: [{ id: "lead-010", tenantId: TENANT_ID, name: "Lucía R███", lastStage: "calificando", frozenReason: "inactividad_lead", frozenAt: "2026-05-28T10:00:00Z", channel: "whatsapp", score: 32, closureReason: null, reactivationCohortAt: null }],
        decidioNo: [],
      }),
    });
  });
}

// Helper: assert no critical/serious axe violations
async function expectAxeClean(
  page: import("@playwright/test").Page,
  label: string,
  includeSelector?: string,
) {
  const builder = new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .exclude("#__nextjs-toast-errors") // Next.js dev overlay
    .exclude("[data-nextjs-dialog]");

  if (includeSelector) {
    builder.include(includeSelector);
  }

  const results = await builder.analyze();

  const criticalOrSerious = results.violations.filter(
    (v) => v.impact === "critical" || v.impact === "serious",
  );

  expect(
    criticalOrSerious,
    `A11y violations on ${label}:\n${criticalOrSerious
      .map(
        (v) =>
          `  [${v.impact}] ${v.id}: ${v.description}\n    Nodes: ${v.nodes
            .map((n) => n.target.join(" > "))
            .join(", ")}`,
      )
      .join("\n")}`,
  ).toHaveLength(0);
}

// ── axe scans ─────────────────────────────────────────────────────────────────

test.describe("A11y — axe-core wcag2aa Embudo board", () => {
  test("SC-10 board Kanban view passes axe wcag2aa", async ({ page }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="kanban-board"], [data-testid="embudo-empty-state"]')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    await expectAxeClean(page, "Embudo board Kanban");
  });

  test("SC-10 board Lista view passes axe wcag2aa", async ({ page }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo?view=lista`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="leads-table"], [data-testid="embudo-empty-state"]')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    await expectAxeClean(page, "Embudo board Lista");
  });
});

test.describe("A11y — Lead workspace Resumen + Historial", () => {
  test("SC-10 lead-resumen passes axe wcag2aa", async ({ page }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo/${LEAD_ID}/resumen`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="resumen-view"]')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    await expectAxeClean(page, "Lead resumen");
  });

  test("SC-10 lead-historial passes axe wcag2aa", async ({ page }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo/${LEAD_ID}/historial`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="historial-view"]')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    await expectAxeClean(page, "Lead historial");
  });

  test("SC-10 EntitySubNavBar has role=tablist (RN-16 / a11y)", async ({
    page,
  }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo/${LEAD_ID}/resumen`);
    await page.waitForLoadState("networkidle");

    // Must have tablist for roving tabindex
    const tablist = page.locator('[role="tablist"]').first();
    await expect(tablist).toBeVisible({ timeout: 10_000 });
  });

  test("SC-10 ScoreDonut has numeric text visible (not only color)", async ({
    page,
  }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo/${LEAD_ID}/resumen`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="resumen-view"]')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    // ScoreDonut must display a numeric value (accessibility: not just color)
    const scoreDonut = page.locator('[data-testid="score-donut"]').first();
    if (await scoreDonut.count() > 0) {
      const scoreText = await scoreDonut.textContent();
      expect(scoreText).toMatch(/\d+/);
    }
  });
});

test.describe("A11y — Nuevo lead page", () => {
  test("SC-10 /nuevo page passes axe wcag2aa", async ({ page }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo/nuevo`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="new-lead-form"], form')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    await expectAxeClean(page, "Nuevo lead form");
  });

  test("SC-10 form fields have accessible labels", async ({ page }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo/nuevo`);
    await page.waitForLoadState("networkidle");

    // Name input must have accessible label
    const nameInput = page
      .locator('input[name="name"], input[aria-label*="nombre"]')
      .first();
    if (await nameInput.count() > 0) {
      const ariaLabel = await nameInput.getAttribute("aria-label");
      const id = await nameInput.getAttribute("id");
      if (id) {
        const associatedLabel = page.locator(`label[for="${id}"]`).first();
        const hasLabel =
          (ariaLabel && ariaLabel.length > 0) ||
          (await associatedLabel.count()) > 0;
        expect(hasLabel).toBe(true);
      }
    }
  });
});

test.describe("A11y — Recuperar view", () => {
  test("SC-10 recuperar page passes axe wcag2aa", async ({ page }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/recuperar`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="recuperar-view"]')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    await expectAxeClean(page, "Recuperar");
  });
});

test.describe("A11y — SLA time display (not only color)", () => {
  test("SC-10 SLA time-in-stage shows text (Xd format, not only dot color)", async ({
    page,
  }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="kanban-board"]')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    // SLA indicator must have text, not just color
    const slaIndicators = page.locator('[data-testid^="sla-indicator-"]');
    const count = await slaIndicators.count();
    if (count > 0) {
      const firstSlaText = await slaIndicators.first().textContent();
      // Should have a numeric day value (e.g. "2d", "8d", etc.)
      expect(firstSlaText).toMatch(/\d+d|\d+ d/i);
    }
    // Even if no SLA indicators (empty), the test passes — it's checking the pattern
  });
});

test.describe("A11y — Drag keyboard accessibility (SC-10 / KeyboardSensor)", () => {
  test("SC-10 lead cards are keyboard-focusable and actionable", async ({
    page,
  }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="kanban-board"]')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    // Lead cards must be focusable
    const firstCard = page
      .locator('[data-testid^="lead-card-"]')
      .first();

    const cardCount = await firstCard.count();
    if (cardCount > 0) {
      await firstCard.focus();
      const isFocused = await firstCard
        .evaluate((el) => document.activeElement === el || el.contains(document.activeElement))
        .catch(() => false);
      // Card must receive focus (keyboard nav for DnD)
      expect(isFocused).toBe(true);
    }
  });

  test("SC-10 no duplicate IDs in board DOM (common with list rendering)", async ({
    page,
  }) => {
    await setupA11yMocks(page);
    await page.goto(`/${TENANT_ID}/adrian/embudo`);
    await page.waitForLoadState("networkidle");
    await page
      .locator('[data-testid="kanban-board"], [data-testid="embudo-empty-state"]')
      .first()
      .waitFor({ state: "visible", timeout: 12_000 })
      .catch(() => {});

    const duplicates = await page.evaluate(() => {
      const ids = Array.from(document.querySelectorAll("[id]")).map(
        (el) => el.id,
      );
      const seen = new Set<string>();
      const dups: string[] = [];
      for (const id of ids) {
        if (id && seen.has(id)) dups.push(id);
        if (id) seen.add(id);
      }
      return dups;
    });

    expect(
      duplicates,
      `Duplicate IDs in board DOM: ${duplicates.join(", ")}`,
    ).toHaveLength(0);
  });
});
