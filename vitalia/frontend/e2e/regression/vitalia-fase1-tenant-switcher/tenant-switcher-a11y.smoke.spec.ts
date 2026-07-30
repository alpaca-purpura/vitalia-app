/**
 * tenant-switcher-a11y.smoke.spec.ts — SC-08 accessibility
 * F1-S3 vitalia-fase1-tenant-switcher — T-9
 *
 * Tests:
 * - SC-08: Trigger is keyboard accessible (Tab focus + Enter opens dropdown)
 * - SC-08b: Trigger title attribute provides tooltip for screen readers
 * - SC-08c: Active tenant shows sr-only "Clínica activa" text
 *
 * 01-spec.md § 8 — Accessibility requirements.
 * Project: smoke
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
const ACTIVE_TENANT = TENANT_FIXTURES.sonrisaPlena;

test.describe("SC-08 — TenantSwitcher accessibility (F1-S3)", () => {
  test.beforeEach(async ({ page }) => {
    await mockTenantsApi(page, ACTIVE_TENANT.id);
  });

  test("SC-08: Trigger is focusable and has aria-label", async ({ page }) => {
    await page.goto(TEST_PAGE, {
      waitUntil: "domcontentloaded",
    });
    const pom = new TenantSwitcherPage(page);

    // Focus the trigger via keyboard
    await pom.trigger.focus();
    await expect(pom.trigger).toBeFocused();
    await expect(pom.trigger).toHaveAttribute("aria-label", "Cambiar clínica");
  });

  test("SC-08b: Trigger title attribute shows active tenant name", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, {
      waitUntil: "domcontentloaded",
    });
    const pom = new TenantSwitcherPage(page);

    const title = await pom.getTriggerTitle();
    expect(title).toBe(ACTIVE_TENANT.name);
  });

  test("SC-08c: Active tenant option has sr-only 'Clínica activa' text", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, {
      waitUntil: "domcontentloaded",
    });
    const pom = new TenantSwitcherPage(page);

    await pom.openDropdown();

    const activeOption = pom.tenantOption(ACTIVE_TENANT.id);
    const srOnly = activeOption.locator(".sr-only");
    // sr-only text should be present in DOM even if visually hidden
    await expect(srOnly).toHaveText("Clínica activa");
  });

  test("SC-08d: Enter key on trigger opens dropdown", async ({ page }) => {
    await page.goto(TEST_PAGE, {
      waitUntil: "domcontentloaded",
    });
    const pom = new TenantSwitcherPage(page);

    await pom.trigger.focus();
    await page.keyboard.press("Enter");

    await expect(pom.dropdown).toBeVisible();
  });
});
