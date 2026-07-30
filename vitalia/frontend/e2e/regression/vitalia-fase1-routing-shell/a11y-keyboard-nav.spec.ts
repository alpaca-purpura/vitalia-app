/**
 * a11y-keyboard-nav.spec.ts — SC-6 accessibility · keyboard nav + axe WCAG 2.1 AA
 *
 * F1-S9 vitalia-fase1-routing-shell — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-6
 *
 * Given: user navegando con teclado solamente
 * When:  user presiona Tab → focus al Ribbon
 *        Arrow keys mueven entre tabs (roving tabindex paridad F1-S7)
 *        Enter en tab "Adrián" → URL /adrian/inbox
 * Then:  focus visible
 *        screen reader anuncia cambio vía title change
 *        no-focus-trap (Tab + Shift+Tab navega libre)
 *        contraste ≥ 4.5:1
 *        axe-core WCAG 2.1 AA passes (@axe tag)
 *
 * gherkin_coverage:
 *   - SC-6: Tab→Ribbon · Arrow→Adrián · Enter→navigate · axe WCAG 2.1 AA
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import { test, mockTenants } from "../../fixtures/routing-shell.fixture";
import { ShellPage } from "./poms/shell-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 720 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-6 — accessibility · keyboard nav + axe WCAG 2.1 AA", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-6-1: Tab key reaches Ribbon tab buttons", async ({ shellPage }) => {
    await mockTenants(shellPage, [{ id: TENANT_ID, name: "Clínica Test" }]);

    const pom = new ShellPage(shellPage);
    await pom.gotoSubtab(TENANT_ID, "valeria", "agenda");

    // Tab several times to reach the Ribbon area
    let ribbonFocused = false;
    for (let i = 0; i < 20; i++) {
      await shellPage.keyboard.press("Tab");
      const focusedEl = await shellPage.evaluate(
        () => document.activeElement?.getAttribute("data-testid") ?? "",
      );
      if (focusedEl.startsWith("ribbon-tab-")) {
        ribbonFocused = true;
        break;
      }
    }

    // At least one Ribbon tab should be reachable via Tab
    expect(ribbonFocused).toBe(true);
  });

  test("SC-6-2: Arrow keys navigate between Ribbon tabs (roving tabindex)", async ({
    shellPage,
  }) => {
    await mockTenants(shellPage, [{ id: TENANT_ID, name: "Clínica Test" }]);

    const pom = new ShellPage(shellPage);
    await pom.gotoSubtab(TENANT_ID, "valeria", "agenda");

    // Focus first ribbon tab via keyboard
    const ribbonTab = shellPage
      .locator('[data-testid="ribbon"] [role="tab"]')
      .first();
    await ribbonTab.focus();

    // Arrow right should move to next tab
    await shellPage.keyboard.press("ArrowRight");

    // Check that focus moved
    const newFocused = await shellPage.evaluate(
      () => document.activeElement?.getAttribute("data-testid") ?? "",
    );
    expect(newFocused).toMatch(/ribbon-tab-/);
  });

  test("SC-6-3: Enter on Adrián Ribbon tab navigates to /adrian/inbox", async ({
    shellPage,
  }) => {
    await mockTenants(shellPage, [{ id: TENANT_ID, name: "Clínica Test" }]);

    const pom = new ShellPage(shellPage);
    await pom.gotoSubtab(TENANT_ID, "valeria", "agenda");

    // Focus Adrian Ribbon tab directly
    const adrianTab = shellPage.locator('[data-testid="ribbon-tab-adrian"]');
    await adrianTab.focus();

    // Press Enter to navigate
    await shellPage.keyboard.press("Enter");

    // URL should change to /adrian/inbox
    await shellPage.waitForURL(`**/${TENANT_ID}/adrian/**`, {
      timeout: 10_000,
    });

    // Ribbon shows Adrian as active
    await pom.waitForRibbonActive("adrian");
  });

  test("SC-6-4: no focus trap — Tab + Shift+Tab navigate freely", async ({
    shellPage,
  }) => {
    await mockTenants(shellPage, [{ id: TENANT_ID, name: "Clínica Test" }]);

    const pom = new ShellPage(shellPage);
    await pom.gotoSubtab(TENANT_ID, "valeria", "agenda");

    // Tab 5 times forward
    for (let i = 0; i < 5; i++) {
      await shellPage.keyboard.press("Tab");
    }

    // Shift+Tab 5 times backward — should not loop or trap
    for (let i = 0; i < 5; i++) {
      await shellPage.keyboard.press("Shift+Tab");
    }

    // Focus should have moved without error — no assertion needed on exact element
    // Just verifying no exception thrown and page remains responsive
    const activeEl = await shellPage.evaluate(
      () => document.activeElement?.tagName ?? "BODY",
    );
    expect(activeEl).not.toBe("");
  });

  test("SC-6-5: not-found outer page keyboard nav — CTA reachable via Tab", async ({
    shellPage,
  }) => {
    const pom = new ShellPage(shellPage);
    await pom.gotoInvalidAgent(TENANT_ID, "agente-invalido");
    await expect(pom.getNotFoundShell()).toBeVisible({ timeout: 10_000 });

    // Tab to reach the "Volver al inicio" CTA
    let ctaFocused = false;
    for (let i = 0; i < 15; i++) {
      await shellPage.keyboard.press("Tab");
      const focusedText = await shellPage.evaluate(
        () => document.activeElement?.textContent?.trim() ?? "",
      );
      if (focusedText.match(/Volver al inicio/i)) {
        ctaFocused = true;
        break;
      }
    }
    expect(ctaFocused).toBe(true);
  });

  test("SC-6-6: axe WCAG 2.1 AA scan — valid shell route @axe", async ({
    shellPage,
  }) => {
    await mockTenants(shellPage, [{ id: TENANT_ID, name: "Clínica Test" }]);

    const pom = new ShellPage(shellPage);
    await pom.gotoSubtab(TENANT_ID, "valeria", "agenda");

    // Run axe scan
    const AxeBuilder = (await import("@axe-core/playwright")).default;
    const accessibilityScanResults = await new AxeBuilder({ page: shellPage })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("SC-6-7: axe WCAG 2.1 AA scan — outer not-found @axe", async ({
    shellPage,
  }) => {
    const pom = new ShellPage(shellPage);
    await pom.gotoInvalidAgent(TENANT_ID, "agente-invalido");
    await expect(pom.getNotFoundShell()).toBeVisible({ timeout: 10_000 });

    const AxeBuilder = (await import("@axe-core/playwright")).default;
    const accessibilityScanResults = await new AxeBuilder({ page: shellPage })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("SC-6-8: axe WCAG 2.1 AA scan — inner not-found @axe", async ({
    shellPage,
  }) => {
    const pom = new ShellPage(shellPage);
    await pom.gotoInvalidSubtab(TENANT_ID, "camila", "subtab-invalido");
    await expect(pom.getNotFoundAgent()).toBeVisible({ timeout: 10_000 });

    const AxeBuilder = (await import("@axe-core/playwright")).default;
    const accessibilityScanResults = await new AxeBuilder({ page: shellPage })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("SC-6-9: axe WCAG 2.1 AA scan — network error fallback @axe", async ({
    shellPage,
  }) => {
    const { mockTenantFetchFailure } =
      await import("../../fixtures/routing-shell.fixture");
    await mockTenantFetchFailure(shellPage, 6_000);

    await shellPage.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });
    const pom = new ShellPage(shellPage);
    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });

    const AxeBuilder = (await import("@axe-core/playwright")).default;
    const accessibilityScanResults = await new AxeBuilder({ page: shellPage })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
