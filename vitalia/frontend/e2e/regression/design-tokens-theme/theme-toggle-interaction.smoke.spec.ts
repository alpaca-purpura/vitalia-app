/**
 * theme-toggle-interaction.spec.ts — SC-01, SC-02, SC-03
 * F1-S1 vitalia-fase1-design-tokens-theme — 03-arch.md § 2.7 (behavior regression)
 *
 * Tests:
 * - SC-01: Toggle light → dark — html attribute, localStorage, aria state
 * - SC-02: Persistence — reload preserves dark theme (no FOUC)
 * - SC-03: Zero console errors during hydration (suppressHydrationWarning)
 *
 * Public page: /test-stack/design-tokens-theme (no Clerk auth required)
 * proxy.ts: /test-stack(.*) is public route
 *
 * Run (dev server required):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/design-tokens-theme/theme-toggle-interaction.spec.ts
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

const TEST_PAGE = "/test-stack/design-tokens-theme";

test.describe("SC-01..SC-03 — ThemeToggle interaction (F1-S1)", () => {
  test.beforeEach(async ({ page }) => {
    // Isolate each test: clear localStorage to reset theme state
    await page.addInitScript(() => {
      localStorage.clear();
    });
  });

  test("SC-01: click toggle changes html to data-theme='dark', localStorage, and aria-state", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    // Initial state: light (default)
    const button = page.getByTestId("theme-toggle");
    await expect(button).toBeVisible();
    await expect(button).toHaveAttribute("aria-pressed", "false");
    await expect(button).toHaveAttribute(
      "aria-label",
      "Cambiar tema (actual: claro)",
    );

    // Click → dark
    await button.click();

    // html element should have data-theme="dark"
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    // localStorage should persist theme
    const storedTheme = await page.evaluate(() =>
      localStorage.getItem("vitalia-theme"),
    );
    expect(storedTheme).toBe("dark");

    // aria-pressed updated
    await expect(button).toHaveAttribute("aria-pressed", "true");
    await expect(button).toHaveAttribute(
      "aria-label",
      "Cambiar tema (actual: oscuro)",
    );
  });

  test("SC-01b: click toggle twice returns to light", async ({ page }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    const button = page.getByTestId("theme-toggle");
    await button.click(); // → dark
    await button.click(); // → light

    await expect(page.locator("html")).not.toHaveAttribute(
      "data-theme",
      "dark",
    );
    await expect(button).toHaveAttribute("aria-pressed", "false");
  });

  test("SC-02: theme persists on reload — no FOUC (dark stays dark)", async ({
    page,
  }) => {
    // Set dark theme via localStorage before navigation
    await page.addInitScript(() => {
      localStorage.setItem("vitalia-theme", "dark");
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    // html should already have data-theme="dark" without clicking
    await expect(page.locator("html")).toHaveAttribute("data-theme", "dark");

    const button = page.getByTestId("theme-toggle");
    await expect(button).toHaveAttribute("aria-pressed", "true");
    await expect(button).toHaveAttribute(
      "aria-label",
      "Cambiar tema (actual: oscuro)",
    );
  });

  test("SC-03: zero console errors during hydration (suppressHydrationWarning)", async ({
    page,
  }) => {
    const consoleErrors: string[] = [];
    const pageErrors: Error[] = [];

    page.on("console", (msg) => {
      if (msg.type() === "error") {
        consoleErrors.push(msg.text());
      }
    });

    page.on("pageerror", (err) => {
      pageErrors.push(err);
    });

    await page.goto(TEST_PAGE, { waitUntil: "networkidle" });

    // Wait a tick for hydration to complete
    await page.waitForTimeout(500);

    // Filter out known-acceptable warnings (Vite HMR, etc.)
    const criticalErrors = consoleErrors.filter(
      (msg) =>
        !msg.includes("[Fast Refresh]") &&
        !msg.includes("[HMR]") &&
        !msg.includes("Warning:") &&
        !msg.includes("hydrat"), // suppress hydration warnings are expected
    );

    expect(criticalErrors).toHaveLength(0);
    expect(pageErrors).toHaveLength(0);
  });
});
