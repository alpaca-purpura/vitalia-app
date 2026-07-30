/**
 * visual-smoke.spec.ts — SC-16 (vitalia-auth-base-functional)
 *
 * Baseline de screenshots para regresión visual.
 * Umbrales maxDiffPixelRatio:
 *   - /sign-in y /sign-up: 0.05 (5%) — Clerk vendor UI renderiza con alta consistencia;
 *     captcha y avatares se enmascaran (mask[]); tolerancia baja es intencional.
 *   - /test-stack/: 0.05 (5%) — páginas de prueba de diseño determinísticas.
 *
 * IMPORTANTE: Las screenshots de referencia se generan en la PRIMERA ejecución LIVE
 * por /pm-vitalia post-deploy (npx playwright test --update-snapshots).
 * Runs subsiguientes comparan contra ese baseline.
 *
 * Páginas (sin autenticación):
 *   - /sign-in → signin.png
 *   - /sign-up → signup.png
 *
 * Nota F1-S9: La página autenticada legacy / (dashboard) fue eliminada en T-5.
 * La nueva landing post-login es /{tenantId}/mateo/agenda (shell-organism · UPDATED v1.2 paradigm-map-zones T-6).
 * El visual baseline para shell-organism se cubre en
 * e2e/regression/vitalia-fase1-routing-shell/happy-navigation.spec.ts.
 *
 * Ejecuta en project=smoke (Desktop Chrome) — ver playwright.config.ts.
 * No requiere project dedicado; usa misma configuración que smoke base.
 *
 * Run para GENERAR baseline (primera vez — requiere app corriendo):
 *   cd vitalia/frontend && E2E_BASE_URL=https://dev-app.vitalialat.com \
 *     npx playwright test e2e/visual/visual-smoke.spec.ts --update-snapshots
 *
 * Run para VERIFICAR contra baseline:
 *   cd vitalia/frontend && E2E_BASE_URL=https://dev-app.vitalialat.com \
 *     npx playwright test e2e/visual/visual-smoke.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

// ─── SC-16: Páginas públicas — visual baseline ───────────────────────────────

test.describe("SC-16 — Visual baseline (vitalia-auth-base-functional)", () => {
  test("SC-16 /sign-in baseline screenshot", async ({ page }) => {
    await page.goto("/sign-in", { waitUntil: "domcontentloaded" });

    // Esperar que el formulario Clerk esté renderizado
    await page
      .waitForSelector("input[type='email'], input[name='identifier'], form", {
        timeout: 10_000,
      })
      .catch(() => {
        // Si Clerk no renderiza el input en este entorno (mock), continuar
      });

    // Ocultar elementos dinámicos para screenshot estable
    await page.addStyleTag({
      content: `
        /* Suprimir animaciones para screenshot determinístico */
        *, *::before, *::after {
          animation-duration: 0ms !important;
          animation-delay: 0ms !important;
          transition-duration: 0ms !important;
          transition-delay: 0ms !important;
        }
      `,
    });

    await expect(page).toHaveScreenshot("signin.png", {
      // 0.05: Clerk vendor UI renderiza consistentemente; captcha/avatar enmascarados.
      maxDiffPixelRatio: 0.05,
      // Mask elementos que cambian entre runs (timestamps, avatares dinámicos)
      mask: [
        page.locator('[data-testid="clerk-captcha"]'),
        page.locator('[aria-label="captcha"]'),
      ],
    });
  });

  test("SC-16 /sign-up baseline screenshot", async ({ page }) => {
    await page.goto("/sign-up", { waitUntil: "domcontentloaded" });

    await page
      .waitForSelector(
        "input[type='email'], input[name='emailAddress'], form",
        {
          timeout: 10_000,
        },
      )
      .catch(() => {});

    await page.addStyleTag({
      content: `
        *, *::before, *::after {
          animation-duration: 0ms !important;
          animation-delay: 0ms !important;
          transition-duration: 0ms !important;
          transition-delay: 0ms !important;
        }
      `,
    });

    await expect(page).toHaveScreenshot("signup.png", {
      // 0.05: Clerk vendor UI renderiza consistentemente; captcha/avatar enmascarados.
      maxDiffPixelRatio: 0.05,
      mask: [
        page.locator('[data-testid="clerk-captcha"]'),
        page.locator('[aria-label="captcha"]'),
      ],
    });
  });
});

// NOTE F1-S9: El bloque "Dashboard autenticado" fue removido en T-5 legacy cleanup.
// La ruta / (dashboard) ya no existe. La nueva landing autenticada es
// /{tenantId}/mateo/agenda (shell-organism · UPDATED v1.2 paradigm-map-zones T-6).
// El coverage visual autenticado vive en:
//   e2e/regression/vitalia-fase1-routing-shell/happy-navigation.spec.ts
