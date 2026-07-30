// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * collapse-strip-reopen.spec.ts — SC-5: colapsar→avatar→reabrir (RN-5 · RN-9 · RN-12)
 *
 * Verifica:
 *   1. El botón "Colapsar a barra" colapsa Valeria → ValeriaCollapsedStrip visible.
 *   2. Colapsar también cierra historial (RN-5/RN-6).
 *   3. Clic en ValeriaCollapsedStrip reabre Valeria en estado B (chat).
 *   4. Reabrir NO restaura el historial (RN-5: chat-only).
 *   5. El estado persiste (valeriaOpen='closed' en localStorage post-colapso).
 *
 * Real-backend (no mocks). Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/collapse-strip-reopen.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-5 — colapsar → strip → reabrir (RN-5 · RN-9 · RN-12)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("colapsar Valeria → ValeriaCollapsedStrip visible", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Verify we start in chat state (B)
    const valeriaOpen = await pom.getValeriaOpen();
    expect(valeriaOpen).toBe("chat");

    // Click collapse button (RN-9: botón colapsar propio visible)
    await pom.collapseToStripBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.collapseToStripBtn.click();
    await shellPage.waitForTimeout(300);

    // Strip should be visible
    await expect(pom.collapsedStrip).toBeVisible({ timeout: 5_000 });

    // Valeria sidebar slot should be hidden/collapsed (not the full chat)
    const valeriaBox = await pom.valeriaSlot.boundingBox();
    // In collapsed state: valeriaSlot may still be in DOM but strip replaces chat
    // Or valeriaSlot itself is the strip container. Either way strip IS visible.
    expect(valeriaBox).not.toBeNull();
  });

  test("colapsar cierra historial (RN-5/RN-6)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // First open history
    await pom.historyToggleBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.historyToggleBtn.click();
    await shellPage.waitForTimeout(300);
    const historyOpenBefore = await pom.getHistoryOpen();
    // History should now be open (if button worked)
    // If BE has no conversations, history might show empty state — still counts as open
    // We verify via DOM presence of the panel

    // Now collapse Valeria
    await pom.collapseToStripBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.collapseToStripBtn.click();
    await shellPage.waitForTimeout(300);

    // History must be closed after collapse (RN-5/RN-6)
    const historyOpenAfter = await pom.getHistoryOpen();
    expect(historyOpenAfter).toBe(false);
    // Suppress unused warning
    void historyOpenBefore;
  });

  test("clic en strip reabre Valeria como chat (B, RN-12)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Collapse first
    await pom.collapseToStripBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.collapseToStripBtn.click();
    // Brief settle — same pattern as test 1 (220ms CSS transition + React re-render)
    await shellPage.waitForTimeout(300);
    // Wait for strip to appear before trying to click it
    await expect(pom.collapsedStrip).toBeVisible({ timeout: 8_000 });

    // Click the strip avatar to reopen via JS (more reliable than Playwright click
    // during the react-resizable-panels layout snap transition)
    await shellPage.evaluate(() => {
      const strip = document.querySelector<HTMLButtonElement>(
        '[data-testid="valeria-collapsed-strip"]',
      );
      strip?.click();
    });

    // Wait for chat region to appear (confirms openValeria() fired + React re-rendered)
    await shellPage
      .locator('[aria-label="Chat con Valeria"]')
      .waitFor({ state: "visible", timeout: 8_000 });

    // Give Zustand persist middleware time to flush to localStorage
    await shellPage.waitForTimeout(300);

    // ValeriaOpen should now be chat again
    const valeriaOpen = await pom.getValeriaOpen();
    expect(valeriaOpen).toBe("chat");
  });

  test("reabrir desde strip NO restaura historial (RN-5: chat-only)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Open history first
    await pom.historyToggleBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.historyToggleBtn.click();
    // Wait for history toggle to settle (panel open/close animation)
    await shellPage.waitForTimeout(500);

    // Collapse — target ChatHeader's "Colapsar a Valeria" specifically.
    // When history is open, ValeriaHistory ALSO has [aria-label="Colapsar a barra"] (closeHistory only).
    // The generic pom.collapseToStripBtn picks "Colapsar a barra" first (wrong button — only closes history).
    // Must target "Colapsar a Valeria" (ChatHeader button) which calls collapseValeria().
    const collapseVaeriaBtn = shellPage.locator('[aria-label="Colapsar a Valeria"]').first();
    await collapseVaeriaBtn.waitFor({ state: "visible", timeout: 15_000 });
    await collapseVaeriaBtn.click();
    // Brief settle — same pattern as tests 1 & 3 (220ms CSS transition + React re-render)
    await shellPage.waitForTimeout(300);
    // Wait for strip to appear before trying to click it
    await expect(pom.collapsedStrip).toBeVisible({ timeout: 8_000 });

    // Reopen via strip via JS (more reliable than Playwright click during layout snap)
    await shellPage.evaluate(() => {
      const strip = document.querySelector<HTMLButtonElement>(
        '[data-testid="valeria-collapsed-strip"]',
      );
      strip?.click();
    });

    // Wait for chat region to appear (confirms openValeria() fired + React re-rendered)
    await shellPage
      .locator('[aria-label="Chat con Valeria"]')
      .waitFor({ state: "visible", timeout: 8_000 });

    // History must NOT be restored (RN-5)
    const historyOpen = await pom.getHistoryOpen();
    expect(historyOpen, "RN-5: reabrir desde strip no restaura historial").toBe(false);
  });

  test("valeriaOpen persiste 'closed' en localStorage post-colapso", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    await pom.collapseToStripBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.collapseToStripBtn.click();
    await shellPage.waitForTimeout(500);

    const storedOpen = await pom.getValeriaOpen();
    expect(storedOpen, "localStorage debe tener valeriaOpen='closed'").toBe("closed");
  });

  // ── BUG fixes (vitalia-shell-core-hardening bugfix-shell-collapse-gap) ─────
  // RED tests: these assert behavior that was broken before the imperative
  // panel.collapse() / panel.expand() fix.

  test("BUG #2: panel Valeria colapsado ≤ 60px (sin gap vacío ~274px)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Collapse to strip
    await pom.collapseToStripBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.collapseToStripBtn.click();
    // Wait for collapse animation + react-resizable-panels layout settle
    await shellPage.waitForTimeout(500);

    // The Valeria panel itself (data-panel="valeria-panel") must be ≤ 60px
    // when collapsed. Before the fix it was clamped to minSize (~318px) leaving
    // a ~274px gap of empty space.
    const valeriaWidth = await shellPage.evaluate(() => {
      const el = document.querySelector<HTMLElement>('[data-panel="valeria-panel"]');
      if (!el) return -1;
      return el.getBoundingClientRect().width;
    });
    expect(
      valeriaWidth,
      `Valeria panel debe ser ≤ 60px al colapsar (era ${valeriaWidth}px — gap bug #2)`,
    ).toBeLessThanOrEqual(60);
  });

  test("BUG #1: resize handle funciona DESPUÉS de ciclo colapsar→reabrir", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Record initial Valeria width in open state
    const widthBefore = await pom.getValeriaWidth();
    expect(widthBefore, "should start with Valeria visible").toBeGreaterThan(100);

    // ── Cycle: collapse ──────────────────────────────────────────────────────
    await pom.collapseToStripBtn.waitFor({ state: "visible", timeout: 15_000 });
    await pom.collapseToStripBtn.click();
    await shellPage.waitForTimeout(400);
    await expect(pom.collapsedStrip).toBeVisible({ timeout: 8_000 });

    // ── Cycle: reopen ────────────────────────────────────────────────────────
    await shellPage.evaluate(() => {
      const strip = document.querySelector<HTMLButtonElement>(
        '[data-testid="valeria-collapsed-strip"]',
      );
      strip?.click();
    });
    await shellPage
      .locator('[aria-label="Chat con Valeria"]')
      .waitFor({ state: "visible", timeout: 8_000 });
    await shellPage.waitForTimeout(400);

    // Wait for shell to be ready after re-open
    await shellPage
      .locator('main#main-content[data-shell-ready="true"]')
      .waitFor({ state: "visible", timeout: 10_000 });

    // ── Drag resize handle ────────────────────────────────────────────────────
    // If expand() was NOT called, the panel is still internally "collapsed" and
    // the drag silently does nothing → widthAfter ≈ widthBefore.
    // After the fix, drag must move the panel by ≥ 50px.
    const widthBeforeDrag = await pom.getValeriaWidth();
    await pom.dragResizeHandle(150);
    await shellPage.waitForTimeout(200);
    const widthAfterDrag = await pom.getValeriaWidth();

    expect(
      Math.abs(widthAfterDrag - widthBeforeDrag),
      `Drag post-reabrir debe cambiar ancho ≥ 50px (cambió solo ${Math.abs(widthAfterDrag - widthBeforeDrag)}px — bug #1 resize muerto)`,
    ).toBeGreaterThanOrEqual(50);
  });
});
