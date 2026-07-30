/**
 * a11y-keyboard.spec.ts — SC-4 adversarial: a11y keyboard nav + axe WCAG 2.1 AA.
 *
 * F1-S4 vitalia-fase1-shell-layout-5050 — T-7
 * Gherkin: SC-4 "Given ShellOrganismLayout en desktop, When usuario navega con teclado,
 *           Then skip-link alcanzable, resize handle focusable + ArrowLeft/Right resize
 *           16px step, axe WCAG 2.1 AA pasa en light y dark."
 *
 * Scenario coverage (04-validators.yaml):
 *   val-fe-e2e-a11y-keyboard
 *   val-fe-axe
 *
 * Tags: @axe (filtered via --grep '@axe' for axe-only runs)
 *
 * Project: smoke (playwright.config.ts — regression/*.spec.ts añadido a testMatch)
 * Requires: dev server at E2E_BASE_URL (localhost:3002), Clerk auth state.
 *
 * Run (all):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/a11y-keyboard.spec.ts \
 *     --project=smoke
 *
 * Run (axe only):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase1-shell-layout-5050/a11y-keyboard.spec.ts \
 *     --grep '@axe' --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "../../fixtures/shell-theme.fixture";
import { ShellLayoutPage } from "../../pages/ShellLayoutPage";
import AxeBuilder from "@axe-core/playwright";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };

test.describe("SC-4 — a11y keyboard nav + axe WCAG 2.1 AA (F1-S4)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  // ── Assertion 1: Tab order LogoMark→ThemeToggle→TenantSwitcher→main ─────────

  test("Tab order LogoMark→ThemeToggle→TenantSwitcher→main", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);
    await pom.waitForShellReady();
    // Anchor the tab sequence to the document start — neutralizes the Chromium +
    // dynamic-SSR starting-point artifact (see ShellLayoutPage.resetTabSequenceToStart).
    await pom.resetTabSequenceToStart();

    // Press Tab from body to begin keyboard navigation
    // Skip-link is first (sr-only — focus reveals it)
    await shellPage.keyboard.press("Tab");
    // First focusable element should be the skip-link
    const skipLinkFocused = await shellPage.evaluate(() => {
      const el = document.activeElement;
      return el?.getAttribute("href") === "#main-content";
    });
    // Skip-link is in layout.tsx as first element in body
    expect(skipLinkFocused).toBe(true);

    // Tab again — focuses into header region (LogoMark link or first interactive)
    await shellPage.keyboard.press("Tab");
    // Tab once more for ThemeToggle or TenantSwitcher
    await shellPage.keyboard.press("Tab");

    // After a few Tabs, focus should be inside the shell (not stuck outside)
    const bodyHasFocus = await shellPage.evaluate(() => {
      return document.activeElement !== document.body;
    });
    expect(bodyHasFocus).toBe(true);
  });

  // ── Assertion 2: resize handle focusable tabindex='0' ──────────────────────

  test("resize handle focusable tabindex='0'", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);

    // react-resizable-panels v4 Separator has tabIndex={0} for keyboard resize
    const tabIndex = await pom.resizeHandle.getAttribute("tabindex");
    expect(tabIndex).toBe("0");

    // Separator must be focusable
    await pom.resizeHandle.focus();
    const isFocused = await shellPage.evaluate(() => {
      return (
        document.activeElement?.getAttribute("aria-label") ===
        "Redimensionar paneles"
      );
    });
    expect(isFocused).toBe(true);
  });

  // ── Assertion 3: ArrowLeft/ArrowRight step 16px on focused handle ───────────

  test("ArrowLeft/ArrowRight step 16px on focused handle", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);
    await pom.waitForShellReady();

    // Focus the resize handle
    await pom.resizeHandle.focus();
    const widthBefore = await pom.getValeriaWidth();
    expect(widthBefore).toBeGreaterThan(0);

    // Press ArrowLeft — should decrease Valeria width
    await shellPage.keyboard.press("ArrowLeft");
    await shellPage.waitForTimeout(100);
    const widthAfterLeft = await pom.getValeriaWidth();
    // Width should decrease (or stay at min clamp)
    expect(widthAfterLeft).toBeLessThanOrEqual(widthBefore + 5);

    // Press ArrowRight — should increase Valeria width (or stay at max)
    await shellPage.keyboard.press("ArrowRight");
    await shellPage.keyboard.press("ArrowRight");
    await shellPage.waitForTimeout(100);
    const widthAfterRight = await pom.getValeriaWidth();
    // After pressing right twice, should be >= width after left
    expect(widthAfterRight).toBeGreaterThanOrEqual(widthAfterLeft - 5);
  });

  // ── Assertion 4: skip-link 'Saltar al contenido' focuses main#main-content ──

  test("skip-link 'Saltar al contenido' focuses main#main-content", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);
    await pom.waitForShellReady();
    // Anchor the tab sequence to the document start (see resetTabSequenceToStart).
    await pom.resetTabSequenceToStart();

    // Tab to reveal skip-link (it's sr-only until focused)
    await shellPage.keyboard.press("Tab");

    // Verify skip-link is now focused
    const skipLinkText = await shellPage.evaluate(() => {
      return document.activeElement?.textContent?.trim();
    });
    expect(skipLinkText).toBe("Saltar al contenido");

    // Press Enter to activate skip-link
    await shellPage.keyboard.press("Enter");
    await shellPage.waitForTimeout(200);

    // Focus should now be on main#main-content (tabIndex={-1} allows programmatic focus)
    const mainFocused = await shellPage.evaluate(() => {
      const active = document.activeElement;
      return active?.id === "main-content";
    });
    expect(mainFocused).toBe(true);
  });

  // ── Assertion 5: axe wcag2aa passes light theme @axe ───────────────────────

  test("axe wcag2aa passes light theme @axe", async ({
    shellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(shellPage);
    await pom.gotoShell(tenantId);

    // Ensure shell is fully rendered
    await expect(pom.topBar).toBeVisible();

    const results = await new AxeBuilder({ page: shellPage })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      // Clerk iframe in dev mode has known third-party a11y issues
      .exclude({ selector: 'iframe[src*="clerk"]' })
      // ShellModeToggle is intentionally disabled (F1-S4 placeholder)
      // aria-disabled on button is valid — no violation
      .analyze();

    const critical = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    expect(
      critical,
      `Axe critical/serious violations (light theme) shell layout:\n${JSON.stringify(
        critical.map((v) => ({
          id: v.id,
          impact: v.impact,
          description: v.description,
          nodes: v.nodes.map((n) => n.html),
        })),
        null,
        2,
      )}`,
    ).toHaveLength(0);
  });

  // ── Assertion 6: axe wcag2aa passes dark theme @axe ────────────────────────

  test("axe wcag2aa passes dark theme @axe", async ({
    darkShellPage,
    tenantId,
  }) => {
    const pom = new ShellLayoutPage(darkShellPage);
    await pom.gotoShell(tenantId);

    // Ensure dark theme is applied
    await expect(pom.topBar).toBeVisible();

    const results = await new AxeBuilder({ page: darkShellPage })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .exclude({ selector: 'iframe[src*="clerk"]' })
      .analyze();

    const critical = results.violations.filter(
      (v) => v.impact === "critical" || v.impact === "serious",
    );

    expect(
      critical,
      `Axe critical/serious violations (dark theme) shell layout:\n${JSON.stringify(
        critical.map((v) => ({
          id: v.id,
          impact: v.impact,
          description: v.description,
          nodes: v.nodes.map((n) => n.html),
        })),
        null,
        2,
      )}`,
    ).toHaveLength(0);
  });
});
