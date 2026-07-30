/**
 * routing-shell.fixture.ts — Playwright fixture for routing-shell E2E specs.
 *
 * F1-S9 vitalia-fase1-routing-shell — T-6
 *
 * Provides:
 *   - `authedAs(role)`: Clerk storageState + tenant setup (wraps auth.fixture authedPage)
 *   - `mockTenants(tenants[])`: page.route() mock for GET /api/v1/iam/users/me/tenants
 *   - `mockTenantFetchFailure()`: mock timeout (delay > 5s AbortError simulation via 500)
 *   - `mockNoTenants()`: mock response { tenants: [] }
 *
 * Usage in specs:
 *   import { test, expect } from '../../fixtures/routing-shell.fixture';
 *
 * spec_anchor: 04-validators.yaml § test_construction_plan.fixtures_required
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

import { test as base, expect } from "../auth.fixture";
import type { Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface TenantStub {
  id: string;
  name?: string;
  slug?: string;
}

export interface RoutingShellFixtures {
  /** Authenticated page with deterministic shell localStorage seeding. */
  shellPage: Page;
  /** Dark-themed authenticated page for visual goldens. */
  darkShellPage: Page;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const TENANTS_ENDPOINT = "**/api/v1/iam/users/me/tenants";
/** Delay > 5s to trigger AbortController timeout in fetchUserTenants */
const NETWORK_FAILURE_DELAY_MS = 6_000;
const SHELL_STORAGE_KEY = "vitalia-shell-state";
const SHELL_SPLIT_KEY = "vitalia-shell-split-agentic";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function seedShellLocalStorage(
  page: Page,
  theme: "light" | "dark" = "light",
): Promise<void> {
  const shellState = JSON.stringify({
    state: { shellMode: "agentic", valeriaState: "full" },
    version: 0,
  });
  const splitState = JSON.stringify([50, 50]);

  await page.addInitScript(
    ({ shellKey, splitKey, shellStateStr, splitStr, themeKey, themeValue }) => {
      localStorage.setItem(shellKey, shellStateStr);
      localStorage.setItem(splitKey, splitStr);
      localStorage.setItem(themeKey, themeValue);
      localStorage.setItem("__vitalia_e2e__", "true");
    },
    {
      shellKey: SHELL_STORAGE_KEY,
      splitKey: SHELL_SPLIT_KEY,
      shellStateStr: shellState,
      splitStr: splitState,
      themeKey: "vitalia-theme",
      themeValue: theme,
    },
  );
}

// ---------------------------------------------------------------------------
// Route mock helpers (attached to page, not fixture — call in test body)
// ---------------------------------------------------------------------------

/**
 * Mock GET /api/v1/iam/users/me/tenants to return a specific tenant list.
 * Call BEFORE navigation.
 */
export async function mockTenants(
  page: Page,
  tenants: TenantStub[],
): Promise<void> {
  await page.route(TENANTS_ENDPOINT, (route) => {
    void route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(tenants),
    });
  });
}

/**
 * Mock GET /api/v1/iam/users/me/tenants to simulate a network timeout.
 * Uses a long delay + 504 to trigger AbortError on the client.
 * Call BEFORE navigation.
 */
export async function mockTenantFetchFailure(
  page: Page,
  delayMs: number = NETWORK_FAILURE_DELAY_MS,
): Promise<void> {
  await page.route(TENANTS_ENDPOINT, async (route) => {
    await new Promise((resolve) => setTimeout(resolve, delayMs));
    await route.fulfill({
      status: 504,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Gateway Timeout" }),
    });
  });
}

/**
 * Mock GET /api/v1/iam/users/me/tenants to return an empty array.
 * Used for SC-8 (user authenticated but no tenants assigned).
 * Call BEFORE navigation.
 */
export async function mockNoTenants(page: Page): Promise<void> {
  await mockTenants(page, []);
}

/**
 * Mock GET /api/v1/iam/users/me/tenants to return a single-tenant list
 * that does NOT include the target tenantId (cross-tenant scenario SC-4).
 */
export async function mockCrossTenantList(
  page: Page,
  validTenant: TenantStub,
): Promise<void> {
  await mockTenants(page, [validTenant]);
}

// ---------------------------------------------------------------------------
// Extended test fixture
// ---------------------------------------------------------------------------

export const test = base.extend<RoutingShellFixtures>({
  /**
   * shellPage: authenticated page with deterministic light shell state.
   */
  shellPage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, "light");
    await use(authedPage);
  },

  /**
   * darkShellPage: authenticated page with dark theme for visual golden specs.
   */
  darkShellPage: async ({ authedPage }, use) => {
    await seedShellLocalStorage(authedPage, "dark");
    await use(authedPage);
  },
});

export { expect };
