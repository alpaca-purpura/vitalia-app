/**
 * Visual baseline spec — F1-S0 vitalia-fase1-stack-stability
 *
 * Generates 4 goldens (light/dark) for:
 *   1. shadcn-primitives — 8 Shadcn primitives showcase
 *   2. agent-tokens-swatch — 7 agent color swatches
 *
 * NOTE F1-S9 T-5: dashboard-legacy block removed (app/(dashboard)/ deleted).
 * The (dashboard)/ route group no longer exists. Visual coverage for the
 * authenticated shell is in e2e/regression/vitalia-fase1-routing-shell/.
 *
 * Project: @project=visual (playwright.config.ts)
 * Viewport: 1440×900, light/dark colorScheme per test
 * Tolerance: maxDiffPixelRatio 0.001 (0.1%)
 *
 * REQUIRES: make dev-vitalia running at E2E_BASE_URL (port 3002)
 * This spec is DEFERRED in F1-S0 (T-4) — goldens require Chris ratification.
 *
 * Run goldens generation:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test --project=visual e2e/visual/stack-stability/ --update-snapshots
 *
 * Run goldens regression:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test --project=visual e2e/visual/stack-stability/
 */

import { test, expect } from "@playwright/test";

const BASE_URL = process.env["E2E_BASE_URL"] ?? "http://localhost:3002";

// ── Helper: navigate + wait for stable render ────────────────────────────────
async function gotoAndWait(
  page: import("@playwright/test").Page,
  path: string,
) {
  await page.goto(`${BASE_URL}${path}`);
  // Wait for Tailwind styles to apply (no animation = deterministic)
  await page.waitForLoadState("networkidle");
}

// ── 1. Shadcn primitives showcase ────────────────────────────────────────────

test.describe("shadcn primitives showcase", () => {
  test("primitives render correctly in light mode", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    // NOTE: primitives-showcase is served via Next.js route or Playwright fixture server
    // In production run, it loads from the same Next.js dev server.
    // The route must exist at /test-stack/primitives (see Next.js config for test fixtures).
    await gotoAndWait(page, "/test-stack/primitives");
    await expect(page).toHaveScreenshot("shadcn-primitives-light.png", {
      fullPage: true,
    });
  });

  test("primitives render correctly in dark mode", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await gotoAndWait(page, "/test-stack/primitives");
    await expect(page).toHaveScreenshot("shadcn-primitives-dark.png", {
      fullPage: true,
    });
  });
});

// ── 2. Agent tokens swatch ───────────────────────────────────────────────────

test.describe("agent tokens swatch", () => {
  test("agent colors render correctly in light mode", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "light" });
    await gotoAndWait(page, "/test-stack/agent-tokens");
    await expect(page).toHaveScreenshot("agent-tokens-swatch-light.png", {
      fullPage: true,
    });
  });

  test("agent colors render correctly in dark mode", async ({ page }) => {
    await page.emulateMedia({ colorScheme: "dark" });
    await gotoAndWait(page, "/test-stack/agent-tokens");
    await expect(page).toHaveScreenshot("agent-tokens-swatch-dark.png", {
      fullPage: true,
    });
  });
});
