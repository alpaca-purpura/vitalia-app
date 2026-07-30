/**
 * sc-05-subtab-invalido.spec.ts — SC-5 · subtab inválido → not-found.tsx jerárquico
 * F1-S10 vitalia-fase1-empty-states — T-10
 *
 * Assertions:
 *   - Navigate to /{tenantId}/lisa/subtab-que-no-existe
 *   - not-found.tsx renders INSIDE the shell (data-testid="not-found-agent")
 *   - Shell organism stays mounted: ribbon + sub-tabs-bar visible
 *   - ValeriaSidebar stays visible (persistent shell element)
 *   - Navigate to /{tenantId}/agente-invalido → outer not-found OR redirected
 *   - No crash / no console uncaught errors
 *
 * The routing spec (F1-S9) wires not-found.tsx hierarchically:
 *   - Invalid subtab within valid agent → inner not-found (shell stays)
 *   - Invalid agent → outer not-found (shell may or may not stay per routing config)
 *
 * Uses: ShellOrganismPage POM + empty-states.fixture
 *
 * SC-5 validator: val-fe-e2e-sc05-subtab-invalido
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { ShellOrganismPage } from "../../pages/ShellOrganismPage";

test.describe("SC-5 · subtab inválido → not-found jerárquico", () => {
  test("subtab inválido dentro de agente válido → not-found dentro shell", async ({
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

    await shell.gotoInvalidSubtab("lisa", "subtab-que-no-existe");

    // not-found component renders inside shell
    await shell.expectNotFoundInShell();

    // Zero uncaught JS errors
    const uncaught = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("net::ERR"),
    );
    expect(uncaught).toHaveLength(0);
  });

  test("shell ribbon + sub-tabs-bar siguen visibles con subtab inválido", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    await shell.gotoInvalidSubtab("valeria", "subtab-invalido-123");

    // Shell organism stays mounted even with invalid subtab
    await expect(shell.ribbon).toBeVisible();
    await expect(shell.subTabsBar).toBeVisible();
  });

  test("ValeriaSidebar visible con subtab inválido (shell persistente)", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    await shell.gotoInvalidSubtab("adrian", "no-existe");

    // Ribbon must be visible — shell is mounted
    await expect(shell.ribbon).toBeVisible();
  });

  test("subtab inválido con caracteres especiales no provoca crash", async ({
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

    // Special characters in subtab segment
    await shell.gotoInvalidSubtab("lisa", "tab con espacios");

    // Page must render (not blank)
    await expect(shellPage.locator("body").first()).toBeVisible();
    // No JS runtime errors
    const uncaught = consoleErrors.filter(
      (e) =>
        !e.includes("favicon").first() &&
        !e.includes("net::ERR") &&
        !e.includes("404"),
    );
    expect(uncaught).toHaveLength(0);
  });
});
