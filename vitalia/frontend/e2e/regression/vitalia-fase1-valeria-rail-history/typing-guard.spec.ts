/**
 * typing-guard.spec.ts — SC-2 typing en composer NO dispara shortcuts
 *
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8
 *
 * Gherkin: 01-spec.md § 1 Scenario 2 (negative)
 *
 * Given: valeriaState='full', focus en composer (contenteditable / textarea / input)
 * When:  User types 'COMPRAR' (C and R are shortcuts)
 * Then:  Characters written normally, valeriaState unchanged, no side-effects
 *
 * SC-2 gherkin_coverage:
 *   - SC-2-1: focus in search input, type 'COMPRAR', state stays 'full'
 *   - SC-2-2: state not changed after typing C, O, M, P, R, A, R
 *   - SC-2-3: localStorage shell-store unchanged (valeriaState still 'full')
 *   - SC-2-4: Cmd+K focuses composer even when body focus (positive case)
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { ValeriaSidebarPage } from "../../pages/ValeriaSidebarPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-2 — typing guard: shortcuts suppressed when input focused", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-2-1: typing 'COMPRAR' in search input does not change valeriaState", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Click into the history search input (focus it)
    await pom.historySearch.click();
    await expect(pom.historySearch).toBeFocused();

    // Type COMPRAR — 'c' and 'r' would normally trigger collapsed/rail shortcuts
    await valeriaFullPage.keyboard.type("COMPRAR");

    // valeriaState must remain 'full' (no shortcut triggered)
    const state = await pom.getValeriaState();
    expect(state).toBe("full");
  });

  test("SC-2-2: search input retains typed text ('COMPRAR')", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    await pom.historySearch.click();
    await expect(pom.historySearch).toBeFocused();
    await valeriaFullPage.keyboard.type("COMPRAR");

    // Input retains the text (letters were NOT intercepted by shortcut handler)
    await expect(pom.historySearch).toHaveValue("COMPRAR");
  });

  test("SC-2-3: localStorage shell-store unchanged after typing in input", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    const stateBefore = await pom.getValeriaState();
    expect(stateBefore).toBe("full");

    await pom.historySearch.click();
    await valeriaFullPage.keyboard.type("COMPRAR");

    const stateAfter = await pom.getValeriaState();
    expect(stateAfter).toBe("full");

    const modeAfter = await pom.getShellMode();
    expect(modeAfter).toBe("agentic");
  });

  test("SC-2-4: Cmd+K focuses composer element (bypass shortcut)", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Cmd+K should trigger handleFocusComposer → document.getElementById('valeria-composer-placeholder').focus()
    const isMac = (
      await valeriaFullPage.evaluate(() => navigator.platform)
    ).includes("Mac");
    if (isMac) {
      await pom.pressShortcut("k", { meta: true });
    } else {
      await pom.pressShortcut("k", { ctrl: true });
    }

    // Composer placeholder should receive focus
    await expect(pom.composer).toBeFocused({ timeout: 3_000 });

    // valeriaState unchanged (Cmd+K is not a state-changing shortcut)
    const state = await pom.getValeriaState();
    expect(state).toBe("full");
  });
});
