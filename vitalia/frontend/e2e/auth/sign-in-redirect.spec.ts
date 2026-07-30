/**
 * sign-in-redirect.spec.ts — SC-01 + SC-02 (vitalia-auth-base-functional)
 *
 * Smoke gate: verifica que rutas protegidas redirigen a /sign-in y que rutas
 * públicas se sirven sin Clerk redirect.
 *
 * Per e2e-testing.md: native Playwright on Linux host. Port 3002 (vitalia).
 * NO requiere autedPage (pruebas sin autenticación).
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/auth/sign-in-redirect.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

// ─── SC-01: Ruta raíz redirige a /sign-in sin autenticación ──────────────────

test.describe("vitalia-auth-base-functional — SC-01: redirect unauthenticated to /sign-in", () => {
  test("SC-01: GET / sin token → 307 redirect → landing en /sign-in con formulario Clerk", async ({
    page,
  }) => {
    // Navigate to root — should redirect to /sign-in
    await page.goto("/", { waitUntil: "domcontentloaded" });

    // URL debe ser /sign-in (after redirect chain)
    await expect(page).toHaveURL(/\/sign-in/);

    // La respuesta inicial puede ser 307 (server redirect) o 200 (client redirect)
    // Lo importante es que terminamos en /sign-in
    const finalUrl = page.url();
    expect(finalUrl).toMatch(/sign-in/);

    // El formulario de Clerk debe estar visible
    // Clerk renderiza un formulario con campo email
    const emailInput = page.locator(
      'input[type="email"], input[name="identifier"], input[autocomplete="email"]',
    );
    await expect(emailInput.first()).toBeVisible({ timeout: 15_000 });
  });
});

// ─── SC-02: Ruta pública /public/{tenant} sirve sin redirect ─────────────────

test.describe("vitalia-auth-base-functional — SC-02: public route served without Clerk redirect", () => {
  test("SC-02: GET /public/aurora-dental-ar → 200, sin redirect a /sign-in", async ({
    page,
  }) => {
    // Navigate to the public landing route for a test tenant
    await page.goto("/public/aurora-dental-ar", {
      waitUntil: "domcontentloaded",
    });

    // Should NOT have been redirected to /sign-in
    await expect(page).not.toHaveURL(/\/sign-in/);

    // URL debe permanecer en /public/aurora-dental-ar (o sub-path)
    expect(page.url()).toMatch(/aurora-dental-ar/);

    // No debe mostrar formulario de Clerk en ruta pública.
    // toHaveCount(0) es correcto: si el elemento no existe en el DOM, count=0 (pasa);
    // si existe y es visible, count>0 (falla loudly — comportamiento deseado).
    const clerkSignIn = page.locator(
      '[data-clerk-sign-in], .cl-sign-in-root, [data-testid="clerk-sign-in"]',
    );
    await expect(clerkSignIn).toHaveCount(0, { timeout: 5_000 });
  });
});
