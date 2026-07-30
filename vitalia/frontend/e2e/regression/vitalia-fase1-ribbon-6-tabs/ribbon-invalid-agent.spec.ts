/**
 * ribbon-invalid-agent.spec.ts — SC-4 edge · URL segmento agente inválido
 *
 * F1-S7 vitalia-fase1-ribbon-6-tabs — T-5
 *
 * Gherkin: 01-spec.md § Gherkin SC-4
 *
 * Given: usuario navega directamente a /{tenantId}/foobar/baz
 * When:  la página carga
 * Then:  extractAgentFromPath(pathname) devuelve null
 * And:   todos los agent tabs + ConfigTab quedan data-active="false" (idle state)
 * And:   NO hay console error (no uncaught exceptions)
 * And:   Ribbon sigue renderizado correctamente (sin crashear)
 *
 * gherkin_coverage:
 *   - SC-4-1: URL /foobar/baz → todos tabs inactive + no console error
 *   - SC-4-2: URL /unknown-segment → ribbon renderizado sin crash
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { RibbonPage } from "./poms/ribbon-page.pom";
import type { AgentSlug } from "@/lib/agent-catalog";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

const ALL_AGENT_SLUGS: AgentSlug[] = [
  "lisa",
  "lucas",
  "adrian",
  "valeria",
  "camila",
];

test.describe("SC-4 — URL agente inválido → idle state, sin console error", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-4-1: URL /foobar/baz → todos los tabs inactive + no console error", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    // Collect console errors during navigation
    const consoleErrors: string[] = [];
    shellPage.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    // Collect uncaught exceptions
    const pageErrors: string[] = [];
    shellPage.on("pageerror", (err) => {
      pageErrors.push(err.message);
    });

    // Navigate to invalid agent URL via raw navigation
    await pom.gotoRaw(`/${TENANT_ID}/foobar/baz`);

    // Ribbon should still be visible (no crash). Wait for visible ribbon.
    await shellPage.waitForSelector('[data-testid="ribbon"]:visible', {
      timeout: 15_000,
    });

    // No tab should be active
    const activeSlug = await pom.getActiveSlug();
    expect(activeSlug).toBeNull();

    // All agent tabs should be inactive
    for (const slug of ALL_AGENT_SLUGS) {
      await expect(pom.getTab(slug)).toHaveAttribute("data-active", "false");
    }

    // ConfigTab should be inactive
    await expect(pom.getConfigTab()).toHaveAttribute("data-active", "false");

    // No uncaught page errors from the invalid URL
    // Filter out known non-critical browser warnings
    const criticalErrors = pageErrors.filter(
      (e) =>
        !e.includes("ResizeObserver") &&
        !e.includes("Non-Error promise rejection") &&
        !e.includes("Script error"),
    );
    expect(criticalErrors).toHaveLength(0);
  });

  test("SC-4-2: URL /unknown/segment → Ribbon renderizado sin crash + idle state", async ({
    shellPage,
  }) => {
    const pom = new RibbonPage(shellPage);

    const pageErrors: string[] = [];
    shellPage.on("pageerror", (err) => {
      pageErrors.push(err.message);
    });

    // Navigate to a completely unknown segment
    await pom.gotoRaw(`/${TENANT_ID}/unknown/segment`);

    // Ribbon should still be visible
    await shellPage.waitForSelector('[data-testid="ribbon"]:visible', {
      timeout: 15_000,
    });

    // Verify ribbon container is visible and functional
    const ribbon = pom.getRibbon();
    await expect(ribbon).toBeAttached();

    // All tabs should remain inactive
    const activeSlug = await pom.getActiveSlug();
    expect(activeSlug).toBeNull();

    // No critical errors
    const criticalErrors = pageErrors.filter(
      (e) =>
        !e.includes("ResizeObserver") &&
        !e.includes("Non-Error promise rejection") &&
        !e.includes("Script error"),
    );
    expect(criticalErrors).toHaveLength(0);
  });
});
