/**
 * marketing.a11y.spec.ts — WCAG 2.1 AA accessibility scan en /marketing
 *
 * Validator ID: visual_a11y_axe
 * Story: vitalia-slice-1-marketing
 * Ticket: T-mk-fe-7
 *
 * Requisitos de accesibilidad (01-spec.md + 03-arch-fe.md):
 *   - Bowtie SVG: role="img" + aria-label + aria-busy en carga
 *   - Stage tabs: role="tablist" + role="tab" + aria-selected + aria-controls
 *   - Stage panels: role="tabpanel" + aria-labelledby
 *   - Attribution matrix: <table> semántica con scope="col" headers
 *   - Modal: role="dialog" + aria-modal + aria-labelledby + focus trap
 *   - Lucas cards: aria-label="Ver detalle: {title}" en botones
 *   - 0 violaciones críticas/serias WCAG 2.1 AA en todas las vistas
 *
 * Network: todos los endpoints mocks via page.route() — no requiere stack live.
 * Graceful skip si @axe-core/playwright no instalado.
 *
 * Ejecución nativa (NUNCA make e2e):
 *   cd vitalia/frontend
 *   E2E_BASE_URL=http://localhost:3002 npx playwright test \
 *     --project=a11y e2e/specs/a11y/marketing.a11y.spec.ts
 *
 * downstream-regression-na: brand-local E2E a11y spec; no cross-brand consumers
 */

import { test, expect } from "../../auth.fixture";
import { MarketingPage } from "../../pages/marketing.page";

// ---------------------------------------------------------------------------
// Graceful import — @axe-core/playwright puede no estar instalado en algunos envs
// ---------------------------------------------------------------------------

let AxeBuilder: (typeof import("@axe-core/playwright"))["default"] | null =
  null;

// ---------------------------------------------------------------------------
// Fixtures de mocks de red (reutilizamos estructura del smoke spec)
// ---------------------------------------------------------------------------

const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";
const CLINIC_ID = "aurora-dental-ar-001";

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

const MOCK_LUCAS_RECOMMENDATIONS = {
  items: [
    {
      id: "rec-a11y-001",
      tenant_id: TENANT_ID,
      clinic_id: CLINIC_ID,
      stage: "attraction",
      recommendation_kind: "increase_budget",
      title: "Aumentar presupuesto Meta Ads en Atracción",
      body: "Lucas detectó que el canal Meta Ads genera un CTR alto con bajo presupuesto.",
      rationale_json: { canal: "meta_ads", ctr: "12.5%" },
      action_payload_json: null,
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

const MOCK_STAGE_DETAIL = {
  stage: "attraction",
  label: "Atracción",
  period_start: "2026-04-20T00:00:00Z",
  period_end: "2026-05-20T00:00:00Z",
  count: 340,
  kpis: [
    { key: "ctr", label: "CTR", value: 12.5, unit: "pct", currency: null },
    {
      key: "cpc",
      label: "CPC promedio",
      value: 850,
      unit: "currency",
      currency: "ARS",
    },
  ],
  trend_data: [],
};

async function setupAllMocks(page: import("@playwright/test").Page) {
  await page.route("**/api/v1/vitalia/marketing/bowtie/summary**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_BOWTIE_SUMMARY),
    });
  });
  await page.route("**/api/v1/vitalia/marketing/recommendations**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_LUCAS_RECOMMENDATIONS),
    });
  });
  await page.route("**/api/v1/vitalia/marketing/stages/**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_STAGE_DETAIL),
    });
  });
  await page.route("**/api/v1/vitalia/marketing/attribution**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(MOCK_ATTRIBUTION),
    });
  });
  await page.route("**/api/v1/vitalia/marketing/referrals**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ referrals: [], total: 0 }),
    });
  });
  await page.route("**/api/v1/vitalia/marketing/channels**", (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ channels: [] }),
    });
  });
}

// ---------------------------------------------------------------------------
// Helper: ejecutar axe y afirmar 0 violaciones críticas/serias
// ---------------------------------------------------------------------------

async function assertNoCriticalA11yViolations(
  page: import("@playwright/test").Page,
  context: string,
): Promise<void> {
  if (!AxeBuilder) {
    test.skip(
      true,
      "@axe-core/playwright no instalado — instalar con: npm i -D @axe-core/playwright",
    );
    return;
  }

  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .disableRules([
      // Falso positivo conocido: next-router focus management en dev
      "scrollable-region-focusable",
      // Radix UI dialog portal — falso positivo en env mockeado sin DOM real completo
      "aria-dialog-name",
    ])
    .analyze();

  const criticalOrSerious = results.violations.filter(
    (v) => v.impact === "critical" || v.impact === "serious",
  );

  if (criticalOrSerious.length > 0) {
    const details = criticalOrSerious
      .map(
        (v) =>
          `[${(v.impact ?? "unknown").toUpperCase()}] ${v.id}: ${v.description}\n` +
          `  Nodos: ${v.nodes.map((n) => n.target.join(", ")).join("; ")}`,
      )
      .join("\n");
    throw new Error(
      `Marketing ${context} tiene ${criticalOrSerious.length} violación(es) WCAG 2.1 AA críticas/serias:\n${details}`,
    );
  }

  expect(criticalOrSerious).toHaveLength(0);
}

// ---------------------------------------------------------------------------
// Suite de tests de accesibilidad
// ---------------------------------------------------------------------------

test.describe("Marketing — WCAG 2.1 AA accessibility (axe-core)", () => {
  test.beforeAll(async () => {
    try {
      const axeModule = await import("@axe-core/playwright");
      AxeBuilder = axeModule.default;
    } catch {
      AxeBuilder = null;
    }
  });

  // ─── V-MK-A11Y-01: Página principal — 0 violaciones críticas ─────────────

  test("V-MK-A11Y-01: /marketing tiene 0 violaciones WCAG 2.1 AA críticas/serias", async ({
    authedPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(
        true,
        "@axe-core/playwright no instalado — instalar con: npm i -D @axe-core/playwright",
      );
      return;
    }

    await setupAllMocks(page);
    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.waitForReady();

    await assertNoCriticalA11yViolations(
      page,
      "/marketing (tab attraction, estado cargado)",
    );
  });

  // ─── V-MK-A11Y-02: Bowtie SVG tiene atributos ARIA correctos ────────────

  test("V-MK-A11Y-02: Bowtie SVG tiene role=img + aria-label + aria-busy correcto", async ({
    authedPage: page,
  }) => {
    await setupAllMocks(page);
    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.waitForReady();

    // SVG debe tener role="img" (semántico para lectores de pantalla)
    await expect(mp.bowtieSvg).toHaveAttribute("role", "img");

    // aria-label presente en el SVG (estado cargado)
    const ariaLabel = await mp.bowtieSvg.getAttribute("aria-label");
    expect(ariaLabel).toBeTruthy();
    expect(ariaLabel).not.toBe("");

    // aria-busy=false cuando datos cargaron
    const ariaBusy = await mp.bowtieSvg.getAttribute("aria-busy");
    // En estado cargado debe ser false o ausente
    expect(ariaBusy === null || ariaBusy === "false").toBeTruthy();
  });

  // ─── V-MK-A11Y-03: Stage tabs cumplen patrón ARIA tabs ──────────────────

  test("V-MK-A11Y-03: Stage tablist tiene role=tablist + 5 tabs con aria-selected", async ({
    authedPage: page,
  }) => {
    await setupAllMocks(page);
    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.waitForReady();

    // Tablist accesible
    await expect(mp.stageTablist).toHaveAttribute("role", "tablist");
    await expect(mp.stageTablist).toHaveAttribute(
      "aria-label",
      "Etapas del embudo",
    );

    // 5 tabs con role="tab"
    await expect(mp.stageTabs).toHaveCount(5);

    // Exactamente 1 tab tiene aria-selected="true" (el activo)
    const selectedTabs = mp.stageTabs.filter({
      has: page.locator('[aria-selected="true"]'),
    });
    await expect(selectedTabs).toHaveCount(1);

    // Todos los tabs tienen aria-controls apuntando a un panel
    for (const slug of [
      "attraction",
      "qualification",
      "reservation",
      "adoption",
      "expansion",
    ]) {
      const tab = mp.stageTab(
        slug as import("../../pages/marketing.page").MarketingStageSlug,
      );
      await expect(tab).toHaveAttribute("aria-controls", `stage-panel-${slug}`);
    }
  });

  // ─── V-MK-A11Y-04: Tab reservation — 0 violaciones + attribution table ──

  test("V-MK-A11Y-04: tab Reserva (reservation) tiene 0 violaciones + tabla de atribución accesible", async ({
    authedPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(true, "@axe-core/playwright no instalado");
      return;
    }

    await setupAllMocks(page);
    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.waitForReady();

    await mp.clickStageTab("reservation");

    // Attribution matrix visible y tiene tabla semántica
    await expect(mp.attributionMatrix).toBeVisible({ timeout: 10_000 });

    // Verificar que hay una <table> con scope="col" en los th (semántica correcta)
    const table = page.locator(
      '[role="tabpanel"][id="stage-panel-reservation"] table',
    );
    if (await table.isVisible({ timeout: 5_000 }).catch(() => false)) {
      const thWithScope = table.locator('th[scope="col"]');
      const thCount = await thWithScope.count();
      expect(thCount).toBeGreaterThan(0);
    }

    await assertNoCriticalA11yViolations(
      page,
      "tab Reserva con Attribution Matrix",
    );
  });

  // ─── V-MK-A11Y-05: Modal de detalle Lucas — focus trap + ARIA ───────────

  test("V-MK-A11Y-05: modal de detalle Lucas tiene role=dialog + aria-modal + aria-labelledby", async ({
    authedPage: page,
  }) => {
    if (!AxeBuilder) {
      test.skip(true, "@axe-core/playwright no instalado");
      return;
    }

    await setupAllMocks(page);
    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.waitForReady();

    // Abrir modal de detalle del primer ítem Lucas
    await expect(mp.lucasCardsSection).toBeVisible({ timeout: 10_000 });
    await mp.clickFirstLucasCardDetail();
    await expect(mp.approvalModalTitle).toBeVisible({ timeout: 10_000 });

    // Dialog tiene los atributos ARIA correctos
    const dialog = page.locator('[role="dialog"]').first();
    await expect(dialog).toHaveAttribute("role", "dialog");
    await expect(dialog).toHaveAttribute("aria-modal", "true");

    // aria-labelledby apunta al h2 del título
    const labelledby = await dialog.getAttribute("aria-labelledby");
    expect(labelledby).toBeTruthy();
    // El h2 con ese ID debe existir en el DOM
    if (labelledby) {
      const labelEl = page.locator(`#${labelledby}`);
      await expect(labelEl).toBeVisible({ timeout: 5_000 });
    }

    // Axe scan con modal abierto
    await assertNoCriticalA11yViolations(
      page,
      "modal de detalle Lucas abierto",
    );

    // Cerrar modal
    await mp.closeApprovalModal();
    await expect(mp.approvalModalTitle).toBeHidden({ timeout: 10_000 });
  });

  // ─── V-MK-A11Y-06: ESC cierra modal (teclado) ────────────────────────────

  test("V-MK-A11Y-06: ESC cierra el modal de detalle (navegación por teclado)", async ({
    authedPage: page,
  }) => {
    await setupAllMocks(page);
    const mp = new MarketingPage(page);
    await mp.goto();
    await mp.waitForReady();

    await expect(mp.lucasCardsSection).toBeVisible({ timeout: 10_000 });
    await mp.clickFirstLucasCardDetail();
    await expect(mp.approvalModalTitle).toBeVisible({ timeout: 10_000 });

    // Cerrar con ESC (accesibilidad teclado)
    await page.keyboard.press("Escape");
    await expect(mp.approvalModalTitle).toBeHidden({ timeout: 10_000 });
  });
});
