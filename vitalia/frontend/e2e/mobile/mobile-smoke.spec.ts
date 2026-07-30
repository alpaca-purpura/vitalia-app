/**
 * mobile-smoke.spec.ts — SC-15 (vitalia-auth-base-functional)
 *
 * Smoke de viewport móvil contra páginas vitalia (iPhone 13: 390×844).
 * Verifica:
 *   - Sin scroll horizontal (scrollWidth ≤ viewportWidth + 1px tolerancia)
 *   - Targets táctiles ≥ 44px de alto (botón primario)
 *   - Contenido visible y renderizable
 *
 * NOTE F1-S9 T-5: bloque "Dashboard autenticado en móvil" removido.
 * La ruta / (dashboard) fue eliminada. El coverage mobile para shell-organism
 * vive en e2e/regression/vitalia-fase1-routing-shell/.
 *
 * Ejecuta en project=mobile (iPhone 13) — ver playwright.config.ts.
 *
 * Run (post-deploy LIVE):
 *   cd vitalia/frontend && E2E_BASE_URL=https://dev-app.vitalialat.com \
 *     npx playwright test e2e/mobile/mobile-smoke.spec.ts --project=mobile
 *
 * Run (local pre-deploy):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/mobile/mobile-smoke.spec.ts --project=mobile
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

// ─── Helper: verificar ausencia de scroll horizontal ─────────────────────────

async function assertNoHorizontalScroll(
  page: import("@playwright/test").Page,
): Promise<void> {
  const scrollWidth = await page.evaluate(() => document.body.scrollWidth);
  const viewportWidth = await page.evaluate(() => window.innerWidth);
  // Tolerancia de 1px por variaciones de renderizado sub-pixel
  expect(scrollWidth).toBeLessThanOrEqual(
    viewportWidth + 1,
    `Scroll horizontal detectado: scrollWidth=${scrollWidth} > viewportWidth=${viewportWidth}`,
  );
}

// ─── Helper: verificar target táctil ≥ 44px de alto ─────────────────────────

async function assertPrimaryButtonTappable(
  page: import("@playwright/test").Page,
): Promise<void> {
  // Buscar el botón principal de acción (sign-in, submit, etc.)
  const btn = page
    .getByRole("button", { name: /iniciar|sign|continue|siguiente|acceder/i })
    .first();
  const isVisible = await btn.isVisible().catch(() => false);

  if (isVisible) {
    const box = await btn.boundingBox();
    if (box !== null) {
      expect(box.height).toBeGreaterThanOrEqual(
        44,
        `Botón primario demasiado pequeño para touch: height=${box.height}px (mínimo 44px)`,
      );
    }
  }
  // Si no hay botón principal visible, el test no falla (página puede ser redirect)
}

// ─── SC-15: Páginas públicas en móvil ────────────────────────────────────────

test.describe("SC-15 — Mobile smoke iPhone 13 (vitalia-auth-base-functional)", () => {
  test("SC-15 /sign-in renderiza sin scroll horizontal y con botón táctil ≥44px", async ({
    page,
  }) => {
    await page.goto("/sign-in", { waitUntil: "domcontentloaded" });

    // Sin scroll horizontal
    await assertNoHorizontalScroll(page);

    // Botón primario táctil
    await assertPrimaryButtonTappable(page);

    // Formulario visible (algún input de texto)
    const inputs = page.locator(
      "input[type='email'], input[type='text'], input[type='password']",
    );
    const inputCount = await inputs.count();
    expect(inputCount).toBeGreaterThan(0);
  });

  test("SC-15 /sign-up renderiza sin scroll horizontal", async ({ page }) => {
    await page.goto("/sign-up", { waitUntil: "domcontentloaded" });

    await assertNoHorizontalScroll(page);

    // Algún input visible
    const inputs = page.locator(
      "input[type='email'], input[type='text'], input[type='password']",
    );
    const inputCount = await inputs.count();
    expect(inputCount).toBeGreaterThan(0);
  });

  test("SC-15 /onboarding/wizard renderiza sin scroll horizontal en móvil", async ({
    page,
  }) => {
    // El wizard puede requerir auth — si redirige a /sign-in, es comportamiento válido
    await page.goto("/onboarding/wizard", { waitUntil: "domcontentloaded" });

    // Aceptar: la página cargó (posiblemente redirigida a /sign-in)
    const currentUrl = page.url();
    const isOnWizard = currentUrl.includes("/onboarding/wizard");
    const isOnSignIn = currentUrl.includes("/sign-in");

    expect(isOnWizard || isOnSignIn).toBeTruthy();

    // Sin scroll horizontal en la página que efectivamente cargó
    await assertNoHorizontalScroll(page);
  });
});
