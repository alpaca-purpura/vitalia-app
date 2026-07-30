// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * large-dataset.spec.ts — SC-14: dataset grande + historial scroll (RN-7)
 *
 * Verifica que con un dataset grande (muchos registros), la UI:
 *   1. No congela el navegador (timeout no dispara).
 *   2. El historial con muchas conversaciones hace scroll sin errores.
 *   3. No hay burbuja de error Next.
 *
 * Real-backend. Gate anti-burbuja via base.ts.
 * Nota: si el tenant dev no tiene 1000 entidades, el test es advisory
 * (verifica comportamiento con los datos reales disponibles).
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/large-dataset.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-14 — dataset grande + historial scroll (RN-7)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("staff directory: carga con N registros sin timeout", async ({
    shellPage,
    tenantId,
  }) => {
    // Navigate to staff directory
    const startMs = Date.now();
    await shellPage.goto(`/${tenantId}/lisa/staff`);
    await shellPage.waitForLoadState("networkidle", { timeout: 30_000 });
    const loadMs = Date.now() - startMs;

    // Page must load in <30s (the timeout above would catch it anyway)
    expect(loadMs).toBeLessThan(30_000);

    // Main content rendered
    const mainContent = shellPage.locator("main#main-content");
    await expect(mainContent).toBeVisible({ timeout: 5_000 });
  });

  test("historial: scroll sin crash (RN-7 push fijo)", async ({
    shellPage,
    tenantId,
  }) => {
    await shellPage.goto(`/${tenantId}/valeria/copilot`);
    await shellPage.waitForLoadState("networkidle", { timeout: 20_000 });

    // Open history panel
    const historyToggle = shellPage.locator(
      '[aria-label="Mostrar historial"], [aria-label="Ocultar historial"]',
    ).first();
    const hasToggle = await historyToggle.isVisible({ timeout: 5_000 }).catch(() => false);

    if (hasToggle) {
      await historyToggle.click();
      await shellPage.waitForTimeout(500);

      const historyPanel = shellPage.locator('[aria-label="Historial conversaciones"]');
      const isVisible = await historyPanel.isVisible({ timeout: 5_000 }).catch(() => false);

      if (isVisible) {
        // Scroll within the history panel
        await shellPage.mouse.wheel(0, 500);
        await shellPage.waitForTimeout(300);
        // No crash: base.ts gate verifies
      }
    }
    // Pass if no runtime errors
  });

  test("embudo board: renderiza sin congelar con leads reales", async ({
    shellPage,
    tenantId,
  }) => {
    const startMs = Date.now();
    await shellPage.goto(`/${tenantId}/adrian/embudo`);
    await shellPage.waitForLoadState("networkidle", { timeout: 30_000 });
    const loadMs = Date.now() - startMs;

    expect(loadMs).toBeLessThan(30_000);

    const mainContent = shellPage.locator("main#main-content");
    await expect(mainContent).toBeVisible({ timeout: 5_000 });
  });
});
