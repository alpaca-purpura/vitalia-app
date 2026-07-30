/**
 * logo-mark.spec.ts — SC-06..SC-09 visual goldens (LogoMark 6-cell grid)
 * F1-S2 vitalia-fase1-topbar-global — T-7
 *
 * Tests (4 goldens):
 * - SC-06: LogoMark grid light mode desktop (1440×900)
 * - SC-07: LogoMark grid dark mode desktop (1440×900)
 * - SC-08: TopBar light mode mobile (390×844 — responsive: full→mark swap)
 * - SC-09: TopBar dark mode mobile (390×844)
 *
 * Project: visual (playwright.config.ts — maxDiffPixelRatio: 0.001, animations: disabled)
 *
 * IMPORTANT: First run requires --update-snapshots to generate baseline:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/topbar-global/logo-mark.spec.ts \
 *     --project=visual --update-snapshots
 *
 * downstream-regression-na: brand-local visual spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

const LOGO_PAGE = "/test-stack/logo-mark";
const TOPBAR_PAGE = "/test-stack/topbar-global";

async function suppressAnimations(page: import("@playwright/test").Page) {
  await page.addStyleTag({
    content: `
      *, *::before, *::after {
        animation-duration: 0ms !important;
        animation-delay: 0ms !important;
        transition-duration: 0ms !important;
        transition-delay: 0ms !important;
      }
    `,
  });
}

test.describe("SC-06..SC-07 — LogoMark grid visual goldens (F1-S2)", () => {
  test.use({ viewport: { width: 1440, height: 900 } });

  test("SC-06: LogoMark 6-cell grid light mode golden", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto(LOGO_PAGE, { waitUntil: "domcontentloaded" });

    const showcase = page.getByTestId("logo-mark-showcase");
    await expect(showcase).toBeVisible();

    await suppressAnimations(page);

    await expect(showcase).toHaveScreenshot("logo-mark-grid-light.png");
  });

  test("SC-07: LogoMark 6-cell grid dark mode golden", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("vitalia-theme", "dark");
    });

    await page.goto(LOGO_PAGE, { waitUntil: "domcontentloaded" });

    const showcase = page.getByTestId("logo-mark-showcase");
    await expect(showcase).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    await suppressAnimations(page);

    await expect(showcase).toHaveScreenshot("logo-mark-grid-dark.png");
  });
});

test.describe("SC-08..SC-09 — TopBar mobile responsive visual goldens (F1-S2)", () => {
  // Mobile viewport — at 390px the mark variant becomes visible (inline-flex md:hidden)
  test.use({ viewport: { width: 390, height: 844 } });

  test("SC-08: TopBar light mode mobile golden (390px — mark variant visible)", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto(TOPBAR_PAGE, { waitUntil: "domcontentloaded" });

    const topbar = page.getByTestId("topbar-global");
    await expect(topbar).toBeVisible();

    await suppressAnimations(page);

    await expect(topbar).toHaveScreenshot("topbar-light-mobile.png");
  });

  test("SC-09: TopBar dark mode mobile golden (390px)", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("vitalia-theme", "dark");
    });

    await page.goto(TOPBAR_PAGE, { waitUntil: "domcontentloaded" });

    const topbar = page.getByTestId("topbar-global");
    await expect(topbar).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    await suppressAnimations(page);

    await expect(topbar).toHaveScreenshot("topbar-dark-mobile.png");
  });
});
