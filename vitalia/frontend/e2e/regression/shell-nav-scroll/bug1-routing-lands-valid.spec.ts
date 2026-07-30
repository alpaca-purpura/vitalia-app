/**
 * bug1-routing-lands-valid.spec.ts — Bug #1: el landing post-login aterriza en
 * una ruta que existe (nunca 404). RN-1 · gherkin bug1_routing_lands_valid.
 *
 * Antes: /{tenantId} → /{tenantId}/valeria/agenda → 404 (isValidAgent('valeria')
 * === false). Ahora: → /{tenantId}/mateo/agenda (DEFAULT_LANDING_SUBPATH, ruta
 * estática shipped) via proxy edge-redirect fix (ya committed).
 *
 * REWORK hybrid-mock → real-backend:
 *   Usa real-backend-forward.fixture (Clerk auth + /api/v1/** → BE :8002 +
 *   gate anti-burbuja base.ts). Sin mock de /api/tenants — el shell resuelve
 *   tenants server-side; el mock client-side era un artefacto hybrid-mock
 *   (handoff aprendizaje #4).
 *
 * TENANT_ID lee E2E_TENANT_ID (tenant owned por el usuario autenticado).
 * NUNCA usar el fallback "vitalia-test-tenant" → cross-tenant-block en BE real.
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import {
  test,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";

const DESKTOP = { width: 1280, height: 720 };

test.describe("Bug #1 — routing post-login lands on a valid route (RN-1)", () => {
  test.use({ viewport: DESKTOP });

  test("/{tenantId} redirige a mateo/agenda (NO valeria/agenda → 404)", async ({
    page,
  }) => {
    // Gate anti-burbuja ON (heredado de mergeTests en la fixture).
    await page.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });
    await page.waitForURL(/\/mateo\/agenda/, { timeout: 20_000 });
    expect(page.url()).toContain("/mateo/agenda");
    expect(page.url()).not.toContain("valeria/agenda");
    // El gate anti-burbuja (teardown de base.ts via mergeTests) confirma cero errores runtime.
  });
});

test.describe("Bug #1 — negative · ruta de agente inválido aún 404 (RN-1 negative)", () => {
  // Ejerce a propósito una ruta inválida → not-found de Next esperado.
  // Gate anti-burbuja OFF porque la página NOT_FOUND no es una hoja válida.
  test.use({ viewport: DESKTOP, failOnRuntimeError: false });

  test("/{tenantId}/valeria/agenda (agente inválido) → muestra 404 (ruta muerta post-migración)", async ({
    page,
  }) => {
    test.skip(
      !process.env["E2E_BASE_URL"],
      "requiere stack dev (E2E_BASE_URL) — corre en el gate",
    );
    await page.goto(`/${TENANT_ID}/valeria/agenda`, {
      waitUntil: "domcontentloaded",
    });
    await page.waitForTimeout(2500);
    const body = (await page.locator("body").innerText()).toLowerCase();
    expect(
      body.includes("no encontramos") ||
        body.includes("no encontr") ||
        body.includes("404"),
      "valeria/agenda debe ser 404 (ruta muerta post-migración)",
    ).toBeTruthy();
  });
});
