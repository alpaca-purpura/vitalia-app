/**
 * sub-tabs-nav.spec.ts — SC-1 happy · click sub-tab navega a nueva ruta
 *
 * F1-S8 vitalia-fase1-sub-tabs-line2 — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-1
 *
 * Given: usuario en /{tenantId}/lisa/marca, Marca sub-tab active
 * When:  click sub-tab Doctores
 * Then:  URL → /{tenantId}/lisa/doctores + Doctores sub-tab data-active=true + bg-agent-lisa-soft
 * And:   Marca sub-tab data-active=false + text-muted-foreground
 *
 * gherkin_coverage:
 *   - SC-1: click Doctores desde active=marca → URL /lisa/doctores + Doctores active
 *   - SC-1-camila: click Reactivar desde active=voz → URL /camila/reactivar + Reactivar active
 *   - SC-1-valeria: click Pacientes desde active=agenda → URL /valeria/pacientes (2 sub-tabs mínimo)
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { SubTabsBarPage } from "./poms/sub-tabs-bar-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-1 — click sub-tab navega a nueva ruta (sub-tabs)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-1-1: click Doctores desde Lisa/marca → URL /lisa/doctores + Doctores active", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "lisa", subtab: "marca" });

    // Verify initial active sub-tab
    const initialActive = await pom.getActiveSubTabId();
    expect(initialActive).toBe("marca");

    // SubTabsBar nav should be labeled for Lisa
    const ariaLabel = await pom.getAriaLabel();
    expect(ariaLabel).toBe("Sub-secciones Lisa");

    // Lisa has 4 sub-tabs
    const count = await pom.getSubTabCount();
    expect(count).toBe(4);

    // Click Doctores
    await pom.clickSubTab("doctores");

    // URL should change to /{tenantId}/lisa/doctores
    await shellPage.waitForURL(`**/${TENANT_ID}/lisa/doctores`, {
      timeout: 10_000,
    });

    // Doctores should be active
    await expect(pom.getSubTab("doctores")).toHaveAttribute(
      "data-active",
      "true",
    );
    await expect(pom.getSubTab("doctores")).toHaveAttribute(
      "aria-selected",
      "true",
    );

    // Marca should be inactive
    await expect(pom.getSubTab("marca")).toHaveAttribute(
      "data-active",
      "false",
    );
    await expect(pom.getSubTab("marca")).toHaveAttribute(
      "aria-selected",
      "false",
    );
  });

  test("SC-1-2: click Reactivar desde Camila/voz → URL /camila/reactivar + Reactivar active", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "camila", subtab: "voz" });

    // Camila has 4 sub-tabs
    const count = await pom.getSubTabCount();
    expect(count).toBe(4);

    const ariaLabel = await pom.getAriaLabel();
    expect(ariaLabel).toBe("Sub-secciones Camila");

    // Click Reactivar
    await pom.clickSubTab("reactivar");

    await shellPage.waitForURL(`**/${TENANT_ID}/camila/reactivar`, {
      timeout: 10_000,
    });

    await expect(pom.getSubTab("reactivar")).toHaveAttribute(
      "data-active",
      "true",
    );
    await expect(pom.getSubTab("voz")).toHaveAttribute("data-active", "false");
  });

  test("SC-1-3: click Pacientes desde Valeria/agenda → URL /valeria/pacientes (caso mínimo 2 sub-tabs)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "valeria", subtab: "agenda" });

    // Valeria has 2 sub-tabs (caso mínimo)
    const count = await pom.getSubTabCount();
    expect(count).toBe(2);

    const ariaLabel = await pom.getAriaLabel();
    expect(ariaLabel).toBe("Sub-secciones Valeria");

    await pom.clickSubTab("pacientes");

    await shellPage.waitForURL(`**/${TENANT_ID}/valeria/pacientes`, {
      timeout: 10_000,
    });

    await expect(pom.getSubTab("pacientes")).toHaveAttribute(
      "data-active",
      "true",
    );
    await expect(pom.getSubTab("agenda")).toHaveAttribute(
      "data-active",
      "false",
    );
  });

  test("SC-1-4: click Config sub-tab Conexiones desde Config/cuenta → URL /config/conexiones (neutral styling)", async ({
    shellPage,
  }) => {
    const pom = new SubTabsBarPage(shellPage);

    await pom.goto({ tenantId: TENANT_ID, agent: "config", subtab: "cuenta" });

    // Config has 3 sub-tabs
    const count = await pom.getSubTabCount();
    expect(count).toBe(3);

    const ariaLabel = await pom.getAriaLabel();
    expect(ariaLabel).toBe("Sub-secciones Configuración");

    await pom.clickSubTab("conexiones");

    await shellPage.waitForURL(`**/${TENANT_ID}/config/conexiones`, {
      timeout: 10_000,
    });

    await expect(pom.getSubTab("conexiones")).toHaveAttribute(
      "data-active",
      "true",
    );
    await expect(pom.getSubTab("cuenta")).toHaveAttribute(
      "data-active",
      "false",
    );
  });
});
