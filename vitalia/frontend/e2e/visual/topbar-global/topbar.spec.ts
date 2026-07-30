/**
 * topbar.spec.ts — SC-04, SC-05 visual goldens (TopBarGlobal)
 * F1-S2 vitalia-fase1-topbar-global — T-7
 *
 * Tests:
 * - SC-04: TopBarGlobal light mode golden (1440×900 desktop)
 * - SC-05: TopBarGlobal dark mode golden (1440×900 desktop)
 *
 * Project: visual (playwright.config.ts — maxDiffPixelRatio: 0.001, animations: disabled)
 *
 * IMPORTANT: First run requires --update-snapshots to generate baseline:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/topbar-global/topbar.spec.ts \
 *     --project=visual --update-snapshots
 *
 * Subsequent runs compare against baseline (maxDiffPixelRatio: 0.001).
 * Shell-mockup-per-component protocol: golden is truth post-ratification.
 *
 * downstream-regression-na: brand-local visual spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

const TEST_PAGE = "/test-stack/topbar-global";

// Helper to suppress CSS animations/transitions for deterministic snapshots
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

test.describe("SC-04..SC-05 — TopBarGlobal visual goldens (F1-S2)", () => {
  // Desktop viewport (matches playwright.config.ts visual project default)
  test.use({ viewport: { width: 1440, height: 900 } });

  test("SC-04: TopBarGlobal light mode golden (desktop)", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const topbar = page.getByTestId("topbar-global");
    await expect(topbar).toBeVisible();
    await expect(page.getByTestId("theme-toggle")).toHaveAttribute(
      "aria-pressed",
      "false",
    );

    await suppressAnimations(page);

    // Snapshot the full topbar element
    await expect(topbar).toHaveScreenshot("topbar-light-desktop.png");
  });

  test("SC-05: TopBarGlobal dark mode golden (desktop)", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("vitalia-theme", "dark");
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const topbar = page.getByTestId("topbar-global");
    await expect(topbar).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await expect(page.getByTestId("theme-toggle")).toHaveAttribute(
      "aria-pressed",
      "true",
    );

    await suppressAnimations(page);

    await expect(topbar).toHaveScreenshot("topbar-dark-desktop.png");
  });
});
