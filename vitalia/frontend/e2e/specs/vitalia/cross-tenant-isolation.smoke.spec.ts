/**
 * cross-tenant-isolation.smoke.spec.ts — V-V-17
 *
 * Validator: V-V-17 — Spec §3.1.D cross-tenant isolation verification
 * Fixture: aurora-dental-ar + checks data never leaks to mindful tenant
 * Flow: Logged as Aurora → attempt access to Mindful data → only Aurora data visible
 */
import { test, expect } from "../../fixtures/aurora-dental-ar.fixture";
import { MINDFUL_FIXTURE } from "../../fixtures/mindful-psych-cl.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Cross-Tenant Isolation (Aurora AR)", () => {
  test("V-V-17: Aurora tenant data does not include Mindful data", async ({
    auroraPage: page,
    aurora,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/brand-studio");

    // Aurora data visible
    await expect(page.getByText(aurora.clinicName)).toBeVisible({
      timeout: 10_000,
    });

    // Mindful data NOT visible (cross-tenant isolation)
    await expect(page.getByText(MINDFUL_FIXTURE.clinicName)).not.toBeVisible();
    await expect(
      page.getByText(MINDFUL_FIXTURE.doctors[0].name),
    ).not.toBeVisible();

    expect(consoleErrors).toHaveLength(0);
  });

  test("V-V-17: X-Tenant-ID header is Aurora tenant, not Mindful", async ({
    auroraPage: page,
    aurora,
  }) => {
    // Intercept API calls and verify correct tenant ID
    const capturedTenantIds: string[] = [];

    await page.route("**/api/**", async (route) => {
      const headers = route.request().headers();
      const tenantId = headers["x-tenant-id"];
      if (tenantId) {
        capturedTenantIds.push(tenantId);
      }
      await route.continue();
    });

    await page.goto("/brand-studio");
    await page.waitForLoadState("networkidle");

    // All requests should be for Aurora tenant, not Mindful
    for (const tenantId of capturedTenantIds) {
      expect(tenantId).not.toBe(MINDFUL_FIXTURE.tenantId);
      // Should match Aurora tenant ID or be the correct value from localStorage
      expect(tenantId).toBe(aurora.tenantId);
    }
  });

  test("V-V-17: treatments page only shows Aurora treatments", async ({
    auroraPage: page,
    aurora,
  }) => {
    await page.goto("/tratamientos");

    // Aurora patient name may appear
    // Mindful patient "Sofía Torres" must NOT appear
    await expect(page.getByText(MINDFUL_FIXTURE.patientName)).not.toBeVisible();
  });

  test("V-V-17: compliance events are tenant-scoped to Aurora", async ({
    auroraPage: page,
    aurora,
  }) => {
    await page.goto("/medical-compliance");

    // Aurora compliance: 347 events (not 52 from Mindful, not 1247 from Sanaré)
    await expect(page.getByText(/347/i)).toBeVisible({ timeout: 10_000 });

    // Mindful's total (52) should NOT appear
    await expect(page.getByText(/\b52\b/)).not.toBeVisible();
  });

  test("V-V-17: cross_tenant_attempt count shows 0 (no actual leak)", async ({
    auroraPage: page,
  }) => {
    await page.goto("/medical-compliance");

    // cross_tenant_attempt = 0 per Aurora fixture (no actual leak)
    await expect(
      page.getByText(/cross_tenant.*0|0.*cross_tenant/i),
    ).toBeVisible({
      timeout: 10_000,
    });
  });
});
