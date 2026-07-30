// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * resumen-live.spec.ts — Live-verify del lead-detail Resumen contra dev-app real.
 *
 * Origen: Chris pegó un runtime crash (2026-06-04) en
 *   /{tenant}/adrian/embudo/{leadId}/resumen — ResumenView.tsx:184
 *   `autonomy.canDo.join(...)` undefined. Causa: el FE imaginó el contrato
 *   `canDo/needsApproval/currentMode`; el BE emite `operated_by/can/needs_ok`
 *   (AutonomyInfo). `board-live.spec.ts` cubría board + writes pero NUNCA el
 *   lead-detail → ese fue el gap de live-verify que dejó pasar el crash.
 *
 * Scenario D — lead-detail Resumen renderiza live SIN burbuja Next:
 *   abre el workspace del primer lead del board → assert resumen-view +
 *   bloque "Estado del agente" (la línea que crasheaba) sin pageerror.
 *
 * ★ Backend REAL (sin MSW). Gate anti-burbuja: importa base.ts
 *   (pageerror / console.error / /api 4xx-5xx / Next overlay) — el crash
 *   `autonomy.can` undefined dispararía pageerror y haría fallar el teardown.
 *
 * Auth: storageState playwright/.clerk/user.json (dr.demo@vitalialat.com).
 *
 * Run:
 *   cd vitalia/frontend && \
 *   E2E_BASE_URL=https://dev-app.vitalialat.com \
 *   npx playwright test e2e/regression/vitalia-fase2-adrian-embudo/resumen-live.spec.ts \
 *   --project=smoke --timeout=90000
 *
 * downstream-regression-na: brand-local vitalia live-verify; no cross-brand consumers.
 * spec_anchor: 01-spec.md § V3 Vista Resumen + ResumenView.tsx
 */

import { test, expect } from "../../fixtures/base";
import { EmbudoBoardPage } from "../../pages/EmbudoBoardPage";

const TENANT_ID =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";

test.describe("vitalia-fase2-adrian-embudo — lead-detail Resumen live", () => {
  test("D: Resumen del lead renderiza Estado del agente sin crash", async ({
    page,
  }) => {
    // Target lead: env override (RESUMEN_LEAD_ID) for a specific lead, else the
    // first card on the live board. Env override lets us pin an AGENT-operated
    // lead so the autonomy branch (the line that crashed) is actually exercised.
    let leadId = process.env["RESUMEN_LEAD_ID"] ?? "";
    if (!leadId) {
      const board = new EmbudoBoardPage(page, TENANT_ID);
      await board.goto();
      await board.waitForLoaded();
      const firstCard = page.locator('[data-testid^="lead-card-"]').first();
      const hasLead = (await firstCard.count()) > 0;
      test.skip(
        !hasLead,
        "No hay leads en el board live — no se puede abrir el Resumen.",
      );
      const testId = await firstCard.getAttribute("data-testid");
      leadId = testId?.replace("lead-card-", "") ?? "";
    }
    expect(leadId, "lead id objetivo (env o primer card)").not.toBe("");

    // Navega al workspace Resumen — la superficie EXACTA que crasheaba.
    await page.goto(`/${TENANT_ID}/adrian/embudo/${leadId}/resumen`);

    // ResumenView debe montar (si crashea, base.ts captura el pageerror).
    const resumen = page.locator('[data-testid="resumen-view"]');
    await expect(resumen, "ResumenView debe renderizar").toBeVisible({
      timeout: 30_000,
    });

    // El bloque "Estado del agente" siempre renderiza; su línea de autonomía
    // (`autonomy.can.join`) es la que reventaba. Si el lead lo opera el agente,
    // el bloque "Puede:" aparece — assert no-vacío cuando está presente.
    await expect(
      page.getByText("Estado del agente"),
      "Bloque Estado del agente presente",
    ).toBeVisible();

    const puede = page.getByText("Puede:", { exact: false });
    if ((await puede.count()) > 0) {
      await expect(
        puede.first(),
        "Línea de autonomía 'Puede:' renderiza (autonomy.can OK)",
      ).toBeVisible();
    }
    // Gate anti-burbuja via base.ts teardown (pageerror/console/overlay = vacío).
  });

  // ── E — B2 (score computado) + U1 (nombre completo) + U2 (contacto) ──────────
  test("E: Resumen muestra nombre completo + teléfono/email + score == Σfactores", async ({
    page,
  }) => {
    let leadId = process.env["RESUMEN_LEAD_ID"] ?? "";
    if (!leadId) {
      const board = new EmbudoBoardPage(page, TENANT_ID);
      await board.goto();
      await board.waitForLoaded();
      const firstCard = page.locator('[data-testid^="lead-card-"]').first();
      const hasLead = (await firstCard.count()) > 0;
      test.skip(!hasLead, "No hay leads en el board live.");
      const testId = await firstCard.getAttribute("data-testid");
      leadId = testId?.replace("lead-card-", "") ?? "";
    }
    expect(leadId).not.toBe("");

    await page.goto(`/${TENANT_ID}/adrian/embudo/${leadId}/resumen`);
    const resumen = page.locator('[data-testid="resumen-view"]');
    await expect(resumen).toBeVisible({ timeout: 30_000 });

    // U1 — el nombre del prospecto NO va enmascarado (non_phi). No debe existir
    // ningún <span data-phi data-phi-type="name"> dentro del Resumen.
    await expect(
      resumen.locator('[data-phi][data-phi-type="name"]'),
      "U1: el nombre NO debe estar enmascarado (non_phi marketing lead)",
    ).toHaveCount(0);

    // U2 — filas de contacto presentes en "Datos del lead".
    await expect(
      page.getByText("Teléfono", { exact: false }),
      "U2: fila Teléfono presente",
    ).toBeVisible();
    await expect(
      page.getByText("Correo", { exact: false }),
      "U2: fila Correo presente",
    ).toBeVisible();

    // B2 — el número grande del score == suma (clampada 0..100) de los deltas del
    // breakdown (glass-box). Antes mentía: número=0 stored mientras factores=+10.
    const breakdown = page.locator('[data-testid="score-breakdown"]');
    await expect(breakdown).toBeVisible();
    const progressbar = breakdown.locator('[role="progressbar"]');
    const ariaNow = await progressbar.getAttribute("aria-valuenow");
    const shownScore = Number(ariaNow ?? "NaN");

    const deltaTexts = await breakdown
      .locator("ul[aria-label='Factores que afectan el puntaje'] li span:last-child")
      .allInnerTexts();
    if (deltaTexts.length > 0) {
      const sum = deltaTexts.reduce((acc, t) => acc + Number(t.replace("+", "")), 0);
      const clamped = Math.max(0, Math.min(100, sum));
      expect(
        shownScore,
        `B2: el score mostrado (${shownScore}) debe == Σfactores clampada (${clamped}). ` +
          "Antes mostraba lead.score STORED (0) mientras el breakdown sumaba +10.",
      ).toBe(clamped);
    }
    // Gate anti-burbuja via base.ts teardown.
  });
});
