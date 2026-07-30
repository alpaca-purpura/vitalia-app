/**
 * topbar.spec.ts — SC-10..SC-13 a11y (TopBarGlobal + skip link)
 * F1-S2 vitalia-fase1-topbar-global — T-7
 *
 * Tests:
 * - SC-10: axe-core WCAG 2.1 AA — zero violations in light mode (TopBar page)
 * - SC-11: axe-core WCAG 2.1 AA — zero violations in dark mode
 * - SC-12: Skip link keyboard navigation — Tab focuses skip link, Enter skips to #main-content
 * - SC-13: role=banner landmark present (WCAG 1.3.6)
 *
 * Project: a11y (playwright.config.ts)
 *
 * Run (dev server required):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/a11y/topbar-global/topbar.spec.ts \
 *     --project=a11y
 *
 * downstream-regression-na: brand-local a11y spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const TEST_PAGE = "/test-stack/topbar-global";

test.describe("SC-10..SC-13 — TopBarGlobal a11y (F1-S2)", () => {
  test("SC-10: zero WCAG 2.1 AA violations in light mode", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const topbar = page.getByTestId("topbar-global");
    await expect(topbar).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(results.violations).toHaveLength(0);
  });

  test("SC-11: zero WCAG 2.1 AA violations in dark mode", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("vitalia-theme", "dark");
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const topbar = page.getByTestId("topbar-global");
    await expect(topbar).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(results.violations).toHaveLength(0);
  });

  test("SC-12: skip link — Tab focuses it, Enter navigates to #main-content", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    // First Tab should focus the skip link (it's the first focusable element in body)
    await page.keyboard.press("Tab");

    // The skip link should be focused and visible
    const skipLink = page.locator('a[href="#main-content"]');

    // Skip link should be focused
    await expect(skipLink).toBeFocused();

    // Verify text (Spanish neutro)
    await expect(skipLink).toHaveText("Saltar al contenido");

    // Press Enter to follow the link
    await page.keyboard.press("Enter");

    // After activation, #main-content should receive focus (tabIndex=-1)
    const mainContent = page.locator("#main-content");
    await expect(mainContent).toBeAttached();
    // After Enter on skip link, browser moves focus to #main-content
    // (tabIndex=-1 allows programmatic focus)
    await expect(mainContent).toBeFocused();
  });

  test("SC-13: role=banner landmark present (WCAG 1.3.6)", async ({ page }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    // banner landmark = <header role="banner">
    const banner = page.getByRole("banner");
    await expect(banner).toBeVisible();
  });

  test("SC-13b: logo link has aria-label='Vitalia inicio'", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const logoLinks = page.getByRole("link", { name: "Vitalia inicio" });
    await expect(logoLinks.first()).toBeVisible();
  });
});
