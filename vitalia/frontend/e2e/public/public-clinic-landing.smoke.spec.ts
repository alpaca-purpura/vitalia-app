/**
 * public-clinic-landing.spec.ts — SC-01 landing pública carga sin auth
 * cap: public_landing.public-clinic-landing
 *
 * Verifica que la ruta /public/{slug} es accesible sin sesión Clerk activa
 * y que la página renderiza (middleware la lista como pública en proxy.ts).
 *
 * WRITE-thin honesto: no hay fixture de clínica real (3-clinic-fixture-latam
 * está pendiente de la Fase 2). Se verifica la ruta con slug placeholder.
 * Scope limitado — NO verifica datos reales de clínica (requiere fixture).
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/public/public-clinic-landing.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 * verification_method: dev-app (public route, no auth required)
 */

import { test, expect } from "@playwright/test";

const SLUG = "aurora-dental-ba";
const PUBLIC_ROUTE = `/public/${SLUG}`;

test.describe("public-clinic-landing — ruta pública sin auth", () => {
  test("SC-01: /public/{slug} carga sin redirección a /sign-in (ruta pública)", async ({
    page,
  }) => {
    // Navegar sin sesión Clerk activa
    await page.goto(PUBLIC_ROUTE, { waitUntil: "domcontentloaded" });

    // No debe redirigir a /sign-in (es ruta pública en proxy.ts)
    expect(page.url()).not.toContain("/sign-in");

    // La página debe tener un <main> con aria-label
    const main = page.locator("main");
    await expect(main).toBeVisible({ timeout: 10_000 });

    // El slug debe aparecer en la página (página renderiza el slug del parámetro)
    await expect(page.getByText(SLUG)).toBeVisible({ timeout: 5_000 });
  });

  test("SC-01b: /public/{slug} responde con contenido sin cabecera Authorization", async ({
    page,
  }) => {
    // Interceptar la respuesta de la ruta pública
    const response = await page.goto(PUBLIC_ROUTE, {
      waitUntil: "domcontentloaded",
    });

    // La ruta debe responder con 200 (no 302/307 a sign-in)
    expect(response?.status()).toBe(200);
  });
});
