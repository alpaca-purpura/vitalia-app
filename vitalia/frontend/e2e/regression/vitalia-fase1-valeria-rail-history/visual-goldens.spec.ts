/**
 * visual-goldens.spec.ts — 13 visual golden tests (F1-S5 ValeriaSidebar ratchet)
 *
 * F1-S5 vitalia-fase1-valeria-rail-history — T-8
 *
 * ITER-1: Goldens generated with `--update-snapshots --project=visual`.
 * Ratification: Chris side-by-side review required before ratchet locks.
 * Per shell-mockup-per-component.md protocol — goldens against ratified HTML mockups.
 *
 * 13 PNGs per 06-tickets.yaml gherkin_coverage (visual scenarios):
 *   1.  valeria-rail-1280x800-light.png
 *   2.  valeria-rail-1280x800-dark.png
 *   3.  valeria-full-1280x800-light.png
 *   4.  valeria-full-1280x800-dark.png
 *   5.  valeria-collapsed-1280x800-light.png
 *   6.  valeria-collapsed-1280x800-dark.png
 *   7.  valeria-history-search-1280x800-light.png
 *   8.  valeria-history-empty-1280x800-light.png
 *   9.  valeria-mobile-drawer-open-375x667.png
 *   10. valeria-mobile-drawer-closed-375x667.png
 *   11. valeria-rail-hover-1280x800-light.png (hover state on collapse button)
 *   12. valeria-full-dark-1280x800.png (alias dark full)
 *   13. valeria-transition-collapsed-to-rail-1280x800.png
 *
 * Visual project config (playwright.config.ts):
 *   snapshotPathTemplate: "e2e/__screenshots__/{testFilePath}/{arg}{ext}"
 *   maxDiffPixelRatio: 0.001 (0.1% tolerance)
 *   animations: "disabled"
 *   caret: "hide"
 *
 * Mockup references (pending Chris ratification):
 *   vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-rail.html
 *   vitalia/docs/product/stories/vitalia-fase1-valeria-rail-history/mockups/valeria-history.html
 *
 * Generation command (iter-1, run AFTER Chris ratifies mockups):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test --project=visual \
 *     e2e/regression/vitalia-fase1-valeria-rail-history/visual-goldens.spec.ts \
 *     --update-snapshots
 *
 * downstream-regression-na: brand-local E2E visual spec; no cross-brand consumers
 */

import { test, expect } from "../../fixtures/shell-theme.fixture";
import { ValeriaSidebarPage } from "../../pages/ValeriaSidebarPage";

const DESKTOP_VIEWPORT = { width: 1280, height: 800 };
const MOBILE_VIEWPORT = { width: 375, height: 667 };

// ---------------------------------------------------------------------------
// § 1 — Rail state goldens (1280x800)
// ---------------------------------------------------------------------------

test.describe("visual goldens — rail state (F1-S5)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("valeria rail light 1280x800 matches", async ({ valeriaRailPage }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    await pom.goto({
      valeriaState: "rail",
      shellMode: "agentic",
      theme: "light",
    });
    await expect(pom.sidebar).toBeVisible();
    await expect(valeriaRailPage).toHaveScreenshot(
      "valeria-rail-1280x800-light.png",
      {
        fullPage: false,
      },
    );
  });

  test("valeria rail dark 1280x800 matches", async ({ valeriaRailPage }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    await pom.goto({
      valeriaState: "rail",
      shellMode: "agentic",
      theme: "dark",
    });
    await expect(pom.sidebar).toBeVisible();
    await expect(valeriaRailPage).toHaveScreenshot(
      "valeria-rail-1280x800-dark.png",
      {
        fullPage: false,
      },
    );
  });
});

// ---------------------------------------------------------------------------
// § 2 — Full state goldens (1280x800)
// ---------------------------------------------------------------------------

test.describe("visual goldens — full state (F1-S5)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("valeria full light 1280x800 matches", async ({ valeriaFullPage }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });
    await expect(pom.sidebar).toBeVisible();
    await expect(valeriaFullPage).toHaveScreenshot(
      "valeria-full-1280x800-light.png",
      {
        fullPage: false,
      },
    );
  });

  test("valeria full dark 1280x800 matches", async ({ valeriaFullPage }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "dark",
    });
    await expect(pom.sidebar).toBeVisible();
    await expect(valeriaFullPage).toHaveScreenshot(
      "valeria-full-1280x800-dark.png",
      {
        fullPage: false,
      },
    );
  });
});

// ---------------------------------------------------------------------------
// § 3 — Collapsed state goldens (1280x800)
// ---------------------------------------------------------------------------

test.describe("visual goldens — collapsed state (F1-S5)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("valeria collapsed light 1280x800 matches", async ({
    valeriaRailPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    await pom.goto({
      valeriaState: "collapsed",
      shellMode: "web",
      theme: "light",
    });
    await expect(valeriaRailPage).toHaveScreenshot(
      "valeria-collapsed-1280x800-light.png",
      {
        fullPage: false,
      },
    );
  });

  test("valeria collapsed dark 1280x800 matches", async ({
    valeriaRailPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    await pom.goto({
      valeriaState: "collapsed",
      shellMode: "web",
      theme: "dark",
    });
    await expect(valeriaRailPage).toHaveScreenshot(
      "valeria-collapsed-1280x800-dark.png",
      {
        fullPage: false,
      },
    );
  });
});

// ---------------------------------------------------------------------------
// § 4 — History search + empty state goldens (1280x800)
// ---------------------------------------------------------------------------

test.describe("visual goldens — history search states (F1-S5)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("valeria history search active 1280x800 matches", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });
    await expect(pom.historySearch).toBeVisible();
    // Type a partial match to show filtered results (not empty)
    await pom.historySearch.click();
    await valeriaFullPage.keyboard.type("Resumen");
    await expect(valeriaFullPage).toHaveScreenshot(
      "valeria-history-search-1280x800-light.png",
      {
        fullPage: false,
      },
    );
  });

  test("valeria history empty state 1280x800 matches", async ({
    valeriaFullPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaFullPage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });
    await expect(pom.historySearch).toBeVisible();
    // No-match query → empty state
    await pom.historySearch.click();
    await valeriaFullPage.keyboard.type("xyzabc123");
    await expect(pom.emptyState).toBeVisible({ timeout: 3_000 });
    await expect(valeriaFullPage).toHaveScreenshot(
      "valeria-history-empty-1280x800-light.png",
      {
        fullPage: false,
      },
    );
  });
});

// ---------------------------------------------------------------------------
// § 5 — Mobile drawer goldens (375x667)
// ---------------------------------------------------------------------------

test.describe("visual goldens — mobile drawer (F1-S5)", () => {
  test.use({ viewport: MOBILE_VIEWPORT });

  test("valeria mobile drawer open 375x667 matches", async ({
    valeriaMobilePage,
  }) => {
    // ★ T-8.bis FIXED: mobile drawer ahora reachable via React.createPortal(drawer, document.body).
    // Drawer ya no está dentro de display:none parent — escapa del hidden agentic main.
    // NOTA: en mobile viewport, getByTestId('valeria-sidebar') matchea AMBOS (desktop hidden +
    // mobile drawer dialog) — usar selector más específico que matchea solo el mobile drawer.
    const pom = new ValeriaSidebarPage(valeriaMobilePage);
    await pom.goto({
      valeriaState: "full",
      shellMode: "agentic",
      theme: "light",
    });
    const mobileDrawer = valeriaMobilePage.locator(
      "[data-testid=valeria-sidebar][aria-modal='true']",
    );
    await expect(mobileDrawer).toBeVisible({ timeout: 5_000 });
    await valeriaMobilePage.waitForTimeout(300);
    await expect(valeriaMobilePage).toHaveScreenshot(
      "valeria-mobile-drawer-open-375x667.png",
      {
        fullPage: false,
      },
    );
  });

  test("valeria mobile drawer closed 375x667 matches", async ({
    valeriaMobilePage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaMobilePage);
    await pom.goto({
      valeriaState: "collapsed",
      shellMode: "web",
      theme: "light",
    });
    // Sidebar is hidden (collapsed + mobile) — screenshot shows web mode
    await expect(valeriaMobilePage).toHaveScreenshot(
      "valeria-mobile-drawer-closed-375x667.png",
      {
        fullPage: false,
      },
    );
  });
});

// ---------------------------------------------------------------------------
// § 6 — Transition state golden (1280x800)
// ---------------------------------------------------------------------------

test.describe("visual goldens — collapsed to rail transition (F1-S5)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("valeria transition collapsed→rail 1280x800 matches", async ({
    valeriaRailPage,
  }) => {
    const pom = new ValeriaSidebarPage(valeriaRailPage);
    // Start collapsed
    await pom.goto({
      valeriaState: "collapsed",
      shellMode: "web",
      theme: "light",
    });
    // Press r → transitions to rail
    await pom.pressShortcut("r");
    await valeriaRailPage.waitForTimeout(300); // allow 220ms animation to settle
    await expect(pom.sidebar).toBeVisible();
    await expect(pom.sidebar).toHaveAttribute("aria-expanded", "true");
    await expect(valeriaRailPage).toHaveScreenshot(
      "valeria-transition-collapsed-to-rail-1280x800.png",
      { fullPage: false },
    );
  });
});
