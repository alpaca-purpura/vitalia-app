// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * history-from-closed.spec.ts — SC-7: abrir historial desde estado A → B+C (RN-6 · RN-7)
 *
 * RN-6: abrir historial desde A (cerrado) también abre Valeria.
 * Transición A→C: si Valeria está cerrada y el usuario abre historial,
 * Valeria se abre Y el historial se muestra (estado B+C).
 *
 * Real-backend (no mocks). Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/history-from-closed.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-7 — historial desde estado A → B+C (RN-6 · RN-7)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("abrir historial desde A reabre Valeria (A → B+C)", async ({
    closedShellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(closedShellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Confirm we start in closed state (A)
    const valeriaOpen = await pom.getValeriaOpen();
    expect(valeriaOpen, "debe iniciar en estado A (closed)").toBe("closed");

    // Strip should be visible
    await expect(pom.collapsedStrip).toBeVisible({ timeout: 5_000 });

    // The history toggle may not be visible in closed state. RN-7 says
    // openHistory() from A also opens Valeria. This is triggered via the
    // keyboard shortcut 'f' (openHistory via ValeriaSidebar) or any
    // mechanism that calls store.openHistory().
    // In closed state, the historyToggleBtn in ChatHeader is NOT rendered.
    // We verify the state transition via store dispatch through keyboard 'f' shortcut.
    await closedShellPage.keyboard.press("f");
    await closedShellPage.waitForTimeout(500);
    await pom.waitForShellReady();

    // Both valeriaOpen=chat AND historyOpen=true
    const valeriaOpenAfter = await pom.getValeriaOpen();
    expect(valeriaOpenAfter, "RN-6: historial desde A abre Valeria (B)").toBe("chat");

    // History panel should be visible (C)
    const historyOpen = await pom.getHistoryOpen();
    expect(historyOpen, "historial debe estar visible (C)").toBe(true);
  });

  test("valeriaOpen='closed' → historyOpen forzado false (RN-5 invariant)", async ({
    closedShellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(closedShellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // In closed state, historyOpen MUST be false (RN-5 invariant)
    const historyOpen = await pom.getHistoryOpen();
    expect(historyOpen, "RN-5: en estado A historyOpen debe ser false").toBe(false);
  });
});
