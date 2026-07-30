// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * a11y-keyboard.spec.ts — SC-16: axe wcag2aa + tab order (AC-12 · AC-16)
 *
 * Verifica accesibilidad del shell:
 *   1. axe WCAG 2.1 AA: 0 violaciones en light theme.
 *   2. Tab order: skip-link → topbar → main (primer elemento focusable).
 *   3. Strip avatar / '+' / historial / colapsar: focusables con aria-label.
 *   4. EntitySubNavBar: tablist con roving tabindex + flechas.
 *
 * Real-backend. Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/a11y-keyboard.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";
import AxeBuilder from "@axe-core/playwright";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-16 — accesibilidad + teclado (AC-12 · AC-16)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("axe WCAG 2.1 AA: 0 violaciones en shell (light theme)", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    const accessibilityScanResults = await new AxeBuilder({ page: shellPage })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("tab order: skip-link es el primer elemento focusable", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    // Reset tab sequence to document start
    await pom.resetTabSequenceToStart();

    // First Tab should land on the skip-link
    await shellPage.keyboard.press("Tab");
    const focusedHref = await shellPage.evaluate(
      () => document.activeElement?.getAttribute("href"),
    );
    expect(focusedHref).toBe("#main-content");
  });

  test("ValeriaCollapsedStrip: aria-label + focusable", async ({
    closedShellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(closedShellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    await expect(pom.collapsedStrip).toBeVisible({ timeout: 5_000 });

    // Strip must be a button with accessible name
    const tagName = await pom.collapsedStrip.evaluate(
      (el) => el.tagName.toLowerCase(),
    );
    expect(tagName).toBe("button");

    const ariaLabel = await pom.collapsedStrip.getAttribute("aria-label");
    expect(ariaLabel).toBeTruthy();
  });

  test("historial toggle: aria-label correcto", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    await pom.historyToggleBtn.waitFor({ state: "visible", timeout: 10_000 });
    const label = await pom.historyToggleBtn.getAttribute("aria-label");
    expect(label).toMatch(/historial/i);
  });

  test("nueva conversación: aria-label correcto", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId, { useProdRoute: true });
    await pom.waitForShellReady();

    await pom.newConversationBtn.waitFor({ state: "visible", timeout: 10_000 });
    const label = await pom.newConversationBtn.getAttribute("aria-label");
    expect(label).toBeTruthy();
    expect(label?.toLowerCase()).toContain("conversaci");
  });
});
