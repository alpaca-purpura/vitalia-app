/**
 * bug2-tenant-selector-visible.spec.ts — Bug #2: el selector de tenant se ve
 * siempre que el usuario tenga ≥1 tenant (aunque sea 1). RN-2 ·
 * gherkin bug2_tenant_selector_visible_single_tenant.
 *
 * Fix (2 capas):
 *   1. useStoreHydration(useTenantStore) en ShellOrganismLayoutClient — restaura
 *      el activeTenant persistido (warm start).
 *   2. useTenants apunta al endpoint REAL del BE: GET /api/v1/iam/users/me/tenants
 *      (core/luana-core-iam). El path viejo /api/tenants NO existe en el BE → 404
 *      → lista vacía → TenantSwitcher oculto. ESTO es lo que rompía el selector en
 *      el stack real (cold start), y lo que el e2e viejo enmascaraba al sembrar un
 *      activeTenant vía storageState (trampa verificación-real-≠-200).
 *
 * COLD-START HONESTO: este test LIMPIA el activeTenant persistido antes de navegar,
 * forzando el fetch real a /me/tenants (forwarded al BE :8002 por la fixture). El
 * selector SOLO aparece si ese fetch puebla availableTenants → auto-pick. Si el
 * path del fetch regresara a /api/tenants (404), el selector quedaría oculto y este
 * test FALLA — que es exactamente la señal que el e2e viejo no daba.
 *
 *   NOTA: el negativo "0 tenants → selector oculto" NO se reproduce honestamente
 *   contra el BE real (el usuario autenticado posee 1 tenant). Se cubre en Vitest
 *   (fe_unit_shell). Ruta de prueba: lucas/lanzar (placeholder limpio, sin /api 4xx
 *   propios) → gate anti-burbuja ON por defecto.
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import {
  test,
  expect,
  TENANT_ID,
} from "../../fixtures/real-backend-forward.fixture";

const DESKTOP = { width: 1280, height: 720 };

test.describe("Bug #2 — tenant selector visible with 1 tenant (RN-2)", () => {
  test.use({ viewport: DESKTOP });

  test("cold-start (sin activeTenant persistido) → el fetch real a /me/tenants puebla el selector", async ({
    page,
  }) => {
    test.skip(
      !process.env["E2E_BASE_URL"],
      "requiere stack dev (E2E_BASE_URL) — corre en el gate",
    );

    // COLD START honesto: limpiar el activeTenant persistido antes de cualquier
    // render → el selector solo puede aparecer si el fetch real /me/tenants
    // puebla availableTenants (auto-pick en el store). Sin esto, el storageState
    // sembraría activeTenant y el test pasaría sin ejercer el contrato real.
    await page.addInitScript(() => {
      try {
        localStorage.removeItem("vitalia-tenant-state");
      } catch {
        /* localStorage no disponible — ignorar */
      }
    });

    // Ruta limpia (placeholder, sin /api 4xx propios) → gate anti-burbuja ON
    // por defecto (heredado de base.ts vía la fixture).
    await page.goto(`/${TENANT_ID}/lucas/lanzar`, {
      waitUntil: "domcontentloaded",
    });

    await expect(
      page.getByTestId("tenant-switcher-trigger"),
      "el selector debe poblarse desde el fetch real /me/tenants (no desde persistencia)",
    ).toBeVisible({ timeout: 15_000 });
    // El gate anti-burbuja (teardown base.ts) confirma cero errores runtime +
    // cero /api/ 4xx (lucas/lanzar limpio + /me/tenants 200).
  });
});
