/**
 * a11y-smoke.spec.ts — SC-14 (vitalia-auth-base-functional)
 *
 * Axe-core accessibility scan contra páginas vitalia.
 * Falla si hay violaciones con impacto "critical" o "serious".
 *
 * Páginas escaneadas (sin autenticación):
 *   - /sign-in
 *   - /sign-up
 *   - /onboarding/wizard
 *
 * NOTE F1-S9 T-5: bloque "Dashboard autenticado" removido.
 * La ruta / (dashboard) fue eliminada. El coverage a11y para shell-organism
 * vive en e2e/regression/vitalia-fase1-routing-shell/a11y-keyboard-nav.spec.ts.
 *
 * Per e2e-testing.md: native Playwright on Linux host. Port 3002 (vitalia).
 * Ejecuta en project=a11y (Desktop Chrome) — ver playwright.config.ts.
 *
 * Prerequisito: @axe-core/playwright instalado (ver package.json devDependencies).
 *
 * Run (post-deploy LIVE):
 *   cd vitalia/frontend && E2E_BASE_URL=https://dev-app.vitalialat.com \
 *     npx playwright test e2e/a11y/a11y-smoke.spec.ts --project=a11y
 *
 * Run (local pre-deploy):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/a11y/a11y-smoke.spec.ts --project=a11y
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// ─── Rutas públicas: /sign-in, /sign-up, /onboarding/wizard ──────────────────

const PUBLIC_PATHS = ["/sign-in", "/sign-up", "/onboarding/wizard"] as const;

test.describe("SC-14 — A11y axe smoke (vitalia-auth-base-functional)", () => {
  for (const pagePath of PUBLIC_PATHS) {
    test(`SC-14 ${pagePath} pasa axe critical+serious`, async ({ page }) => {
      await page.goto(pagePath, { waitUntil: "domcontentloaded" });

      // Esperar a que la página esté estable antes del escaneo
      await page.waitForLoadState("networkidle").catch(() => {
        // networkidle puede fallar en entornos con polling; continuamos
      });

      const results = await new AxeBuilder({ page })
        // Excluir iframes de terceros (Clerk widget usa iframe interno)
        // Excluir solo los iframes de Clerk (widget de auth usa iframe interno en dev mode).
        // Excluir todos los iframes globalmente ocultaría violaciones en iframes propios.
        .exclude({ selector: 'iframe[src*="clerk"]' })
        .analyze();

      const criticalOrSerious = results.violations.filter((v) =>
        (["critical", "serious"] as Array<string>).includes(v.impact ?? ""),
      );

      expect(
        criticalOrSerious,
        `Violaciones axe critical/serious en ${pagePath}:\n${JSON.stringify(criticalOrSerious, null, 2)}`,
      ).toHaveLength(0);
    });
  }
});
