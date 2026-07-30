/**
 * history-empty-search.spec.ts — SC-6 búsqueda sin resultados (empty state)
 *
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8
 *
 * Gherkin: 01-spec.md § 1 Scenario 6 (empty_state)
 *
 * Given: valeriaState='full', history visible con 8 mock items
 * When:  User types 'xyzabc123' (no match), then presses Esc
 * Then:  EmptyStateInline visible, groups hidden, Esc clears search + restores list
 *
 * SC-6 gherkin_coverage:
 *   - SC-6-1: type 'xyzabc123' → history-empty-state visible
 *   - SC-6-2: empty state shows 'Sin resultados' (Spanish neutro)
 *   - SC-6-3: group labels (Hoy/Ayer/Esta semana) disappear when empty
 *   - SC-6-4: search input retains typed text
 *   - SC-6-5: press Esc → search cleared + list restored (Valeria stays 'full')
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test } from "../../fixtures/shell-theme.fixture";
import { ValeriaSidebarPage } from "../../pages/ValeriaSidebarPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-6 — history empty search state", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-6-1: type 'xyzabc123' → history-empty-state visible", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Click search + type no-match query
    await pom.historySearch.click();
    await valeriaFullPage.keyboard.type("xyzabc123");

    // EmptyState component must appear
    await expect(pom.emptyState).toBeVisible({ timeout: 3_000 });
  });

  test("SC-6-2: empty state copy is Spanish neutro ('Sin resultados')", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    await pom.historySearch.click();
    await valeriaFullPage.keyboard.type("xyzabc123");

    await expect(pom.emptyState).toBeVisible({ timeout: 3_000 });

    // Must contain 'Sin resultados' heading
    await expect(pom.emptyState).toContainText("Sin resultados");
    // Must contain the suggestion copy (Spanish neutro, no voseo)
    await expect(pom.emptyState).toContainText("Intenta con otra palabra");
  });

  test("SC-6-3: group labels (Hoy/Ayer/Esta semana) hidden when search empty", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    // Verify groups visible before search (exact: true avoids strict mode violations)
    await expect(
      valeriaFullPage.getByText("Hoy", { exact: true }).first(),
    ).toBeVisible();

    // Type no-match query
    await pom.historySearch.click();
    await valeriaFullPage.keyboard.type("xyzabc123");
    await expect(pom.emptyState).toBeVisible({ timeout: 3_000 });

    // Group labels should not be visible (filtered out)
    await expect(
      valeriaFullPage.getByText("Hoy", { exact: true }).first(),
    ).not.toBeVisible();
    await expect(
      valeriaFullPage.getByText("Ayer", { exact: true }).first(),
    ).not.toBeVisible();
    await expect(
      valeriaFullPage.getByText("Esta semana", { exact: true }).first(),
    ).not.toBeVisible();
  });

  test("SC-6-4: search input retains typed text when empty state shown", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    await pom.historySearch.click();
    await valeriaFullPage.keyboard.type("xyzabc123");

    await expect(pom.emptyState).toBeVisible({ timeout: 3_000 });

    // Input must retain the typed text
    await expect(pom.historySearch).toHaveValue("xyzabc123");
  });

  test("SC-6-5: press Esc clears search + restores list, Valeria stays 'full'", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({ valeriaState: "full", shellMode: "agentic" });

    await pom.historySearch.click();
    await valeriaFullPage.keyboard.type("xyzabc123");
    await expect(pom.emptyState).toBeVisible({ timeout: 3_000 });

    // Press Esc — clears search (NOT collapses Valeria while input has focus)
    await valeriaFullPage.keyboard.press("Escape");

    // Empty state should be gone
    await expect(pom.emptyState).not.toBeVisible({ timeout: 3_000 });

    // Search input cleared
    await expect(pom.historySearch).toHaveValue("");

    // History list restored — 'Hoy' group visible again
    await expect(
      valeriaFullPage.getByText("Hoy", { exact: true }).first(),
    ).toBeVisible({ timeout: 3_000 });

    // Critical: valeriaState still 'full' — Esc did NOT collapse when input was focused
    const state = await pom.getValeriaState();
    expect(state).toBe("full");
  });
});
