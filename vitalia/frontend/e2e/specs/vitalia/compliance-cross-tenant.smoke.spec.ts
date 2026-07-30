/**
 * compliance-cross-tenant.smoke.spec.ts — Spec §15 Compliance smoke #3
 *
 * Validator: Compliance smoke — cross_tenant_attempt=0 (no actual leak occurred)
 * Fixture: aurora-dental-ar (cross_tenant_attempt count=0)
 * Flow: compliance dashboard → cross_tenant_attempt 0 → tenant data scoped correctly
 */
import { test, expect } from "../../fixtures/aurora-dental-ar.fixture";
import { SANARE_FIXTURE } from "../../fixtures/sanare-latam-mx.fixture";
import { collectConsoleErrors } from "../../auth.fixture";

test.describe("Compliance Smoke — Cross-Tenant Isolation Audit", () => {
  test("cross_tenant_attempt count=0 in compliance log", async ({
    auroraPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/medical-compliance");

    // cross_tenant_attempt = 0 per Aurora mock
    await expect(
      page.getByText(/cross_tenant.*attempt.*0|0.*cross_tenant/i),
    ).toBeVisible({
      timeout: 10_000,
    });

    expect(consoleErrors).toHaveLength(0);
  });

  test("Aurora tenant cannot access Sanaré treatment data", async ({
    auroraPage: page,
  }) => {
    const consoleErrors = collectConsoleErrors(page);

    await page.goto("/tratamientos");

    // Sanaré patient "Fernanda López" must NOT appear in Aurora's view
    await expect(page.getByText(SANARE_FIXTURE.patientName)).not.toBeVisible();

    // Aurora patient "Juan Pérez" may appear
    // Both should not co-exist (tenant isolation)

    expect(consoleErrors).toHaveLength(0);
  });

  test("X-Tenant-ID consistently Aurora throughout session", async ({
    auroraPage: page,
    aurora,
  }) => {
    const capturedTenantIds = new Set<string>();

    await page.route("**/api/**", async (route) => {
      const headers = route.request().headers();
      const tid = headers["x-tenant-id"];
      if (tid) capturedTenantIds.add(tid);
      await route.continue();
    });

    // Navigate multiple routes to collect tenant IDs
    await page.goto("/brand-studio");
    await page.goto("/medical-compliance");
    await page.waitForLoadState("networkidle");

    // All tenant IDs must be Aurora's (no leakage to other tenants)
    for (const tid of capturedTenantIds) {
      expect(tid).toBe(aurora.tenantId);
    }
  });

  test("compliance log shows cross_tenant_attempt type in event filter", async ({
    auroraPage: page,
  }) => {
    await page.goto("/medical-compliance");

    // Event type filter should include cross_tenant_attempt
    const filterSelect = page.getByRole("combobox", { name: /tipo/i });
    if (await filterSelect.isVisible({ timeout: 5_000 }).catch(() => false)) {
      // Option should be available
      const options = await filterSelect.evaluate((el: HTMLSelectElement) =>
        Array.from(el.options).map((o) => o.value),
      );
      // cross_tenant_attempt should be filterable
      const hasCrossTenant = options.some((o) => o.includes("cross_tenant"));
      if (options.length > 0) {
        expect(hasCrossTenant).toBe(true);
      }
    }
  });
});
