/**
 * click-collapse.spec.ts — SC-5 click rail PanelLeftClose mientras shellMode='agentic'
 *
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8
 *
 * Gherkin: 01-spec.md § 1 Scenario 5 (edge)
 *
 * Given: valeriaState='rail', shellMode='agentic'
 * When:  User clicks PanelLeftClose button (footer rail)
 * Then:  setValeriaState('collapsed') + setShellMode('web') executed
 *        Shell transitions, chat hidden, rail visible (4 buttons MVP)
 *        Click PanelLeftOpen or press r/f → returns to agentic
 *
 * SC-5 gherkin_coverage:
 *   - SC-5-1: click collapse → valeriaState='collapsed'
 *   - SC-5-2: click collapse → shellMode='web' (D2 auto-coupling)
 *   - SC-5-3: sidebar aria-expanded=false after collapse
 *   - SC-5-4: click PanelLeftOpen → valeriaState='full', shellMode='agentic' restored
 *
 * Note: clickRailCollapseBtn() uses Locator.dispatchEvent('click') to bypass
 * the Next.js dev overlay portal that intercepts pointer events in dev mode.
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { ValeriaSidebarPage } from "../../pages/ValeriaSidebarPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

/** Wait for D2 auto-coupling effect to run (React useEffect) */
const EFFECT_WAIT_MS = 300;

test.describe("SC-5 — click collapse button transitions state", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-5-1: click PanelLeftClose → valeriaState='collapsed'", async ({
    valeriaRailPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    await pom.goto({ valeriaState: "rail", shellMode: "agentic" });

    expect(await pom.getValeriaState()).toBe("rail");

    await pom.clickRailCollapseBtn();
    await valeriaRailPage.waitForTimeout(EFFECT_WAIT_MS);

    const state = await pom.getValeriaState();
    expect(state).toBe("collapsed");
  });

  test("SC-5-2: click PanelLeftClose → shellMode='web' (D2 auto-coupling)", async ({
    valeriaRailPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    await pom.goto({ valeriaState: "rail", shellMode: "agentic" });

    await pom.clickRailCollapseBtn();
    // D2 effect: collapsed auto-sets shellMode='web' — wait for useEffect to run
    await valeriaRailPage.waitForTimeout(EFFECT_WAIT_MS);

    const mode = await pom.getShellMode();
    expect(mode).toBe("web");
  });

  test("SC-5-3: sidebar aria-expanded=false after click collapse", async ({
    valeriaRailPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    await pom.goto({ valeriaState: "rail", shellMode: "agentic" });

    await pom.clickRailCollapseBtn();
    await valeriaRailPage.waitForTimeout(EFFECT_WAIT_MS);

    // collapsed → aria-expanded=false
    await pom.expectAriaExpanded(false);
  });

  test("SC-5-4: after collapse, press r → valeriaState='rail' + shellMode='agentic' restored", async ({
    valeriaRailPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    await pom.goto({ valeriaState: "rail", shellMode: "agentic" });

    // Collapse
    await pom.clickRailCollapseBtn();
    await valeriaRailPage.waitForTimeout(EFFECT_WAIT_MS);
    expect(await pom.getValeriaState()).toBe("collapsed");

    // Press r to restore
    await pom.pressShortcut("r");
    await valeriaRailPage.waitForTimeout(EFFECT_WAIT_MS);

    const state = await pom.getValeriaState();
    expect(state).toBe("rail");

    const mode = await pom.getShellMode();
    expect(mode).toBe("agentic");

    // aria-expanded=true restored
    await pom.expectAriaExpanded(true);
  });
});
