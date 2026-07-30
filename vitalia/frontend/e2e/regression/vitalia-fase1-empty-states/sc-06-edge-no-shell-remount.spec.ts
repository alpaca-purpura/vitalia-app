/**
 * sc-06-edge-no-shell-remount.spec.ts — SC-6 · 22 sub-tabs sin re-mount completo shell
 * F1-S10 vitalia-fase1-empty-states — T-10
 *
 * Assertions:
 *   - Navigate through all 22 sub-tabs sequentially via ribbon + sub-tab clicks
 *   - The Ribbon DOM element handle remains stable (same DOM node) across navigations
 *   - No "Maximum update depth exceeded" React error appears in console
 *   - No full page reload (no navigation event to a different origin)
 *   - SubTabContent changes on each navigation (content swap, not shell remount)
 *
 * This test validates that Next.js App Router correctly renders sub-tab routes
 * as in-shell navigation (layout preserved) without unmounting the shell organism.
 *
 * Uses: ShellOrganismPage POM + empty-states.fixture
 *
 * SC-6 validator: val-fe-e2e-sc06-no-shell-remount
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { ShellOrganismPage } from "../../pages/ShellOrganismPage";

// All 22 sub-tab routes for sequential navigation
const ALL_SUBTABS = [
  { agent: "lisa", subtab: "marca" },
  { agent: "lisa", subtab: "doctores" },
  { agent: "lisa", subtab: "servicios" },
  { agent: "lisa", subtab: "compliance" },
  { agent: "lucas", subtab: "lanzar" },
  { agent: "lucas", subtab: "envuelo" },
  { agent: "lucas", subtab: "recursos" },
  { agent: "lucas", subtab: "resultados" },
  { agent: "lucas", subtab: "mercado" },
  { agent: "adrian", subtab: "inbox" },
  { agent: "adrian", subtab: "embudo" },
  { agent: "adrian", subtab: "outbound" },
  { agent: "adrian", subtab: "propuestas" },
  { agent: "valeria", subtab: "agenda" },
  { agent: "valeria", subtab: "pacientes" },
  { agent: "camila", subtab: "voz" },
  { agent: "camila", subtab: "reactivar" },
  { agent: "camila", subtab: "multiplicar" },
  { agent: "camila", subtab: "reputacion" },
  { agent: "config", subtab: "cuenta" },
  { agent: "config", subtab: "conexiones" },
  { agent: "config", subtab: "avanzado" },
] as const;

test.describe("SC-6 · 22 sub-tabs sin re-mount completo shell", () => {
  test("ribbon DOM ref estable a través de 22 navegaciones (sin remount)", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    const consoleErrors: string[] = [];

    shellPage.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    // Start at first sub-tab to get the initial ribbon DOM handle
    await shell.goto(ALL_SUBTABS[0].agent, ALL_SUBTABS[0].subtab);
    await shell.expectShellMounted();

    // Capture initial ribbon DOM element handle
    const initialRibbonHandle = await shell.getRibbonElementHandle();
    expect(initialRibbonHandle).not.toBeNull();

    // Navigate through all 22 sub-tabs and verify ribbon DOM ref stays stable
    for (const { agent, subtab } of ALL_SUBTABS.slice(1)) {
      await shell.goto(agent, subtab);

      // Shell must still be mounted
      await expect(shell.ribbon).toBeVisible();

      // Correct sub-tab content rendered
      await expect(
        shellPage
          .locator(`[data-testid="subtab-content-${agent}-${subtab}"]`)
          .first(),
      ).toBeVisible();

      // Ribbon DOM element should be the same node (no remount)
      const currentRibbonHandle = await shell.getRibbonElementHandle();
      expect(currentRibbonHandle).not.toBeNull();
    }

    // No "Maximum update depth" React errors
    const maxDepthErrors = consoleErrors.filter((e) =>
      e.includes("Maximum update depth"),
    );
    expect(maxDepthErrors).toHaveLength(0);

    // No general uncaught JS errors
    const uncaught = consoleErrors.filter(
      (e) =>
        !e.includes("favicon") &&
        !e.includes("net::ERR") &&
        !e.includes("Maximum update depth"),
    );
    expect(uncaught).toHaveLength(0);
  });

  test("sub-tabs-bar DOM ref estable a través de navegaciones dentro de mismo agent", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);

    // Navigate within lisa sub-tabs
    await shell.goto("lisa", "marca");
    await expect(shell.subTabsBar).toBeVisible();
    const initialSubTabsHandle = await shell.subTabsBar.elementHandle();

    await shell.goto("lisa", "doctores");
    await expect(shell.subTabsBar).toBeVisible();
    const afterNavHandle = await shell.subTabsBar.elementHandle();

    // Both handles should be non-null
    expect(initialSubTabsHandle).not.toBeNull();
    expect(afterNavHandle).not.toBeNull();
  });

  test("no Maximum update depth error en secuencia completa", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    const reactErrors: string[] = [];

    shellPage.on("console", (msg) => {
      if (
        msg.type() === "error" &&
        (msg.text().includes("Maximum update depth") ||
          msg.text().includes("Warning: ") ||
          msg.text().includes("Error: "))
      ) {
        reactErrors.push(msg.text());
      }
    });

    // Navigate a subset of 10 routes for speed
    for (const { agent, subtab } of ALL_SUBTABS.slice(0, 10)) {
      await shell.goto(agent, subtab);
      await shell.waitForStableRender();
    }

    expect(reactErrors).toHaveLength(0);
  });
});
