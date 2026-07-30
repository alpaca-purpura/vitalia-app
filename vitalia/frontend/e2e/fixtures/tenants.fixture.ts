/**
 * tenants.fixture.ts — Mock tenant data for TenantSwitcher E2E tests
 *
 * F1-S3 vitalia-fase1-tenant-switcher — T-9
 *
 * Provides realistic LatAm clinic tenant data for network mocking.
 * No Clerk Organizations — tenants via luana-core-iam (03-arch.md § 2.8).
 *
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

import type { Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Fixture tenant data (realistic LatAm clinics)
// ---------------------------------------------------------------------------

export const TENANT_FIXTURES = {
  sonrisaPlena: {
    id: "sonrisa-plena-mx",
    name: "Sonrisa Plena",
    city: "Ciudad de México",
  },
  dermalia: {
    id: "dermalia-mx",
    name: "Dermalia",
    city: "Guadalajara",
  },
  auroraWellness: {
    id: "aurora-wellness-ar",
    name: "Aurora Wellness",
    city: "Buenos Aires",
  },
} as const;

export type TenantFixtureKey = keyof typeof TENANT_FIXTURES;

/**
 * Mock the /api/tenants endpoint with fixture data.
 * Simulates the bootstrap call from useTenants hook.
 */
export async function mockTenantsApi(
  page: Page,
  activeTenantId: string = TENANT_FIXTURES.sonrisaPlena.id,
): Promise<void> {
  await page.route("**/api/tenants", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        tenants: Object.values(TENANT_FIXTURES),
      }),
    });
  });

  // Pre-seed localStorage with active tenant to simulate persisted state
  await page.addInitScript(
    ({ tenantId, tenants, storageKey }) => {
      const state = {
        state: {
          activeTenant:
            tenants.find((t: { id: string }) => t.id === tenantId) ??
            tenants[0],
        },
        version: 1,
      };
      localStorage.setItem(storageKey, JSON.stringify(state));
    },
    {
      tenantId: activeTenantId,
      tenants: Object.values(TENANT_FIXTURES),
      storageKey: "vitalia-tenant-state",
    },
  );
}

/**
 * Mock /api/tenants to return an empty list (no tenants scenario).
 */
export async function mockEmptyTenantsApi(page: Page): Promise<void> {
  await page.route("**/api/tenants", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ tenants: [] }),
    });
  });

  // Clear localStorage to simulate no persisted state
  await page.addInitScript(() => {
    localStorage.removeItem("vitalia-tenant-state");
  });
}

/**
 * Mock /api/tenants to return a server error (error state scenario).
 */
export async function mockTenantsApiError(page: Page): Promise<void> {
  await page.route("**/api/tenants", async (route) => {
    await route.fulfill({
      status: 500,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Internal server error" }),
    });
  });

  // Clear localStorage to simulate no persisted state
  await page.addInitScript(() => {
    localStorage.removeItem("vitalia-tenant-state");
  });
}
