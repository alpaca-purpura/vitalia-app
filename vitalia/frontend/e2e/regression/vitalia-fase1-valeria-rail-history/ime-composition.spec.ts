/**
 * ime-composition.spec.ts — SC-3 IME composition guard
 *
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8
 *
 * Gherkin: 01-spec.md § 1 Scenario 3 (edge)
 *
 * Given: Focus en composer textarea, IME composition active (isComposing=true)
 * When:  User accidentally presses 'r' or 'c' during composition
 * Then:  Handler skips (isComposing guard), valeriaState unchanged
 *
 * SC-3 gherkin_coverage:
 *   - SC-3-1: dispatch compositionstart + keydown(r, isComposing=true) → no state change
 *   - SC-3-2: dispatch compositionstart + keydown(c, isComposing=true) → no state change
 *
 * IME simulation strategy:
 *   - page.evaluate dispatches compositionstart, then KeyboardEvent with isComposing=true
 *   - Verifies useKeyboardShortcuts guard via e.isComposing check
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { ValeriaSidebarPage } from "../../pages/ValeriaSidebarPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-3 — IME composition guard (keyboard shortcuts suppressed)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-3-1: keydown 'r' during IME composition does not change valeriaState", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    const stateBefore = await pom.getValeriaState();
    expect(stateBefore).toBe("full");

    // Click into search input to set focus context
    await pom.historySearch.click();
    await expect(pom.historySearch).toBeFocused();

    // Simulate IME composition: compositionstart → keydown(r, isComposing=true) → compositionend
    await pom.simulateImeComposition(pom.historySearch, "r");

    // Brief wait for any potential state update
    await valeriaFullPage.waitForTimeout(100);

    // valeriaState must still be 'full' (guard blocked the 'r' shortcut)
    const stateAfter = await pom.getValeriaState();
    expect(stateAfter).toBe("full");

    const modeAfter = await pom.getShellMode();
    expect(modeAfter).toBe("agentic");
  });

  test("SC-3-2: keydown 'c' during IME composition does not trigger collapsed state", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    const stateBefore = await pom.getValeriaState();
    expect(stateBefore).toBe("full");

    // Click into search input to set focus context
    await pom.historySearch.click();
    await expect(pom.historySearch).toBeFocused();

    // Simulate IME composition with 'c' key (would normally collapse Valeria)
    await pom.simulateImeComposition(pom.historySearch, "c");

    await valeriaFullPage.waitForTimeout(100);

    // valeriaState must still be 'full' (not 'collapsed')
    const stateAfter = await pom.getValeriaState();
    expect(stateAfter).toBe("full");

    // shellMode must still be 'agentic' (not 'web' which would be set by collapse)
    const modeAfter = await pom.getShellMode();
    expect(modeAfter).toBe("agentic");
  });
});
