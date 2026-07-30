/**
 * sub-tabs-invalid-subtab.spec.ts — SC-5 edge · agent válido + subtab inválido → N sub-tabs, ninguno active
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-5
 *
 * Given: usuario navega a /{tenantId}/lisa/inexistente (agent válido, subtab inválido)
 * When:  la página carga
 * Then:  4 SubTabs Lisa renderizados (no return null — agent es válido)
 * And:   NINGÚN SubTab tiene aria-selected=true
 * And:   todos los sub-tabs text-muted-foreground (inactive styling)
 * And:   sin console.error
 *
 * Esto verifica que extractSubtabFromPath retorna el segmento raw (pasthrough)
 * y SubTabsBar compara contra RIBBON_SUBTABS[activeAgent].map(s => s.id) — sin match → all inactive.
 *
 * gherkin_coverage:
 *   - SC-5: /lisa/inexistente → 4 SubTabs, ninguno active
 *   - SC-5b: /lucas/inexistente → 5 SubTabs Lucas, ninguno active
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { SubTabsBarPage } from "./poms/sub-tabs-bar-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-5 — agent válido + subtab inválido → N sub-tabs rendered, ninguno active", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-5-1: /lisa/inexistente → 4 SubTabs Lisa + ninguno active + sin errores", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    const pageErrors: string[] = [];
    shellPage.on("pageerror", (err) => {
      pageErrors.push(err.message);
    });

    await pom.goto({
      tenantId: TENANT_ID,
      agent: "lisa",
      subtab: "inexistente",
    });

    // Lisa is a valid agent — SubTabsBar should render 4 sub-tabs (NOT return null)
    expect(await pom.isPresent()).toBe(true);
    expect(await pom.getSubTabCount()).toBe(4);
    expect(await pom.getAriaLabel()).toBe("Sub-secciones Lisa");

    // No sub-tab should be active (subtab segment doesn't match any RIBBON_SUBTABS.lisa[].id)
    const activeId = await pom.getActiveSubTabId();
    expect(activeId).toBeNull();

    // Verify each Lisa sub-tab is inactive
    for (const id of ["marca", "doctores", "servicios", "compliance"]) {
      await expect(pom.getSubTab(id)).toHaveAttribute("aria-selected", "false");
      await expect(pom.getSubTab(id)).toHaveAttribute("data-active", "false");
    }

    // No errors
    expect(pageErrors).toHaveLength(0);
  });

  test("SC-5-2: /lucas/inexistente → 5 SubTabs Lucas + ninguno active", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({
      tenantId: TENANT_ID,
      agent: "lucas",
      subtab: "inexistente",
    });

    expect(await pom.isPresent()).toBe(true);
    expect(await pom.getSubTabCount()).toBe(5);
    expect(await pom.getAriaLabel()).toBe("Sub-secciones Lucas");

    const activeId = await pom.getActiveSubTabId();
    expect(activeId).toBeNull();

    for (const id of [
      "lanzar",
      "envuelo",
      "recursos",
      "resultados",
      "mercado",
    ]) {
      await expect(pom.getSubTab(id)).toHaveAttribute("aria-selected", "false");
    }
  });
});
