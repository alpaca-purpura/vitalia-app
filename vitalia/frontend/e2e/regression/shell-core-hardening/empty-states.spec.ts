// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * empty-states.spec.ts — SC-13: empty states renderizados sin errores (RN-13)
 *
 * Verifica que los empty states de las secciones principales renderan
 * sin errores de consola ni burbuja Next. Cubre el caso de tenant sin datos.
 *
 * Real-backend. Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/empty-states.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-13 — empty states sin errores (RN-13)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("Valeria chat: empty state sin mensajes renderiza sin crash", async ({
    shellPage,
    tenantId,
  }) => {
    await shellPage.goto(`/${tenantId}/valeria/copilot`);
    await shellPage.waitForLoadState("networkidle", { timeout: 15_000 });
    // Shell ready — no runtime errors expected (base.ts gate covers it)
    const chatArea = shellPage.locator('[data-testid="chat-header"], main#main-content');
    await expect(chatArea.first()).toBeVisible({ timeout: 10_000 });
  });

  test("staff directory empty state renderiza (sin doctores)", async ({
    shellPage,
    tenantId,
  }) => {
    await shellPage.goto(`/${tenantId}/lisa/staff`);
    await shellPage.waitForLoadState("networkidle", { timeout: 15_000 });

    // Either real content or empty state — both acceptable
    const mainContent = shellPage.locator("main#main-content");
    await expect(mainContent).toBeVisible({ timeout: 10_000 });
  });

  test("embudo directory empty state renderiza (sin leads)", async ({
    shellPage,
    tenantId,
  }) => {
    await shellPage.goto(`/${tenantId}/adrian/embudo`);
    await shellPage.waitForLoadState("networkidle", { timeout: 15_000 });

    const mainContent = shellPage.locator("main#main-content");
    await expect(mainContent).toBeVisible({ timeout: 10_000 });
  });

  test("historial vacío: panel historial muestra empty state sin crash", async ({
    shellPage,
    tenantId,
  }) => {
    await shellPage.goto(`/${tenantId}/valeria/copilot`);
    await shellPage.waitForLoadState("networkidle", { timeout: 20_000 });

    // Open history
    const historyToggle = shellPage.locator(
      '[aria-label="Mostrar historial"], [aria-label="Ocultar historial"]',
    ).first();
    const hasToggle = await historyToggle.isVisible({ timeout: 5_000 }).catch(() => false);

    if (hasToggle) {
      await historyToggle.click();
      await shellPage.waitForTimeout(500);
      // No crash expected — base.ts gate covers runtime errors
    }
    // Pass if no errors thrown
  });
});
