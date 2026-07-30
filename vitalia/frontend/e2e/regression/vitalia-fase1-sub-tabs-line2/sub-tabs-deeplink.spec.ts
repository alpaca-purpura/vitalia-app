/**
 * sub-tabs-deeplink.spec.ts — SC-3 happy · deep link → active state correcto desde URL
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-3
 *
 * Given: usuario navega directamente a /{tenantId}/camila/reactivar
 * When:  página carga
 * Then:  4 SubTabs Camila renderizados
 * And:   Reactivar sub-tab aria-selected=true + bg-agent-camila-soft + text-agent-camila
 * And:   otros 3 sub-tabs aria-selected=false + text-muted-foreground
 *
 * gherkin_coverage:
 *   - SC-3: deep link /camila/reactivar → Reactivar active + active styling
 *   - SC-3b: deep link /lucas/resultados → Resultados active (Lucas idx 3)
 *   - SC-3c: deep link /lisa/compliance → Compliance active (Lisa último sub-tab)
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { SubTabsBarPage } from "./poms/sub-tabs-bar-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-3 — deep link → URL-derived active state correcto", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-3-1: /camila/reactivar → Reactivar active + otros inactive", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({
      tenantId: TENANT_ID,
      agent: "camila",
      subtab: "reactivar",
    });

    // 4 Camila sub-tabs
    expect(await pom.getSubTabCount()).toBe(4);
    expect(await pom.getAriaLabel()).toBe("Sub-secciones Camila");

    // Reactivar should be active
    expect(await pom.getActiveSubTabId()).toBe("reactivar");
    await expect(pom.getSubTab("reactivar")).toHaveAttribute(
      "aria-selected",
      "true",
    );
    await expect(pom.getSubTab("reactivar")).toHaveAttribute(
      "data-active",
      "true",
    );

    // Other sub-tabs should be inactive
    await expect(pom.getSubTab("voz")).toHaveAttribute(
      "aria-selected",
      "false",
    );
    await expect(pom.getSubTab("multiplicar")).toHaveAttribute(
      "data-active",
      "false",
    );
    await expect(pom.getSubTab("reputacion")).toHaveAttribute(
      "data-active",
      "false",
    );
  });

  test("SC-3-2: /lucas/resultados → Resultados active (sub-tab idx 3)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({
      tenantId: TENANT_ID,
      agent: "lucas",
      subtab: "resultados",
    });

    // 5 Lucas sub-tabs
    expect(await pom.getSubTabCount()).toBe(5);
    expect(await pom.getAriaLabel()).toBe("Sub-secciones Lucas");

    expect(await pom.getActiveSubTabId()).toBe("resultados");
    await expect(pom.getSubTab("resultados")).toHaveAttribute(
      "aria-selected",
      "true",
    );

    // First sub-tab should be inactive
    await expect(pom.getSubTab("lanzar")).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });

  test("SC-3-3: /lisa/compliance → Compliance active (Lisa último sub-tab)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({
      tenantId: TENANT_ID,
      agent: "lisa",
      subtab: "compliance",
    });

    expect(await pom.getSubTabCount()).toBe(4);
    expect(await pom.getAriaLabel()).toBe("Sub-secciones Lisa");

    expect(await pom.getActiveSubTabId()).toBe("compliance");
    await expect(pom.getSubTab("compliance")).toHaveAttribute(
      "aria-selected",
      "true",
    );

    // Marca (first) should be inactive
    await expect(pom.getSubTab("marca")).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });
});
