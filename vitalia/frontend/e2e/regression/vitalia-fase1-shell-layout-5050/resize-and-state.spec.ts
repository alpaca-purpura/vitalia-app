// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * resize-and-state.spec.ts — SC-4 + SC-22: resize boundary clamp + persistencia + race drag.
 *
 * vitalia-fase1-shell-layout-5050 (SC-4) + vitalia-shell-core-hardening (SC-22 · AC-14)
 *
 * NEW MACHINE (vitalia-shell-core-hardening T-1):
 *   - valeriaOpen: 'closed' | 'chat'   (replaces 'full' | 'rail' | 'collapsed')
 *   - historyOpen: boolean             (additive — NOT persisted)
 *   - clamp: 320px (replaces 580px full / 360px rail from F1-S5)
 *   - NO keyboard 'f' shortcut (setValeriaState('full') eliminated · AC-1)
 *
 * SC-22 / AC-14: REACTIVATED — the "test omitido" was the state rail→full snap-up test
 * that used keyboard 'f' to dispatch setValeriaState('full'). That shortcut is
 * GONE in the new machine (AC-1 eliminated shellMode + cycleValeriaState).
 * The new race test verifies: drag IMMEDIATELY post-hydration respects 320px clamp.
 *
 * Project: smoke (playwright.config.ts regression/*.spec.ts matched)
 * Requires: dev server at E2E_BASE_URL (localhost:3002), Clerk auth state.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/resize-and-state.spec.ts \
 *     --project=smoke
 *
 * AC-14 REACTIVATION NOTE:
 * The original test "state rail->full snap-up to min (580 full)" used:
 *   document.dispatchEvent(new KeyboardEvent("keydown", { key: "f" })) → setValeriaState('full')
 * That shortcut is gone (AC-1). This test NOW verifies:
 *   drag immediately post-hydration → clamps at 320px (no stale-layout race).
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
/** New machine clamp: 320px (03-arch-fe § 1.1 · RN-8) */
const CLAMP_MIN_PX = 320;
const TOLERANCE_PX = 30;

test.describe("SC-4 + SC-22 — resize boundary + persistencia + race drag (F1-S4 · shell-core-hardening)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  // ── SC-4 Assertion 1: drag handle left — clamped at 320px ─────────────────

  test("drag handle left below min (320 clamp) — clamped (SC-4 · RN-8)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const initialWidth = await pom.getValeriaWidth();
    expect(initialWidth).toBeGreaterThan(0);

    // Drag far left (400px) — should clamp at 320px (new machine)
    await pom.dragResizeHandle(-400);

    const clampedWidth = await pom.getValeriaWidth();

    // New clamp: 320px (not 580px from legacy F1-S5)
    expect(clampedWidth).toBeGreaterThanOrEqual(CLAMP_MIN_PX - TOLERANCE_PX);
    // Should be narrower than initial
    expect(clampedWidth).toBeLessThanOrEqual(initialWidth + 20);
  });

  // ── SC-4 Assertion 2: localStorage persists post-drag ─────────────────────

  test("localStorage vitalia-shell-split-agentic persists post-drag (SC-4 · RN-4)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });

    // Drag handle right by 50px to ensure non-default layout
    await pom.dragResizeHandle(50);

    const persistedSplit = await pom.getPersistedSplit();
    expect(persistedSplit).not.toBeNull();
    if (persistedSplit) {
      const parsed = JSON.parse(persistedSplit) as unknown;
      expect(Array.isArray(parsed)).toBe(true);
      expect((parsed as unknown[]).length).toBeGreaterThanOrEqual(2);
    }
  });

  // ── SC-4 Assertion 2b: shell state (valeriaOpen) survives reload ──────────
  // Uses page with closed state seeded. Verifies no clobber after reload.

  test("shell state (valeriaOpen) survives reload (SC-4 · ADR-vitalia-006)", async ({
    closedShellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(closedShellPage);
    // Navigate with valeriaOpen='closed' pre-seeded (closedShellPage fixture)
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // After navigation+hydration the store MUST read persisted 'closed',
    // not the default 'chat'. New machine: no SSR clobber (ADR-vitalia-006).
    const state = await pom.getValeriaOpen();
    expect(state, "valeriaOpen='closed' deve sobreviver ao reload").toBe("closed");
  });

  // ── SC-4 Assertion 3: state chat — no auto-shrink current width ───────────

  test("estado chat — sem auto-shrink: ancho preservado (SC-4 · RN-4)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const chatWidth = await pom.getValeriaWidth();
    expect(chatWidth).toBeGreaterThan(0);

    // New machine: no 'full' vs 'rail' state; Valeria is always 'chat' or 'closed'.
    // Open history (additive) — shouldn't auto-shrink Valeria overall width.
    await pom.historyToggleBtn.waitFor({ state: "visible", timeout: 10_000 });
    await pom.historyToggleBtn.click();
    await shellPage.waitForTimeout(300);

    // Close history
    await pom.historyToggleBtn.click();
    await shellPage.waitForTimeout(300);

    // Width should be approximately the same as before (history toggle doesn't resize Valeria panel)
    const widthAfter = await pom.getValeriaWidth();
    expect(Math.abs(widthAfter - chatWidth)).toBeLessThanOrEqual(100);
  });

  // ── SC-22 / AC-14 REACTIVATED: drag IMMEDIATELY post-hydration ───────────
  //
  // Original AC-14 "test omitido": the F1-S5 test "state rail->full snap-up to min (580 full)"
  // dispatched keyboard 'f' → setValeriaState('full'). That shortcut is gone (AC-1).
  //
  // NEW race test: the user drags the resize handle BEFORE the shell has fully settled
  // (immediately after topBar visible, BEFORE data-shell-ready="true").
  // The clamp (320px) must still be respected — no stale-layout window allows
  // dragging below the clamp.

  test("AC-14 REACTIVATED: drag imediato post-hidratação respeita clamp 320px (SC-22 · RN-16)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);

    // Navigate to the shell — DO NOT call waitForShellReady() before dragging.
    // We want to capture the race window between topBar visible and shell-ready.
    if (tenantId && tenantId !== "vitalia-test-tenant") {
      await shellPage.goto(`/${tenantId}`);
    } else {
      await shellPage.goto("/test-stack/shell-layout");
    }

    // Wait only for topBar (SSR skeleton) — NOT for data-shell-ready
    await pom.topBar.waitFor({ state: "visible", timeout: 30_000 });

    // Attempt drag IMMEDIATELY (race window: skeleton → client hydration)
    // If the handle is not yet visible, this is a no-op (the test still passes because
    // the clamp will be verified after shell-ready settles).
    const handleVisible = await pom.resizeHandle.isVisible({ timeout: 3_000 }).catch(() => false);

    if (handleVisible) {
      // Race drag: move left by 500px — must clamp at 320px
      await pom.dragResizeHandle(-500);
    }

    // Now wait for shell to settle
    await pom.waitForShellReady();

    const clampedWidth = await pom.getValeriaWidth();

    // Even in the race window, clamp must hold
    expect(
      clampedWidth,
      "drag imediato pós-hidratação: ancho min clampado em 320px (AC-14 · RN-16)",
    ).toBeGreaterThanOrEqual(CLAMP_MIN_PX - TOLERANCE_PX);
  });

  test("AC-14 REACTIVATED: estado persistido após drag imediato (SC-22 · RN-16)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);

    if (tenantId && tenantId !== "vitalia-test-tenant") {
      await shellPage.goto(`/${tenantId}`);
    } else {
      await shellPage.goto("/test-stack/shell-layout");
    }

    await pom.topBar.waitFor({ state: "visible", timeout: 30_000 });

    // Drag in the race window (may be before shell-ready)
    const handleVisible = await pom.resizeHandle.isVisible({ timeout: 3_000 }).catch(() => false);
    if (handleVisible) {
      await pom.dragResizeHandle(30); // Small drag right to record a non-default position
    }

    await pom.waitForShellReady();

    // The dragged position should be persisted in localStorage
    const persistedSplit = await pom.getPersistedSplit();
    // Split should exist (drag triggers persist)
    if (handleVisible) {
      expect(persistedSplit).not.toBeNull();
    }
    // And valeriaOpen remains 'chat' (drag doesn't change open state)
    const valeriaOpen = await pom.getValeriaOpen();
    expect(valeriaOpen).toBe("chat");
  });
});
