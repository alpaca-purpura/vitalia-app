/**
 * sub-tabs-mobile-overflow.spec.ts — SC-6 edge · overflow-x-auto en viewport angosto
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-6
 *
 * Given: viewport 375x667 (mobile) + usuario en /{tenantId}/lucas/lanzar (5 sub-tabs)
 * When:  la página carga
 * Then:  SubTabsBar container tiene overflow-x-auto (sub-tabs scrollan horizontalmente)
 * And:   todos los 5 sub-tabs de Lucas están en el DOM (no ocultos/truncados)
 * And:   Lanzar sub-tab es el active
 *
 * SC-6 verifica que el container CSS handles overflow-x-auto correctamente
 * (el contenido scrollable no está recortado en mobile).
 *
 * gherkin_coverage:
 *   - SC-6: mobile 375 + Lucas 5 sub-tabs → overflow-x-auto scrollable
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { SubTabsBarPage } from "./poms/sub-tabs-bar-page.pom";

const MOBILE_VIEWPORT = { width: 375, height: 667 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-6 — mobile viewport + sub-tabs overflow-x-auto", () => {
  test.use({ viewport: MOBILE_VIEWPORT });

  test("SC-6-1: mobile 375 + Lucas/lanzar (5 sub-tabs) → all sub-tabs in DOM + overflow container", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lucas", subtab: "lanzar" });

    // SubTabsBar must be present
    expect(await pom.isPresent()).toBe(true);

    // All 5 Lucas sub-tabs must be in DOM (overflow-x-auto — not hidden by clipping)
    expect(await pom.getSubTabCount()).toBe(5);

    // Container must have overflow-x-auto class (CSS horizontal scroll)
    const bar = pom.getSubTabsBar();
    await expect(bar).toHaveClass(/overflow-x-auto/);

    // Container must have min-h-[42px] (Q4 cement)
    await expect(bar).toHaveClass(/min-h-\[42px\]/);

    // Lanzar should be active
    await expect(pom.getSubTab("lanzar")).toHaveAttribute(
      "data-active",
      "true",
    );

    // All 5 sub-tabs are in DOM (even if scrolled out of view)
    for (const id of [
      "lanzar",
      "envuelo",
      "recursos",
      "resultados",
      "mercado",
    ]) {
      await expect(pom.getSubTab(id)).toBeAttached();
    }
  });

  test("SC-6-2: mobile 375 + Lisa/marca (4 sub-tabs) → scrollable container + Marca active", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    expect(await pom.isPresent()).toBe(true);
    expect(await pom.getSubTabCount()).toBe(4);

    const bar = pom.getSubTabsBar();
    await expect(bar).toHaveClass(/overflow-x-auto/);

    await expect(pom.getSubTab("marca")).toHaveAttribute("data-active", "true");
  });
});
