/**
 * sc-01-navegacion-22-subtabs.spec.ts — SC-1 · 22 sub-tabs navegables sin error
 * F1-S10 vitalia-fase1-empty-states — T-10
 * UPDATED: paradigm-map-zones T-6 (2026-05-30) — rutas valeria/agenda + valeria/pacientes
 *   → mateo/agenda + mateo/pacientes (Valeria es sidebar only v1.2).
 *
 * Assertions:
 *   - Navigate to each of the 22 {agent}/{subtab} routes
 *   - SubTabContent dispatcher renders correct data-testid for each
 *   - Ribbon stays mounted (no full shell remount detected)
 *   - Zero console errors during navigation sequence
 *   - SubTabHeader visible with correct agent.subtab
 *
 * Uses: ShellOrganismPage POM + empty-states.fixture (Clerk auth + shell seeded)
 *
 * SC-1 validator: val-fe-e2e-sc01-navegacion-22-subtabs
 * downstream-regression-na: brand-local vitalia e2e spec
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/empty-states.fixture";
import { ShellOrganismPage } from "../../pages/ShellOrganismPage";

// ── All 22 sub-tab routes (from RIBBON_SUBTABS SSoT — agent-catalog.ts) ───────
// UPDATED v1.2 (paradigm-map-zones T-6 2026-05-30):
//   valeria (2) → mateo (2) — Valeria is sidebar only, Mateo = Operar/agenda+pacientes
const SUBTAB_ROUTES = [
  // lisa (4)
  { agent: "lisa", subtab: "marca" },
  { agent: "lisa", subtab: "doctores" },
  { agent: "lisa", subtab: "servicios" },
  { agent: "lisa", subtab: "compliance" },
  // mateo (2) — UPDATED from valeria (2) in v1.2
  { agent: "mateo", subtab: "agenda" },
  { agent: "mateo", subtab: "pacientes" },
  // lucas (5)
  { agent: "lucas", subtab: "lanzar" },
  { agent: "lucas", subtab: "envuelo" },
  { agent: "lucas", subtab: "recursos" },
  { agent: "lucas", subtab: "resultados" },
  { agent: "lucas", subtab: "mercado" },
  // adrian (4)
  { agent: "adrian", subtab: "inbox" },
  { agent: "adrian", subtab: "embudo" },
  { agent: "adrian", subtab: "outbound" },
  { agent: "adrian", subtab: "propuestas" },
  // camila (4)
  { agent: "camila", subtab: "voz" },
  { agent: "camila", subtab: "reactivar" },
  { agent: "camila", subtab: "multiplicar" },
  { agent: "camila", subtab: "reputacion" },
  // config (3)
  { agent: "config", subtab: "cuenta" },
  { agent: "config", subtab: "conexiones" },
  { agent: "config", subtab: "avanzado" },
] as const;

test.describe("SC-1 · 22 sub-tabs navegables sin error", () => {
  test("navega los 22 sub-tabs sin error de consola", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);
    const consoleErrors: string[] = [];

    // Capture console errors during full navigation
    shellPage.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    // Navigate each sub-tab and assert SubTabContent rendered
    for (const { agent, subtab } of SUBTAB_ROUTES) {
      await shell.goto(agent, subtab);
      await shell.expectShellMounted();
      await shell.expectSubTabContentVisible(agent, subtab);
    }

    // Zero console errors across all 22 navigations
    const relevantErrors = consoleErrors.filter(
      (e) =>
        !e.includes("favicon") && !e.includes("404") && !e.includes("net::ERR"),
    );
    expect(relevantErrors).toHaveLength(0);
  });

  test("SubTabHeader visible en cada sub-tab", async ({
    shellPage,
    tenantId,
  }) => {
    const shell = new ShellOrganismPage(shellPage, tenantId);

    // Sample check — test the first of each agent to keep test time reasonable
    // UPDATED v1.2: valeria/agenda → mateo/agenda (paradigm-map-zones T-6)
    const sampleRoutes = [
      { agent: "lisa", subtab: "marca" },
      { agent: "mateo", subtab: "agenda" },
      { agent: "lucas", subtab: "lanzar" },
      { agent: "adrian", subtab: "embudo" },
      { agent: "camila", subtab: "voz" },
      { agent: "config", subtab: "cuenta" },
    ];

    for (const { agent, subtab } of sampleRoutes) {
      await shell.goto(agent, subtab);
      await shell.expectSubTabHeaderVisible(agent, subtab);
    }
  });

  test.describe("parametrized · subtab-content data-testid matches route", () => {
    for (const { agent, subtab } of SUBTAB_ROUTES) {
      test(`${agent}.${subtab} → data-testid="subtab-content-${agent}-${subtab}"`, async ({
        shellPage,
        tenantId,
      }) => {
        const shell = new ShellOrganismPage(shellPage, tenantId);
        await shell.goto(agent, subtab);
        await expect(
          shellPage
            .locator(`[data-testid="subtab-content-${agent}-${subtab}"]`)
            .first(),
        ).toBeVisible();
      });
    }
  });
});
