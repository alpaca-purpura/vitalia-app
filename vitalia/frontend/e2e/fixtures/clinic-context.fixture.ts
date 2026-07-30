/**
 * clinic-context.fixture.ts — Clinic context fixture for fidelización E2E tests
 *
 * Sanaré MX clinic context: dental+orthodontics multi-session clinic.
 * Used by fidelización smoke + regression specs.
 *
 * Network: all API calls mocked via page.route() — no live stack required.
 * Auth: extends auth.fixture.ts (Clerk testing token bypass).
 *
 * Clerk org activation: injects a script that calls window.Clerk.setActive()
 * with E2E_CLERK_ORG_ID (the test organization created for E2E) so that
 * useAuth().orgId is populated. Required because API hooks use orgId as tenantId.
 *
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

import { test as base } from "../auth.fixture";
import type { Page } from "@playwright/test";

// ---------------------------------------------------------------------------
// Clinic context constants
// ---------------------------------------------------------------------------

/**
 * Clerk organization ID for the E2E test organization.
 * Created via Clerk API: org_3DzUI3lLjwX83Kth0j5enWrjIDY
 * This is the `orgId` that useAuth() will return after setActive().
 * Used as X-Tenant-ID header in all API calls.
 */
export const E2E_CLERK_ORG_ID =
  process.env["E2E_CLERK_ORG_ID"] ?? "org_3DzUI3lLjwX83Kth0j5enWrjIDY";

export const CLINIC_CONTEXT = {
  tenantId: process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant",
  /** Clerk orgId used as tenantId in API headers (useAuth().orgId) */
  clerkOrgId: E2E_CLERK_ORG_ID,
  clinicId: "sanare-mx-dental-001",
  clinicName: "Sanaré MX — Ortodoncia y Dental",
  clinicType: "dental" as const,
  country: "MX",
  city: "Ciudad de México",
  currency: "MXN",
  doctors: [
    {
      id: "dr-ortiz-mx",
      name: "Dr. Carlos Ortiz",
      specialty: "Ortodoncia",
    },
    {
      id: "dr-vega-mx",
      name: "Dra. Laura Vega",
      specialty: "Odontología general",
    },
  ],
  /** Default tenant JWT context (mocked — no live Clerk required) */
  mockUserId: "user_e2e_admin_clinic_001",
  mockUserRole: "admin_clinic" as const,
} as const;

// ---------------------------------------------------------------------------
// Fixture type
// ---------------------------------------------------------------------------

export type ClinicContextFixtures = {
  /** Pre-authenticated page scoped to Sanaré MX dental clinic */
  clinicPage: Page;
  /** Clinic context data */
  clinic: typeof CLINIC_CONTEXT;
};

// ---------------------------------------------------------------------------
// Mock: tenant + clinic identity endpoints
// ---------------------------------------------------------------------------

export async function setupClinicContextMocks(page: Page): Promise<void> {
  // Mock: tenant profile
  await page.route("**/api/v1/vitalia/tenant/profile", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        tenant_id: CLINIC_CONTEXT.tenantId,
        clinic_id: CLINIC_CONTEXT.clinicId,
        clinic_name: CLINIC_CONTEXT.clinicName,
        clinic_type: CLINIC_CONTEXT.clinicType,
        country: CLINIC_CONTEXT.country,
        currency: CLINIC_CONTEXT.currency,
      }),
    });
  });

  // Mock: current user (admin_clinic role — PHI access permitted)
  await page.route("**/api/v1/vitalia/iam/me", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        user_id: CLINIC_CONTEXT.mockUserId,
        role: CLINIC_CONTEXT.mockUserRole,
        clinic_id: CLINIC_CONTEXT.clinicId,
        tenant_id: CLINIC_CONTEXT.tenantId,
      }),
    });
  });

  // Mock: doctors list
  await page.route("**/api/v1/vitalia/doctors**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        doctors: CLINIC_CONTEXT.doctors,
      }),
    });
  });
}

// ---------------------------------------------------------------------------
// Fixture extension
// ---------------------------------------------------------------------------

export const test = base.extend<ClinicContextFixtures>({
  // eslint-disable-next-line no-empty-pattern -- Playwright fixture signature requires destructuring
  clinic: async ({}, use) => {
    await use(CLINIC_CONTEXT);
  },

  clinicPage: async ({ authedPage }, use) => {
    // Scope tenant + clinic via localStorage injection
    await authedPage.addInitScript(
      ({ tid, cid, orgId }: { tid: string; cid: string; orgId: string }) => {
        localStorage.setItem("x-tenant-id", tid);
        localStorage.setItem("x-clinic-id", cid);
        localStorage.setItem("__vitalia_e2e__", "true");

        // Activate Clerk organization so useAuth().orgId is populated.
        // API hooks use orgId as X-Tenant-ID. Poll until Clerk is ready then setActive.
        const activateOrg = () => {
          const w = window as typeof window & {
            Clerk?: {
              loaded?: boolean;
              setActive?: (opts: { organization: string }) => Promise<void>;
              session?: unknown;
            };
          };
          if (w.Clerk?.loaded && typeof w.Clerk.setActive === "function") {
            w.Clerk.setActive({ organization: orgId }).catch(() => {
              // best-effort — Clerk may reject if org not found in dev
            });
          } else {
            setTimeout(activateOrg, 100);
          }
        };
        // Start polling after minimal delay (DOM + Clerk init)
        setTimeout(activateOrg, 200);
      },
      {
        tid: CLINIC_CONTEXT.tenantId,
        cid: CLINIC_CONTEXT.clinicId,
        orgId: E2E_CLERK_ORG_ID,
      },
    );

    await setupClinicContextMocks(authedPage);

    await use(authedPage);
  },
});

export { expect } from "../auth.fixture";
