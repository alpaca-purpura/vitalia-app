// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * default-30-70.spec.ts — SC-1: fresh load mide anchos 30/70
 *
 * RN-3: default fresh = chat 30/70 historial cerrado.
 * Verifica que en fresh load (sin estado persistido), Valeria ocupa ~30%
 * y el panel de app ~70% del espacio disponible.
 *
 * Real-backend (no mocks). Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/default-30-70.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
// Tolerance: react-resizable-panels stores percentages; pixel conversion may drift ±5%
const TOLERANCE_PCT = 0.05;

test.describe("SC-1 — default fresh load 30/70 split (RN-3)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("fresh load: Valeria ~30%, app ~70% del contenedor", async ({
    page,
    tenantId,
  }) => {
    // Clear localStorage to simulate fresh load (no saved preference)
    await page.addInitScript(() => {
      localStorage.clear();
    });

    const pom = new ShellLayoutPage(page);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const valeriaWidth = await pom.getValeriaWidth();
    const containerWidth = await pom.getMainContainerWidth();

    expect(containerWidth).toBeGreaterThan(0);
    expect(valeriaWidth).toBeGreaterThan(0);

    const valeriaPct = valeriaWidth / containerWidth;
    // RN-3: default = 30% Valeria slot
    expect(valeriaPct).toBeGreaterThanOrEqual(0.30 - TOLERANCE_PCT);
    expect(valeriaPct).toBeLessThanOrEqual(0.30 + TOLERANCE_PCT + 0.05); // +5% headroom
  });

  test("fresh load: historyOpen = false (RN-3 · historial cerrado)", async ({
    page,
    tenantId,
  }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    const pom = new ShellLayoutPage(page);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const historyOpen = await pom.getHistoryOpen();
    expect(historyOpen).toBe(false);
  });

  test("fresh load: valeriaOpen = 'chat' (B — panel visible)", async ({
    page,
    tenantId,
  }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    const pom = new ShellLayoutPage(page);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const valeriaOpen = await pom.getValeriaOpen();
    expect(valeriaOpen).toBe("chat");

    // Verify Valeria slot is visible (not collapsed strip)
    const isVisible = await pom.isValeriaSlotVisible();
    expect(isVisible).toBe(true);
  });
});
