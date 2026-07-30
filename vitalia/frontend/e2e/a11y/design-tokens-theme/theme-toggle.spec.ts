/**
 * theme-toggle.spec.ts — SC-06, SC-07, SC-08 a11y
 * F1-S1 vitalia-fase1-design-tokens-theme — 03-arch.md § 2.7 (a11y)
 *
 * Tests:
 * - SC-06: axe-core WCAG 2.1 AA — zero violations in light mode
 * - SC-07: axe-core WCAG 2.1 AA — zero violations in dark mode
 * - SC-08: Keyboard navigation — Tab focus + Enter/Space activate toggle
 *
 * Project: a11y (playwright.config.ts)
 *
 * Run (dev server required):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/a11y/design-tokens-theme/theme-toggle.spec.ts \
 *     --project=a11y
 *
 * downstream-regression-na: brand-local a11y spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

const TEST_PAGE = "/test-stack/design-tokens-theme";

test.describe("SC-06..SC-08 — ThemeToggle a11y (F1-S1)", () => {
  test("SC-06: zero WCAG 2.1 AA violations in light mode", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const button = page.getByTestId("theme-toggle");
    await expect(button).toBeVisible();

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(results.violations).toHaveLength(0);
  });

  test("SC-07: zero WCAG 2.1 AA violations in dark mode", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("vitalia-theme", "dark");
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const button = page.getByTestId("theme-toggle");
    await expect(button).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa"])
      .analyze();

    expect(results.violations).toHaveLength(0);
  });

  test("SC-08: keyboard navigation — Tab focuses toggle, Enter activates, Space activates", async ({
    page,
  }) => {
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const button = page.getByTestId("theme-toggle");
    await expect(button).toBeVisible();

    // Tab to focus button
    await page.keyboard.press("Tab");

    // Wait for focus — button should be focused
    // (multiple Tabs may be needed if other focusable elements precede it)
    const focusedTag = await page.evaluate(() =>
      document.activeElement?.getAttribute("data-testid"),
    );

    // If not directly focused, try additional Tabs
    if (focusedTag !== "theme-toggle") {
      for (let i = 0; i < 5; i++) {
        await page.keyboard.press("Tab");
        const tag = await page.evaluate(() =>
          document.activeElement?.getAttribute("data-testid"),
        );
        if (tag === "theme-toggle") break;
      }
    }

    // Verify button is focused
    await expect(button).toBeFocused();

    // Enter should activate (light → dark)
    expect(
      await page.evaluate(() =>
        document
          .querySelector('[data-testid="theme-toggle"]')
          ?.getAttribute("aria-pressed"),
      ),
    ).toBe("false");

    await page.keyboard.press("Enter");
    await expect(button).toHaveAttribute("aria-pressed", "true");

    // Space should activate (dark → light)
    await page.keyboard.press("Space");
    await expect(button).toHaveAttribute("aria-pressed", "false");
  });
});
