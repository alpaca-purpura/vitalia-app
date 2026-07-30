// cap: configuracion.cuenta
// story-origin: vitalia-fase2-config-cuenta
/**
 * config-cuenta-visual.spec.ts — visual goldens · sub-tab "Mi cuenta"
 *
 * 3 snapshots (plan original 04-validators § visual_goldens · generados post fix UI
 * 2026-06-12 — campos agrupados en SectionCard per mockup ratificado):
 *   1. cuenta-datos.png        (/config/cuenta/datos)
 *   2. cuenta-prefs.png        (/config/cuenta/preferencias)
 *   3. cuenta-resp.png         (/config/cuenta/responsable)
 *
 * Threshold: maxDiffPixelRatio 0.001 (0.1%) — project=visual (animations disabled).
 * Data: mocks deterministas via page.route (patrón lisa-marca-visual.spec.ts) —
 * los goldens congelan el CONTRATO VISUAL; el contrato funcional lo cubre
 * e2e/shell-organism/config-cuenta.spec.ts (real backend).
 *
 * GENERATE baseline:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/config-cuenta-visual.spec.ts --project=visual --update-snapshots
 * VERIFY:
 *   ... --project=visual   (sin --update-snapshots)
 *
 * Ratchet: una vez ratificados, cambiarlos requiere re-ratificación explícita Chris
 * (shell-mockup-per-component.md). Origen: fix UI post-done — los campos quedaron
 * sueltos y ningún gate mecánico lo vio (WARN goldens pendientes mordió).
 *
 * downstream-regression-na: brand-local vitalia visual spec
 */

import { test, expect, type Page } from "@playwright/test";

const BASE_URL = process.env["E2E_BASE_URL"] ?? "http://localhost:3002";
/** Tenant del storageState (dr.demo) — la ruta exige tenant válido del user. */
const TENANT_ID = "e69a691d-070e-5caf-a053-6e74642ec100";

const THRESHOLD = { maxDiffPixelRatio: 0.001 } as const;

// ---------------------------------------------------------------------------
// Deterministic API mocks (snake_case — shape real del BE)
// ---------------------------------------------------------------------------

const ACCOUNT_FIXTURE = {
  clinic_id: "11111111-1111-4111-8111-111111111111",
  tenant_id: TENANT_ID,
  name: "Clínica Aurora Dental",
  slug: "aurora-dental-ar",
  country: "AR",
  timezone: "America/Argentina/Buenos_Aires",
  plan_tier: "pro",
  is_active: true,
  legal_name: "Aurora Salud S.A.",
  fiscal_id: "30-71234567-8",
  address: "Av. Corrientes 1234, C1043 CABA",
  phone: "+54 11 4123-4567",
  email: "hola@auroradental.com.ar",
  language: "es-419",
  currency: "ARS",
  primary_specialties: ["odontologia-estetica", "medicina-estetica"],
};

const CATALOG_FIXTURE = {
  country: "AR",
  specialties: [
    { id: "odontologia-estetica", name: "Odontología estética", tier: 1 },
    { id: "medicina-estetica", name: "Medicina estética", tier: 1 },
    { id: "oftalmologia-refractiva", name: "Oftalmología refractiva", tier: 1 },
    { id: "psicologia", name: "Psicología", tier: 2 },
  ],
};

const DPO_FIXTURE = {
  name: "Dra. Marina López",
  email: "privacidad@auroradental.com.ar",
  role_label: "Responsable de tratamiento (DPO)",
  manage_url_subpath: "config/seguridad",
};

async function setupCuentaMocks(page: Page): Promise<void> {
  await page.route("**/api/v1/clinics/account/specialties-catalog**", (r) =>
    r.fulfill({ json: CATALOG_FIXTURE }),
  );
  await page.route("**/api/v1/clinics/account/dpo**", (r) => r.fulfill({ json: DPO_FIXTURE }));
  await page.route("**/api/v1/clinics/account/", (r) => r.fulfill({ json: ACCOUNT_FIXTURE }));
}

/** Mask dinámicos: indicador de autosave (timestamps/estado). */
const DYNAMIC_MASKS = (page: Page) => [page.locator('[data-testid="autosave-indicator"]')];

// ---------------------------------------------------------------------------
// Goldens
// ---------------------------------------------------------------------------

test.describe("config/cuenta — visual goldens (3 sub-sub-tabs)", () => {
  test.beforeEach(async ({ page }) => {
    await setupCuentaMocks(page);
  });

  test("cuenta-datos", async ({ page }) => {
    await page.goto(`${BASE_URL}/${TENANT_ID}/config/cuenta/datos`);
    await page.waitForSelector('[data-testid="account-data-view"]', { timeout: 15_000 });
    await page.waitForTimeout(1200); // settle fonts/layout
    await expect(page).toHaveScreenshot("cuenta-datos.png", {
      ...THRESHOLD,
      fullPage: true,
      mask: DYNAMIC_MASKS(page),
    });
  });

  test("cuenta-prefs", async ({ page }) => {
    await page.goto(`${BASE_URL}/${TENANT_ID}/config/cuenta/preferencias`);
    await page.waitForSelector('[data-testid="preferences-view"]', { timeout: 15_000 });
    await page.waitForTimeout(1200);
    await expect(page).toHaveScreenshot("cuenta-prefs.png", {
      ...THRESHOLD,
      fullPage: true,
      mask: DYNAMIC_MASKS(page),
    });
  });

  test("cuenta-resp", async ({ page }) => {
    await page.goto(`${BASE_URL}/${TENANT_ID}/config/cuenta/responsable`);
    await page.waitForSelector('[data-testid="responsible-view"]', { timeout: 15_000 });
    await page.waitForTimeout(1200);
    await expect(page).toHaveScreenshot("cuenta-resp.png", {
      ...THRESHOLD,
      fullPage: true,
      mask: DYNAMIC_MASKS(page),
    });
  });
});
