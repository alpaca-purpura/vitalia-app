/**
 * theme-toggle.spec.ts — SC-04, SC-05 visual goldens
 * F1-S1 vitalia-fase1-design-tokens-theme — 03-arch.md § 2.7 (visual regression)
 *
 * Tests:
 * - SC-04: ThemeToggle light baseline golden (400×300 viewport)
 * - SC-05: ThemeToggle dark baseline golden (400×300 viewport)
 *
 * Project: visual (playwright.config.ts — maxDiffPixelRatio: 0.001, animations: disabled)
 * Goldens path: e2e/__screenshots__/design-tokens-theme/
 *
 * IMPORTANT: First run requires --update-snapshots to generate baseline:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/design-tokens-theme/theme-toggle.spec.ts \
 *     --project=visual --update-snapshots
 *
 * Subsequent runs compare against baseline (maxDiffPixelRatio: 0.001).
 * Shell-mockup-per-component protocol: golden is truth post-ratification.
 *
 * downstream-regression-na: brand-local visual spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

const TEST_PAGE = "/test-stack/design-tokens-theme";

test.describe("SC-04..SC-05 — ThemeToggle visual goldens (F1-S1)", () => {
  test.use({ viewport: { width: 400, height: 300 } });

  test("SC-04: ThemeToggle light mode golden", async ({ page }) => {
    // Clear state — ensure light mode
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    // Ensure light theme is active
    const button = page.getByTestId("theme-toggle");
    await expect(button).toBeVisible();
    await expect(button).toHaveAttribute("aria-pressed", "false");

    // Suppress all animations for deterministic snapshot
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

    await expect(page).toHaveScreenshot("theme-toggle-light.png");
  });

  test("SC-05: ThemeToggle dark mode golden", async ({ page }) => {
    // Pre-set dark theme via localStorage
    await page.addInitScript(() => {
      localStorage.setItem("vitalia-theme", "dark");
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    // Ensure dark theme is active
    const button = page.getByTestId("theme-toggle");
    await expect(button).toBeVisible();
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");
    await expect(button).toHaveAttribute("aria-pressed", "true");

    // Suppress animations
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

    await expect(page).toHaveScreenshot("theme-toggle-dark.png");
  });
});
