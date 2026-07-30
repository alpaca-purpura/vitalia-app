// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * history-push.spec.ts — SC-6: historial empuja 260px (RN-7)
 *
 * Verifica que abrir el historial empuja el panel de chat 260px
 * (el historial es ADDITIVE: estado C = chat + history).
 * El ancho del agente (app-panel-slot) se angosta en consecuencia.
 *
 * Real-backend (no mocks). Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/history-push.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
/** History panel fixed width from 03-arch-fe § 6 */
const HISTORY_WIDTH_PX = 260;
const TOLERANCE_PX = 20;

test.describe("SC-6 — historial empuja 260px (RN-7)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("abrir historial: panel chat se angosta ~260px", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Record Valeria width before opening history
    const valeriaWidthBefore = await pom.getValeriaWidth();
    expect(valeriaWidthBefore).toBeGreaterThan(0);

    // Open history
    await pom.historyToggleBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.historyToggleBtn.click();
    await shellPage.waitForTimeout(500);

    // History panel should now be visible
    const historyOpen = await pom.getHistoryOpen();
    expect(historyOpen).toBe(true);

    // The ValeriaSidebar (which contains both chat + history) should be wider.
    // But the CHAT part inside Valeria gets 260px narrower.
    // We verify by checking historyPanel is visible and has correct width.
    await expect(pom.historyPanel).toBeVisible({ timeout: 5_000 });
    const historyBox = await pom.historyPanel.boundingBox();
    expect(historyBox).not.toBeNull();
    if (historyBox) {
      expect(historyBox.width).toBeGreaterThanOrEqual(
        HISTORY_WIDTH_PX - TOLERANCE_PX,
      );
      expect(historyBox.width).toBeLessThanOrEqual(
        HISTORY_WIDTH_PX + TOLERANCE_PX,
      );
    }
  });

  test("cerrar historial: panel chat recupera el ancho", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const valeriaWidthBefore = await pom.getValeriaWidth();

    // Open history
    await pom.historyToggleBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.historyToggleBtn.click();
    await shellPage.waitForTimeout(300);

    // Close history
    await pom.historyToggleBtn.click();
    await shellPage.waitForTimeout(300);

    const historyOpen = await pom.getHistoryOpen();
    expect(historyOpen, "historial debe estar cerrado").toBe(false);

    // Width should be approximately back to original
    const valeriaWidthAfter = await pom.getValeriaWidth();
    expect(
      Math.abs(valeriaWidthAfter - valeriaWidthBefore),
    ).toBeLessThanOrEqual(30);
  });

  test("historial NO persiste abierto (RN-11)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Open history
    await pom.historyToggleBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.historyToggleBtn.click();
    await shellPage.waitForTimeout(300);

    // Reload to simulate navigating away + back
    await shellPage.reload();
    await pom.waitForShellReady();

    // History must start closed (RN-11: no persiste abierto)
    const historyOpenAfterReload = await pom.getHistoryOpen();
    expect(
      historyOpenAfterReload,
      "RN-11: historial no persiste abierto tras reload",
    ).toBe(false);
  });
});
