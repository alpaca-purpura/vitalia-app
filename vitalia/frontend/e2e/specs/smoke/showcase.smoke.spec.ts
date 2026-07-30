// canon: design-system-canon.md §5 · story-origin: core-ds-foundation
/**
 * showcase.smoke.spec.ts — E2E smoke (anti-burbuja) para /showcase
 *
 * Story: core-ds-foundation
 * Ticket: T-9
 *
 * /showcase = catálogo público del design-system @luana/ui-kit (R-FID durable).
 * Sin tenant, sin PHI, sin auth — ruta pública (ver src/proxy.ts isPublicRoute).
 *
 * Cubre:
 *   - La página renderiza sin burbuja de error de Next (fixture base.ts assert
 *     pageerror/console-error/hidratación + overlay nextjs-portal ausente).
 *   - Las 5 secciones del canon montan con su heading visible.
 *
 * Network: ninguna llamada al backend — EntityPicker usa searchFn stub en memoria.
 * Auth: NINGUNA — ruta pública. Importa `test`/`expect` de fixtures/base (NO
 *   de @playwright/test) para activar el gate anti-burbuja.
 *
 * Ejecución nativa (NUNCA make e2e):
 *   cd vitalia/frontend
 *   E2E_BASE_URL=http://localhost:3002 npx playwright test \
 *     --project=smoke e2e/specs/smoke/showcase.smoke.spec.ts
 *
 * downstream-regression-na: brand-local E2E smoke spec; no cross-brand consumers
 */

import { test, expect } from "../../fixtures/base";

test.describe("/showcase smoke", () => {
  test("renderiza el catálogo @luana/ui-kit sin burbuja de error", async ({
    page,
  }) => {
    await page.goto("/showcase");

    // Header de la página presente
    await expect(
      page.getByRole("heading", { name: /Design System/i }),
    ).toBeVisible({ timeout: 15_000 });

    // Las 5 secciones del canon montan (por data-testid)
    await expect(page.getByTestId("showcase-section-atoms")).toBeVisible();
    await expect(page.getByTestId("showcase-section-layout")).toBeVisible();
    await expect(page.getByTestId("showcase-section-entity")).toBeVisible();
    await expect(page.getByTestId("showcase-section-autosave")).toBeVisible();
    await expect(page.getByTestId("showcase-section-archetypes")).toBeVisible();

    // Heading conocido de la primera sección
    await expect(
      page.getByRole("heading", { name: /Átomos/i }),
    ).toBeVisible();

    // El gate anti-burbuja del fixture base.ts asserta en teardown:
    // sin pageerror / console-error / overlay nextjs-portal.
  });
});
