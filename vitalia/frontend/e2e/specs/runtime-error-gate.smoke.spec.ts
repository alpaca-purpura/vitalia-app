/**
 * runtime-error-gate.smoke.spec.ts — Prueba del gate anti-burbuja (#37 §3).
 *
 * Navega rutas PÚBLICAS (sin auth) y asserta cero errores de runtime: la burbuja
 * roja de Next, errores de hidratación, console.error, 4xx-5xx en /api/, y el
 * overlay de error en el DOM. Es el smoke que demuestra que el gate funciona.
 *
 * Correr (stack levantado):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test runtime-error-gate
 *
 * Rollout: cuando un spec autenticado quiera el gate, compone base + auth con
 * `mergeTests` (ver base.ts). Acá usamos rutas públicas para no depender de Clerk.
 */
import { test, expect, expectNoNextErrorOverlay } from "../fixtures/base";

// Rutas públicas que renderizan sin sesión (landing + sign-in de Clerk).
const PUBLIC_ROUTES = ["/", "/sign-in"];

for (const route of PUBLIC_ROUTES) {
  test(`sin errores de runtime en ruta pública ${route}`, async ({ page }) => {
    const resp = await page.goto(route, { waitUntil: "domcontentloaded" });
    // El server no debe devolver 5xx (la página debe servir, incluso si redirige a sign-in).
    expect(
      resp?.status() ?? 0,
      `${route} debe servir sin 5xx`,
    ).toBeLessThan(500);
    // Dar tiempo a la hidratación para que un error de cliente aflore.
    await page.waitForLoadState("networkidle").catch(() => {});
    await expectNoNextErrorOverlay(page);
    // El fixture asserta pageErrors / hydration / console / failedApi vacíos al teardown.
  });
}
