/**
 * marketing.smoke.spec.ts — E2E smoke para /marketing
 *
 * Validator ID: e2e_smoke_marketing
 * Story: vitalia-slice-1-marketing
 * Ticket: T-mk-fe-7
 *
 * Cubre (gherkin_coverage):
 *   SC-MK-01: Lucas approval modal opens + closes (no confirm)
 *             → test_lucas_approval_modal_opens_closes_no_confirm
 *   SC-MK-03: Tab change updates URL + re-renders stage content
 *             → test_tab_change_updates_url_re_renders
 *   Bonus: bowtie carga con 5 tabs visibles (smoke básico)
 *
 * Network: todos los endpoints mocks via page.route() — no requiere stack live.
 * Auth: Clerk testing token via auth.fixture.ts (authedPage fixture).
 *
 * HIPAA-lite: fixtures no contienen PHI — solo IDs hash, slugs, agregados.
 *
 * Ejecución nativa (NUNCA make e2e):
 *   cd vitalia/frontend
 *   E2E_BASE_URL=http://localhost:3002 npx playwright test \
 *     --project=smoke e2e/specs/smoke/marketing.smoke.spec.ts
 *
 * downstream-regression-na: brand-local E2E smoke spec; no cross-brand consumers
 */

import { test, expect } from "../../auth.fixture";
import { MarketingPage } from "../../pages/marketing.page";

// ---------------------------------------------------------------------------
// Constantes de fixtures (sin PHI — solo datos de marketing agregados)
// ---------------------------------------------------------------------------

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";
const CLINIC_ID = "aurora-dental-ar-001";

/** Respuesta mock del Bowtie summary con 5 etapas */
const MOCK_BOWTIE_SUMMARY = {
  period_start: "2026-04-20T00:00:00Z",
  period_end: "2026-05-20T00:00:00Z",
  stages: [
    {
      slug: "attraction",
      label: "Atracción",
      count: 340,
      primary_kpi_value: 12.5,
      primary_kpi_label: "CTR",
    },
    {
      slug: "qualification",
      label: "Calificación",
      count: 180,
      primary_kpi_value: 52.9,
      primary_kpi_label: "Conv.",
    },
    {
      slug: "reservation",
      label: "Reserva",
      count: 95,
      primary_kpi_value: 52.8,
      primary_kpi_label: "Show",
    },
    {
      slug: "adoption",
      label: "Adopción",
      count: 67,
      primary_kpi_value: 70.5,
      primary_kpi_label: "Retenc.",
    },
    {
      slug: "expansion",
      label: "Expansión",
      count: 28,
      primary_kpi_value: null,
      primary_kpi_label: null,
    },
  ],
  overall_conversion_pct: 8.2,
  overall_roi_x: 3.4,
  overall_ltv_cents: 150000,
  currency: "ARS",
  last_sync_at: "2026-05-20T10:00:00Z",
};

/** Respuesta mock de recomendaciones Lucas — 1 recomendación activa */
const MOCK_LUCAS_RECOMMENDATIONS = {
  items: [
    {
      id: "rec-smoke-001",
      tenant_id: TENANT_ID,
      clinic_id: CLINIC_ID,
      stage: "attraction",
      recommendation_kind: "increase_budget",
      title: "Aumentar presupuesto Meta Ads en Atracción",
      body: "Lucas detectó que el canal Meta Ads genera un CTR de 12.5% pero el presupuesto diario es bajo. Aumentarlo un 20% incrementaría leads en ~40 por mes.",
      rationale_json: {
        canal: "meta_ads",
        ctr: "12.5%",
        budget_actual: "ARS 5.000/día",
      },
      action_payload_json: { increase_pct: 20, channel: "meta_ads" },
      priority: 1,
      confidence_pct: 87,
      projected_impact_text: "+40 leads/mes",
      status: "open",
      approved_by_user_id: null,
      approved_at: null,
      undo_until: null,
      expires_at: "2026-05-27T00:00:00Z",
      created_at: "2026-05-20T08:00:00Z",
    },
  ],
};

/** Respuesta mock del detalle de etapa "reservation" */
const MOCK_STAGE_DETAIL_RESERVATION = {
  stage: "reservation",
  label: "Reserva",
  period_start: "2026-04-20T00:00:00Z",
  period_end: "2026-05-20T00:00:00Z",
  count: 95,
  kpis: [
    {
      key: "show_rate",
      label: "Tasa de show",
      value: 78.5,
      unit: "pct",
      currency: null,
    },
    {
      key: "avg_lead_time_h",
      label: "Lead time promedio",
      value: 24,
      unit: "h",
      currency: null,
    },
  ],
  trend_data: [],
};

/** Respuesta mock de la matriz de atribución */
const MOCK_ATTRIBUTION = {
  origins: [
    {
      origin: "sales_agent",
      leads: 180,
      qualified: 90,
      conv_listo: 45,
      reservations: 38,
      adoption: 28,
      value_cents: 95000,
    },
    {
      origin: "walk_in",
      leads: 80,
      qualified: 50,
      conv_listo: 30,
      reservations: 25,
      adoption: 20,
      value_cents: 55000,
    },
    {
      origin: "phone_manual",
      leads: 50,
      qualified: 30,
      conv_listo: 15,
      reservations: 22,
      adoption: 14,
      value_cents: 35000,
    },
    {
      origin: "proactive_outbound",
      leads: 30,
      qualified: 10,
      conv_listo: 5,
      reservations: 10,
      adoption: 5,
      value_cents: 20000,
    },
  ],
  totals: {
    origin: "total",
    leads: 340,
    qualified: 180,
    conv_listo: 95,
    reservations: 95,
    adoption: 67,
    value_cents: 205000,
  },
  top_insight_text:
    "El canal Agente de ventas genera el 53% de los leads calificados.",
};

// ---------------------------------------------------------------------------
// Helper: instalar mocks de red comunes
// ---------------------------------------------------------------------------

async function setupMarketingMocks(page: import("@playwright/test").Page) {
  // Bowtie summary
  await page.route("**/api/v1/vitalia/marketing/bowtie/summary**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_BOWTIE_SUMMARY),
    });
  });

  // Lucas recommendations (todas las etapas)
  await page.route("**/api/v1/vitalia/marketing/recommendations**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_LUCAS_RECOMMENDATIONS),
    });
  });

  // Stage detail — cualquier etapa (genérico)
  await page.route("**/api/v1/vitalia/marketing/stages/**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_STAGE_DETAIL_RESERVATION),
    });
  });

  // Attribution matrix
  await page.route("**/api/v1/vitalia/marketing/attribution**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_ATTRIBUTION),
    });
  });

  // Referrals (si la etapa expansion las carga)
  await page.route("**/api/v1/vitalia/marketing/referrals**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ referrals: [], total: 0 }),
    });
  });

  // Channels (si expansion/attribution los carga)
  await page.route("**/api/v1/vitalia/marketing/channels**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ channels: [] }),
    });
  });
}

// ---------------------------------------------------------------------------
// Suite de smoke tests
// ---------------------------------------------------------------------------

test.describe("/marketing smoke", () => {
  // ─── Smoke básico: bowtie + tabs visibles ─────────────────────────────────

  test("carga bowtie SVG + 5 tabs de etapas visibles", async ({
    authedPage: page,
  }) => {
    await setupMarketingMocks(page);

    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.waitForReady();

    // Bowtie SVG presente y accesible
    await expect(mp.bowtieSvg).toBeVisible({ timeout: 10_000 });

    // 5 tabs del embudo visibles
    await expect(mp.stageTabs).toHaveCount(5);

    // Sección Lucas visible (h3 o loading)
    await expect(mp.lucasCardsSection).toBeVisible({ timeout: 10_000 });
  });

  // ─── SC-MK-03: Tab change updates URL + re-renders stage content ──────────

  test("test_tab_change_updates_url_re_renders: cambio de tab actualiza URL y re-renderiza contenido de etapa", async ({
    authedPage: page,
  }) => {
    await setupMarketingMocks(page);

    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.waitForReady();

    // Hacer clic en tab "Reserva" (slug=reservation)
    await mp.clickStageTab("reservation");

    // URL debe contener ?tab=reservation (nuqs replace)
    await expect(page).toHaveURL(/tab=reservation/, { timeout: 10_000 });

    // Panel de reserva visible
    await expect(mp.stagePanel("reservation")).toBeVisible({ timeout: 10_000 });

    // AttributionMatrix visible (SC-MK-03: matriz inline en etapa reservation)
    await expect(mp.attributionMatrix).toBeVisible({ timeout: 10_000 });
  });

  // ─── SC-MK-01: Lucas approval modal opens + closes (no confirm) ───────────

  test("test_lucas_approval_modal_opens_closes_no_confirm: modal de aprobación Lucas se abre y cierra sin confirmar", async ({
    authedPage: page,
  }) => {
    await setupMarketingMocks(page);

    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.waitForReady();

    // El panel de atracción (default tab) debe mostrar recomendaciones Lucas
    // Esperar a que la sección Lucas cargue
    await expect(mp.lucasCardsSection).toBeVisible({ timeout: 10_000 });

    // Hacer clic en el primer ítem Lucas para abrir el modal de detalle
    await mp.clickFirstLucasCardDetail();

    // Modal title visible (detail modal: "¿Confirmas la aprobación?" o el título del rec)
    await expect(mp.approvalModalTitle).toBeVisible({ timeout: 10_000 });

    // Cerrar modal SIN confirmar (botón "Cancelar" o "Cerrar" o Escape)
    await mp.closeApprovalModal();

    // Modal NO visible tras cierre
    await expect(mp.approvalModalTitle).toBeHidden({ timeout: 10_000 });
  });
});
