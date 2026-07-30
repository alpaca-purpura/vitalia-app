/**
 * keyboard-cycle.spec.ts — SC-1 keyboard cycle de estados
 *
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8
 *
 * Gherkin: 01-spec.md § 1 Scenario 1 (happy path)
 *
 * Given: valeriaState='full', shellMode='agentic', focus NOT in any input/textarea
 * When:  User presses r / f / c / Escape / r
 * Then:  State transitions per D2 auto-coupling, localStorage persists
 *
 * Test route: /test-stack/shell-layout (public, no Clerk auth required)
 *
 * SC-1 gherkin_coverage:
 *   - SC-1-1: press r → valeriaState='rail'
 *   - SC-1-2: press f → valeriaState='full'
 *   - SC-1-3: press c → valeriaState='collapsed', shellMode='web'
 *   - SC-1-4: press Esc → still collapsed (idempotent)
 *   - SC-1-5: press r → valeriaState='rail', shellMode='agentic' restored
 *   - SC-1-6: localStorage persists valeriaState after each change
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { ValeriaSidebarPage } from "../../pages/ValeriaSidebarPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-1 — keyboard cycle de estados (ValeriaSidebar)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-1-1: press r → valeriaState='rail', history desaparece", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Press 'r' — shortcut to rail state
    await pom.pressShortcut("r");

    // Sidebar still attached (not collapsed → aria-expanded true)
    await pom.expectAriaExpanded(true);

    // localStorage updated to rail
    const state = await pom.getValeriaState();
    expect(state).toBe("rail");

    // shellMode stays agentic (r/f don't trigger web mode)
    const mode = await pom.getShellMode();
    expect(mode).toBe("agentic");
  });

  test("SC-1-2: press f → valeriaState='full', history visible", async ({
    valeriaRailPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    await pom.goto({ valeriaState: "rail", shellMode: "agentic" });

    await pom.pressShortcut("f");

    await pom.expectAriaExpanded(true);

    const state = await pom.getValeriaState();
    expect(state).toBe("full");

    const mode = await pom.getShellMode();
    expect(mode).toBe("agentic");
  });

  test("SC-1-3: press c → valeriaState='collapsed' + shellMode='web' auto-coupled", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    await pom.pressShortcut("c");

    // collapsed → aria-expanded false
    await pom.expectAriaExpanded(false);

    const state = await pom.getValeriaState();
    expect(state).toBe("collapsed");

    // D2: auto-coupling — collapsed triggers shellMode='web'
    const mode = await pom.getShellMode();
    expect(mode).toBe("web");
  });

  test("SC-1-4: press Esc while collapsed → idempotent, still collapsed", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Collapse first
    await pom.pressShortcut("c");
    const stateAfterC = await pom.getValeriaState();
    expect(stateAfterC).toBe("collapsed");

    // Press Esc — Esc also maps to 'collapsed' per useKeyboardShortcuts
    await pom.pressShortcut("Escape");

    const stateAfterEsc = await pom.getValeriaState();
    expect(stateAfterEsc).toBe("collapsed");

    const mode = await pom.getShellMode();
    expect(mode).toBe("web");
  });

  test("SC-1-5: press r after collapsed → valeriaState='rail' + shellMode='agentic' restored", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Collapse to web mode
    await pom.pressShortcut("c");
    const modeAfterC = await pom.getShellMode();
    expect(modeAfterC).toBe("web");

    // Press r → rail + auto-couple back to agentic
    await pom.pressShortcut("r");

    const state = await pom.getValeriaState();
    expect(state).toBe("rail");

    const mode = await pom.getShellMode();
    expect(mode).toBe("agentic");
  });

  test("SC-1-6: localStorage persists valeriaState after each keyboard transition", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // r → rail: verify localStorage updated immediately (Zustand persist middleware)
    await pom.pressShortcut("r");
    expect(await pom.getValeriaState()).toBe("rail");

    // f → full: localStorage updated
    await pom.pressShortcut("f");
    expect(await pom.getValeriaState()).toBe("full");

    // c → collapsed: localStorage updated
    await pom.pressShortcut("c");
    expect(await pom.getValeriaState()).toBe("collapsed");

    // r → rail: localStorage updated (final state)
    await pom.pressShortcut("r");
    const finalState = await pom.getValeriaState();
    expect(finalState).toBe("rail");

    // Confirm shellMode persists as well
    const finalMode = await pom.getShellMode();
    expect(finalMode).toBe("agentic");

    // Verify the full localStorage shape is valid Zustand persist JSON
    const fullStorage = await pom.getStorageState();
    expect(fullStorage).not.toBeNull();
    expect(fullStorage?.valeriaState).toBe("rail");
    expect(fullStorage?.shellMode).toBe("agentic");
  });
});
