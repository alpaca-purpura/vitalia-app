/**
 * sub-tabs-agent-change.spec.ts — SC-2 happy · cambio de agente re-renderiza SubTabsBar
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-2
 *
 * Given: usuario en /{tenantId}/lisa/doctores (Lisa active, 4 SubTabs Lisa)
 * When:  click RibbonTab Lucas (F1-S7)
 * Then:  URL → /{tenantId}/lucas/lanzar
 * And:   SubTabsBar re-renderiza 5 SubTabs Lucas
 * And:   Lanzar sub-tab es el active por defecto
 * And:   nav aria-label cambia a 'Sub-secciones Lucas'
 *
 * gherkin_coverage:
 *   - SC-2: lisa → lucas agent change: sub-tabs count 4→5 + aria-label actualizado
 *   - SC-2b: lucas → config: sub-tabs count 5→3 + neutral styling Config
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { SubTabsBarPage } from "./poms/sub-tabs-bar-page.pom";
import { RibbonPage } from "../vitalia-fase1-ribbon-6-tabs/poms/ribbon-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-2 — cambio de agente re-renderiza SubTabsBar con nuevos sub-tabs", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-2-1: lisa → lucas → SubTabsBar 4 sub-tabs Lisa re-renders 5 sub-tabs Lucas + aria-label updated", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);
    const ribbonPom = new RibbonPage(shellPage);

    // Start at lisa/doctores
    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "doctores" });

    // Verify Lisa 4 sub-tabs initial
    expect(await pom.getSubTabCount()).toBe(4);
    expect(await pom.getAriaLabel()).toBe("Sub-secciones Lisa");

    // Click Lucas tab on Ribbon (F1-S7 integration)
    await ribbonPom.clickTab("lucas");

    // URL should change to /lucas/lanzar
    await shellPage.waitForURL(`**/${TENANT_ID}/lucas/lanzar`, {
      timeout: 10_000,
    });

    // Wait for SubTabsBar to re-render with Lucas
    await shellPage.waitForSelector('[data-testid="sub-tabs-bar"]', {
      state: "attached",
      timeout: 8_000,
    });

    // SubTabsBar should now have 5 sub-tabs (Lucas)
    expect(await pom.getSubTabCount()).toBe(5);
    expect(await pom.getAriaLabel()).toBe("Sub-secciones Lucas");

    // Lanzar should be the default active sub-tab
    const activeId = await pom.getActiveSubTabId();
    expect(activeId).toBe("lanzar");
  });

  test("SC-2-2: lucas → config → SubTabsBar 5 sub-tabs Lucas re-renders 3 sub-tabs Config (neutral)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);
    const ribbonPom = new RibbonPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lucas", subtab: "lanzar" });

    expect(await pom.getSubTabCount()).toBe(5);

    // Click Config tab on Ribbon
    await ribbonPom.clickConfigTab();

    await shellPage.waitForURL(`**/${TENANT_ID}/config/cuenta`, {
      timeout: 10_000,
    });

    await shellPage.waitForSelector('[data-testid="sub-tabs-bar"]', {
      state: "attached",
      timeout: 8_000,
    });

    expect(await pom.getSubTabCount()).toBe(3);
    expect(await pom.getAriaLabel()).toBe("Sub-secciones Configuración");

    const activeId = await pom.getActiveSubTabId();
    expect(activeId).toBe("cuenta");
  });
});
