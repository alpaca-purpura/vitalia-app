/**
 * network-failure.ts — page.route abort helper for grid timeout (SC-7)
 *
 * Simulates backend timeout for /api/v1/scheduling/agenda/grid endpoint.
 * React Query retries 3 times with exponential backoff, then renders EmptyState error.
 *
 * Usage in spec:
 *   import { setupGridNetworkFailure, clearNetworkFailure } from '../fixtures/network-failure';
 *   await setupGridNetworkFailure(page);
 *   // ...assertions on EmptyState error...
 *   await clearNetworkFailure(page);
 *
 * downstream-regression-na: brand-local vitalia E2E fixture
 *
 * @see 04-validators.yaml § test_construction_plan step 4
 * @see SC-7 network_failure scenario
 */

import type { Page, Route } from "@playwright/test";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

/** Milliseconds before abort (simulates server timeout) */
const ABORT_DELAY_MS = 100;

// ---------------------------------------------------------------------------
// Abort patterns
// ---------------------------------------------------------------------------

/**
 * Abort all requests to the agenda grid endpoint.
 * React Query will attempt 3 retries then show EmptyState error variant.
 */
export async function setupGridNetworkFailure(page: Page): Promise<void> {
  await page.route(
    "**/api/v1/scheduling/agenda/grid**",
    async (route: Route) => {
      // Small delay to let React Query start (avoids race with loading state)
      await new Promise((resolve) => setTimeout(resolve, ABORT_DELAY_MS));
      await route.abort("failed");
    },
  );
}

/**
 * Abort all requests to the agenda grid and aggregates endpoints.
 * Use for month view + day view combined failure scenario.
 */
export async function setupAllAgendaNetworkFailure(page: Page): Promise<void> {
  await page.route(
    "**/api/v1/scheduling/agenda/**",
    async (route: Route) => {
      await new Promise((resolve) => setTimeout(resolve, ABORT_DELAY_MS));
      await route.abort("failed");
    },
  );
}

/**
 * Abort initial grid requests, then restore on the Nth retry.
 * Useful for testing retry recovery flow.
 */
export async function setupTransientNetworkFailure(
  page: Page,
  failCount: number,
): Promise<void> {
  let callCount = 0;
  await page.route(
    "**/api/v1/scheduling/agenda/grid**",
    async (route: Route) => {
      callCount++;
      if (callCount <= failCount) {
        await new Promise((resolve) => setTimeout(resolve, ABORT_DELAY_MS));
        await route.abort("failed");
      } else {
        // Let through to real backend (or other mocks intercept)
        await route.continue();
      }
    },
  );
}

/**
 * Abort payment charge network (for SC-7 variant with payment timeout).
 */
export async function setupChargeNetworkFailure(page: Page): Promise<void> {
  await page.route(
    "**/api/v1/payments/charge",
    async (route: Route) => {
      if (route.request().method() === "POST") {
        await new Promise((resolve) => setTimeout(resolve, ABORT_DELAY_MS));
        await route.abort("failed");
      } else {
        await route.continue();
      }
    },
  );
}

/**
 * Remove all network failure mocks from the page.
 * Safe to call even if no mocks are registered.
 */
export async function clearNetworkFailure(page: Page): Promise<void> {
  await page.unrouteAll({ behavior: "ignoreErrors" });
}
