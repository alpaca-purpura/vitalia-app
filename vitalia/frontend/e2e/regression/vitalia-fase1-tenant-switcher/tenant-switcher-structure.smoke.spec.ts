/**
 * tenant-switcher-structure.smoke.spec.ts — SC-01, SC-02 structure regression
 * F1-S3 vitalia-fase1-tenant-switcher — T-9
 *
 * Tests:
 * - SC-01: Trigger renders with aria-label="Cambiar clínica"
 * - SC-02: Trigger opens dropdown containing "MIS CLÍNICAS" header
 *
 * Project: smoke (playwright.config.ts — *.smoke.spec.ts pattern)
 * Requires: dev server running at E2E_BASE_URL + authenticated session
 *
 * Network mocking: /api/tenants mocked via page.route() using TENANT_FIXTURES.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-fase1-tenant-switcher/tenant-switcher-structure.smoke.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";
import { TenantSwitcherPage } from "../../pages/tenant-switcher.page";
import {
  mockTenantsApi,
  TENANT_FIXTURES,
} from "../../fixtures/tenants.fixture";

const BASE_URL = process.env["E2E_BASE_URL"] ?? "http://localhost:3002";
// T-FIX-1: target test-stack page instead of /{tenantId}/dashboard (route not yet created — Fase 2)
const TEST_PAGE = `${BASE_URL}/test-stack/tenant-switcher`;

test.describe("SC-01..SC-02 — TenantSwitcher structure (F1-S3)", () => {
  test.beforeEach(async ({ page }) => {
    await mockTenantsApi(page, TENANT_FIXTURES.sonrisaPlena.id);
  });

  test("SC-01: Trigger has aria-label='Cambiar clínica'", async ({ page }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    const pom = new TenantSwitcherPage(page);

    await expect(pom.trigger).toBeVisible();
    const ariaLabel = await pom.getTriggerAriaLabel();
    expect(ariaLabel).toBe("Cambiar clínica");
  });

  test("SC-01b: Trigger has data-testid='tenant-switcher-trigger'", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    const pom = new TenantSwitcherPage(page);

    await expect(pom.trigger).toBeVisible();
  });

  test("SC-02: Opening dropdown shows 'MIS CLÍNICAS' header", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    const pom = new TenantSwitcherPage(page);

    await pom.openDropdown();
    await expect(pom.headerLabel).toBeVisible();
  });

  test("SC-02b: Dropdown contains list of tenant options", async ({ page }) => {
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    const pom = new TenantSwitcherPage(page);

    await pom.openDropdown();

    // All fixture tenants should be rendered
    for (const tenant of Object.values(TENANT_FIXTURES)) {
      await expect(pom.tenantOption(tenant.id)).toBeVisible();
    }
  });
});
