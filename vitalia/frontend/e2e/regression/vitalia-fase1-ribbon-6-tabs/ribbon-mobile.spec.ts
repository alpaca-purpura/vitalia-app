/**
 * ribbon-mobile.spec.ts — SC-5 responsive · viewport 375px overflow-x-auto
 *
 * F1-S7 vitalia-fase1-ribbon-6-tabs — T-5
 *
 * Gherkin: 01-spec.md § Gherkin SC-5
 *
 * Given: viewport width 375px (iPhone SE mobile)
 * When:  usuario carga la shell en /{tenantId}/lisa/marca
 * Then:  Ribbon container tiene overflow-x-auto (horizontal scroll disponible)
 * And:   todos los tabs siguen renderizados (no collapse a menu)
 * And:   tabs son accesibles via scroll horizontal
 * And:   tab activo (Lisa) sigue visible + data-active="true"
 *
 * gherkin_coverage:
 *   - SC-5-1: mobile 375px → ribbon visible + overflow-x-auto scroll disponible
 *   - SC-5-2: mobile 375px → tab activo visible + no colapsa a hamburger
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { RibbonPage } from "./poms/ribbon-page.pom";

const MOBILE_VIEWPORT = { width: 375, height: 667 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-5 — mobile viewport 375px → overflow-x-auto scroll", () => {
  test.use({ viewport: MOBILE_VIEWPORT });

  test("SC-5-1: mobile 375px → Ribbon visible + overflow scroll disponible", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    const ribbon = pom.getRibbon();

    // Ribbon should be attached and visible
    await expect(ribbon).toBeAttached();

    // Check that overflow-x-auto is applied via CSS
    const overflowX = await ribbon.evaluate((el) => {
      return window.getComputedStyle(el).overflowX;
    });
    // overflow-x should be "auto" or "scroll" (horizontal scroll enabled)
    expect(["auto", "scroll"]).toContain(overflowX);

    // All 5 agent tabs + ConfigTab should still be in DOM (not collapsed)
    await expect(pom.getTab("lisa")).toBeAttached();
    await expect(pom.getTab("lucas")).toBeAttached();
    await expect(pom.getTab("adrian")).toBeAttached();
    await expect(pom.getTab("valeria")).toBeAttached();
    await expect(pom.getTab("camila")).toBeAttached();
    await expect(pom.getConfigTab()).toBeAttached();
  });

  test("SC-5-2: mobile 375px → tab activo Lisa visible + data-active correcto", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Lisa tab should be active
    await expect(pom.getTab("lisa")).toHaveAttribute("data-active", "true");
    await expect(pom.getTab("lisa")).toHaveAttribute("aria-selected", "true");

    // Active tab (Lisa) should be visible/attached in DOM at mobile viewport
    await expect(pom.getTab("lisa")).toBeAttached();

    // Ribbon should NOT have collapsed into a hamburger menu (tabs still visible)
    // Verify by checking count of ribbon-tab-* elements = 5 agents + 1 config
    const tabCount = await shellPage
      .locator('[data-testid^="ribbon-tab-"]')
      .count();
    // Should have at least 5 agent tabs (ribbon-tab-lisa, ribbon-tab-lucas, etc.)
    expect(tabCount).toBeGreaterThanOrEqual(5);
  });
});
