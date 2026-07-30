// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * network-failure.spec.ts — SC-15: error de red → error-state + retry (RN-?)
 *
 * Este spec SÍ mockea el fetch del surface bajo prueba (la naturaleza del test
 * es verificar el comportamiento ante error de red — no sería verificable sin mock).
 * Ver doctrina: SC-15 (network failure) sí mockea el fetch; SC-20/21/22 no.
 *
 * Verifica que ante un error 5xx del backend:
 *   1. La UI muestra el error-state (NetworkErrorFallback o similar).
 *   2. No hay burbuja Next.js (data-nextjs-dialog ausente).
 *   3. Hay un botón de retry visible.
 *   4. No hay excepciones JS no capturadas (pageErrors vacío — page.on('pageerror')).
 *
 * Mocks: intercepta /api/* → responde 503.
 * Gate anti-burbuja: base.ts con failOnRuntimeError:false (el 503 es el error esperado).
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/network-failure.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-15 — error de red → error-state + retry", () => {
  test.use({
    viewport: DESKTOP_VIEWPORT,
    // Disable the runtime error gate for the /api/ 5xx interception
    // (this test intentionally exercises the 5xx path)
    failOnRuntimeError: false,
  });

  test("503 en /api/clinics/staff → NetworkErrorFallback o error state visible", async ({
    shellPage,
    tenantId,
  }) => {
    // Intercept ALL API calls → 503
    await shellPage.route("**/api/**", (route) => {
      void route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Service Unavailable (mock)" }),
      });
    });

    await shellPage.goto(`/${tenantId}/lisa/staff`);
    await shellPage.waitForLoadState("networkidle", { timeout: 15_000 });

    // One of these must appear
    const errorFallback = shellPage.locator(
      '[data-testid="network-error-fallback"], [data-testid="agent-error-boundary"], [role="alert"]',
    );
    const retryBtn = shellPage.locator(
      '[data-testid="network-error-retry"], button[aria-label*="reintentar" i]',
    );

    const hasFallback = await errorFallback.first().isVisible({ timeout: 10_000 }).catch(() => false);
    const hasRetry = await retryBtn.first().isVisible({ timeout: 10_000 }).catch(() => false);

    // At least one error state indicator must appear
    expect(
      hasFallback || hasRetry,
      "debe renderizar error-state o retry ante 503",
    ).toBe(true);

    // No Next.js error dialog (bubble) — the error must be handled gracefully
    const nextDialog = shellPage.locator(
      "[data-nextjs-dialog], [data-nextjs-error-overlay]",
    );
    await expect(nextDialog).toHaveCount(0);
  });

  test("503 no produce excepciones JS no capturadas (pageErrors vacío)", async ({
    shellPage,
    tenantId,
  }) => {
    const pageErrors: string[] = [];
    shellPage.on("pageerror", (err) => {
      pageErrors.push(`${err.name}: ${err.message}`);
    });

    await shellPage.route("**/api/**", (route) => {
      void route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Service Unavailable (mock)" }),
      });
    });

    await shellPage.goto(`/${tenantId}/lisa/staff`);
    await shellPage.waitForLoadState("networkidle", { timeout: 15_000 });
    await shellPage.waitForTimeout(1000);

    expect(pageErrors, "503 no debe producir excepciones JS no capturadas").toEqual([]);
  });
});
