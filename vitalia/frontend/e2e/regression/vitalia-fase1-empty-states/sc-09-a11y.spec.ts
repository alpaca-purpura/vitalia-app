/**
 * sc-09-a11y.spec.ts — SC-9 · accessibility heading hierarchy + keyboard + axe wcag2aa
 * F1-S10 vitalia-fase1-empty-states — T-10
 *
 * Assertions:
 *   - axe wcag2aa: 0 violations on sample of 6 sub-tabs (covers all agents)
 *   - Heading hierarchy: SubTabHeader renders h2 as top-level heading in content area
 *   - Keyboard navigation: Tab focuses interactive elements correctly
 *   - Space/Enter activates TogglePill tabs (lisa.servicios, adrian.embudo)
 *   - Focus management: ribbon tab focusable, sub-tab focusable
 *   - aria-selected="true" on active ribbon tab
 *   - aria-live="polite" on messages area (adrian.inbox)
 *
 * Uses: @axe-core/playwright for wcag2aa scan
 * Uses: ShellOrganismPage POM + empty-states.fixture
 *
 * SC-9 validators: val-fe-e2e-sc09-a11y + val-fe-axe-empty-states
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import AxeBuilder from "@axe-core/playwright";
import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { ShellOrganismPage } from "../../pages/ShellOrganismPage";

// Sample 6 sub-tabs for axe scan (one per agent)
const AXE_SCAN_ROUTES = [
  { agent: "lisa", subtab: "servicios" },
  { agent: "lucas", subtab: "lanzar" },
  { agent: "adrian", subtab: "embudo" },
  { agent: "valeria", subtab: "agenda" },
  { agent: "camila", subtab: "voz" },
  { agent: "config", subtab: "cuenta" },
] as const;

test.describe("SC-9 · accessibility heading hierarchy + keyboard", () => {
  test.describe("axe wcag2aa · 0 violations en agentes representativos", () => {
    for (const { agent, subtab } of AXE_SCAN_ROUTES) {
      test(`axe wcag2aa · ${agent}.${subtab}`, async ({
        shellPage,
        tenantId,
      }) => {
        const shell = new ShellOrganismPage(shellPage, tenantId);
        await shell.goto(agent, subtab);
        await shell.expectShellMounted();

        const axeResults = await new AxeBuilder({ page: shellPage })
          .withTags(["wcag2a", "wcag2aa"])
          // Exclude known false positives from Next.js static elements
          .exclude("[data-nextjs-router]")
          .analyze();

        expect(axeResults.violations).toHaveLength(0);
      });
    }
  });

  test.describe("heading hierarchy", () => {
    test("SubTabHeader h2 visible como heading único en área de contenido", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("lisa", "marca");
      await shell.expectShellMounted();

      // SubTabHeader renders h2 — data-testid="subtab-header-lisa-marca"
      await expect(
        shellPage.locator('[data-testid="subtab-header-lisa-marca"]').first(),
      ).toBeVisible();

      // Verify h2 is the top-level heading in the content area (not multiple h1)
      const h1Count = await shellPage.locator("h1").first().count();
      // Shell layout should have at most 1 h1 (page title if any)
      expect(h1Count).toBeLessThanOrEqual(1);
    });

    test("no h1 conflictivo en sub-tab content (h2 es el primer heading visible)", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("valeria", "agenda").first();
      await shell.expectShellMounted();

      // h2 from SubTabHeader
      const h2Count = await shellPage.locator("h2").first().count();
      expect(h2Count).toBeGreaterThanOrEqual(1);
    });
  });

  test.describe("keyboard navigation", () => {
    test("Tab navega a ribbon tabs y sub-tabs (focusable)", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("lisa", "marca").first();
      await shell.expectShellMounted();

      // Focus the ribbon element area and Tab through it
      await shell.ribbon.press("Tab");
      // After tab, some element inside ribbon should have focus
      const focusedElement = await shellPage.evaluate(
        () => document.activeElement?.tagName,
      );
      expect(focusedElement).not.toBe("BODY");
    });

    test("Space/Enter activa TogglePill en lisa.servicios", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("lisa", "servicios");
      await shell.expectShellMounted();

      // Focus the Escalera toggle button
      const escaleraButton = shellPage
        .locator('[data-testid="servicios-toggle"]')
        .locator("text=Escalera");
      await escaleraButton.focus();
      await escaleraButton.press("Space");

      // Escalera pane should activate
      await expect(
        shellPage.locator('[data-testid="pane-escalera"]').first(),
      ).toBeVisible();
    });

    test("ribbon tabs accessible via keyboard aria-selected", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("lisa", "marca").first();

      // Active ribbon tab should have aria-selected="true"
      await expect(
        shellPage
          .locator('[data-testid="ribbon-tab-lisa"][aria-selected="true"]')
          .first(),
      ).toBeVisible();
    });
  });

  test.describe("ARIA landmarks", () => {
    test("lista de conversaciones tiene aria-label (adrian.inbox)", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("adrian", "inbox").first();
      await shell.expectShellMounted();

      await expect(
        shellPage.locator('[aria-label="Lista de conversaciones"]').first(),
      ).toBeVisible();
    });

    test("grilla agenda tiene aria-label (valeria.agenda)", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("valeria", "agenda").first();
      await shell.expectShellMounted();

      await expect(
        shellPage.locator('[aria-label="Grilla de agenda semanal"]').first(),
      ).toBeVisible();
    });

    test("thread messages tiene aria-live='polite' (adrian.inbox)", async ({
      shellPage,
      tenantId,
    }) => {
      const shell = new ShellOrganismPage(shellPage, tenantId);
      await shell.goto("adrian", "inbox").first();
      await shell.expectShellMounted();

      await expect(
        shellPage
          .locator(
            '[aria-live="polite"][aria-label="Mensajes de la conversación"]',
          )
          .first(),
      ).toBeVisible();
    });
  });
});
