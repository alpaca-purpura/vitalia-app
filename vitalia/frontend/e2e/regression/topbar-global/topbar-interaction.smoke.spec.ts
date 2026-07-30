/**
 * topbar-interaction.smoke.spec.ts — SC-01, SC-02, SC-03 behavior regression
 * F1-S2 vitalia-fase1-topbar-global — T-7
 *
 * Tests:
 * - SC-01: TopBarGlobal renders with role=banner, data-testid=topbar-global
 * - SC-02: Logo links to / with aria-label="Vitalia inicio"
 * - SC-03: ThemeToggle button present and interactive (re-tests F1-S1 in TopBar context)
 *
 * Project: smoke (playwright.config.ts — *.smoke.spec.ts)
 * Public page: /test-stack/topbar-global (no Clerk auth required)
 *
 * Run (dev server required):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/topbar-global/topbar-interaction.smoke.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

const TEST_PAGE = "/test-stack/topbar-global";

test.describe("SC-01..SC-03 — TopBarGlobal interaction (F1-S2)", () => {
  test.beforeEach(async ({ page }) => {
    // Isolate each test: clear localStorage to reset theme state
    await page.addInitScript(() => {
      localStorage.clear();
    });
  });

  test("SC-01: TopBarGlobal renders with role=banner and data-testid", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const topbar = page.getByTestId("topbar-global");
    await expect(topbar).toBeVisible();
    await expect(topbar).toHaveAttribute("role", "banner");
  });

  test("SC-02: Logo links to / with aria-label='Vitalia inicio'", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    // At desktop viewport, the full logo is visible (hidden md:inline-flex)
    // We query by aria-label which is on all LogoMark instances
    const logoLinks = page.getByRole("link", { name: "Vitalia inicio" });
    // At least one logo link must be present
    await expect(logoLinks.first()).toBeVisible();
    await expect(logoLinks.first()).toHaveAttribute("href", "/");
  });

  test("SC-03: ThemeToggle present inside TopBar, toggles dark mode", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const toggleBtn = page.getByTestId("theme-toggle");
    await expect(toggleBtn).toBeVisible();
    await expect(toggleBtn).toHaveAttribute("aria-pressed", "false");

    // Click → dark
    await toggleBtn.click();
    await expect(toggleBtn).toHaveAttribute("aria-pressed", "true");
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    // Click again → light
    await toggleBtn.click();
    await expect(toggleBtn).toHaveAttribute("aria-pressed", "false");
  });

  test("SC-01b: TopBar height is 48px (h-12 class)", async ({ page }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const topbar = page.getByTestId("topbar-global");
    const box = await topbar.boundingBox();
    // h-12 = 48px (Tailwind default, may vary slightly with border)
    expect(box?.height).toBeGreaterThanOrEqual(47);
    expect(box?.height).toBeLessThanOrEqual(50);
  });

  test("SC-03b: zero console errors during load", async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    await page.goto(TEST_PAGE, { waitUntil: "networkidle" });
    await page.waitForTimeout(500);

    const criticalErrors = consoleErrors.filter(
      (msg) =>
        !msg.includes("[Fast Refresh]") &&
        !msg.includes("[HMR]") &&
        !msg.includes("Warning:") &&
        !msg.includes("hydrat"),
    );

    expect(criticalErrors).toHaveLength(0);
  });
});
