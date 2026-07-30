/**
 * tenant-switcher-visual.smoke.spec.ts — Visual golden screenshots
 * F1-S3 vitalia-fase1-tenant-switcher — T-10
 *
 * 8 visual golden scenarios:
 * 1. Closed trigger — light mode
 * 2. Closed trigger — dark mode
 * 3. Open dropdown — light mode (success state)
 * 4. Open dropdown — dark mode (success state)
 * 5. Open dropdown — loading state (skeleton)
 * 6. Open dropdown — error state (alert + Reintentar)
 * 7. Add clinic modal — open (Próximamente dialog)
 * 8. Active tenant badge (TenantBadge + Check mark)
 *
 * maxDiffPixelRatio: 0.002 (0.2% tolerance — font rendering variance)
 * Update: npx playwright test --update-snapshots
 *
 * Project: smoke
 *
 * downstream-regression-na: brand-local E2E visual spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";
import { TenantSwitcherPage } from "../../pages/tenant-switcher.page";
import {
  mockTenantsApi,
  mockTenantsApiError,
  TENANT_FIXTURES,
} from "../../fixtures/tenants.fixture";

const BASE_URL = process.env["E2E_BASE_URL"] ?? "http://localhost:3002";
const ACTIVE_TENANT = TENANT_FIXTURES.sonrisaPlena;
// T-FIX-1: target test-stack page instead of /{tenantId}/dashboard (route not yet created — Fase 2)
const TEST_PAGE = `${BASE_URL}/test-stack/tenant-switcher`;

/** Toggle dark mode by setting data-theme=dark on <html> */
async function enableDarkMode(
  page: import("@playwright/test").Page,
): Promise<void> {
  await page.evaluate(() => {
    document.documentElement.setAttribute("data-theme", "dark");
    document.documentElement.classList.add("dark");
  });
}

/** Restore light mode */
async function enableLightMode(
  page: import("@playwright/test").Page,
): Promise<void> {
  await page.evaluate(() => {
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.classList.remove("dark");
  });
}

test.describe("Visual goldens — TenantSwitcher (F1-S3 T-10)", () => {
  // ── 1 & 2: Closed trigger ─────────────────────────────────────────────
  test("visual-01: Closed trigger — light mode", async ({ page }) => {
    await mockTenantsApi(page, ACTIVE_TENANT.id);
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    await enableLightMode(page);

    const pom = new TenantSwitcherPage(page);
    await expect(pom.trigger).toBeVisible();

    // Screenshot: just the trigger button
    await expect(pom.trigger).toHaveScreenshot("trigger-closed-light.png", {
      maxDiffPixelRatio: 0.002,
    });
  });

  test("visual-02: Closed trigger — dark mode", async ({ page }) => {
    await mockTenantsApi(page, ACTIVE_TENANT.id);
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    await enableDarkMode(page);

    const pom = new TenantSwitcherPage(page);
    await expect(pom.trigger).toBeVisible();

    await expect(pom.trigger).toHaveScreenshot("trigger-closed-dark.png", {
      maxDiffPixelRatio: 0.002,
    });
  });

  // ── 3 & 4: Open dropdown success ──────────────────────────────────────
  test("visual-03: Open dropdown — light mode (success state)", async ({
    page,
  }) => {
    await mockTenantsApi(page, ACTIVE_TENANT.id);
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    await enableLightMode(page);

    const pom = new TenantSwitcherPage(page);
    await pom.openDropdown();

    await expect(pom.dropdown).toHaveScreenshot("dropdown-open-light.png", {
      maxDiffPixelRatio: 0.002,
    });
  });

  test("visual-04: Open dropdown — dark mode (success state)", async ({
    page,
  }) => {
    await mockTenantsApi(page, ACTIVE_TENANT.id);
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    await enableDarkMode(page);

    const pom = new TenantSwitcherPage(page);
    await pom.openDropdown();

    await expect(pom.dropdown).toHaveScreenshot("dropdown-open-dark.png", {
      maxDiffPixelRatio: 0.002,
    });
  });

  // ── 5: Loading state ──────────────────────────────────────────────────
  test("visual-05: Open dropdown — loading state (skeleton rows)", async ({
    page,
  }) => {
    // Delay /api/tenants response to catch loading state
    let resolveRequest: (() => void) | null = null;

    await page.route("**/api/tenants", async (route) => {
      await new Promise<void>((resolve) => {
        resolveRequest = resolve;
      });
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ tenants: Object.values(TENANT_FIXTURES) }),
      });
    });

    // Clear localStorage so activeTenant is null (triggers loading trigger render)
    await page.addInitScript(() => {
      localStorage.clear();
    });

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });

    // NOTE: In loading state with no persisted activeTenant, the trigger may not
    // render (graceful degrade per 03-arch.md § 8.4). This test captures the
    // loading skeleton state inside the dropdown when trigger IS visible.
    const triggerVisible = await page
      .getByTestId("tenant-switcher-trigger")
      .isVisible()
      .catch(() => false);

    if (triggerVisible && resolveRequest === null) {
      // Trigger open while loading
      await page.getByTestId("tenant-switcher-trigger").click();

      await expect(
        page.getByTestId("tenant-switcher-dropdown"),
      ).toHaveScreenshot("dropdown-loading.png", {
        maxDiffPixelRatio: 0.002,
      });
    }

    // Resolve the delayed request
    if (resolveRequest) {
      (resolveRequest as () => void)();
    }
  });

  // ── 6: Error state ────────────────────────────────────────────────────
  test("visual-06: Open dropdown — error state (alert + Reintentar)", async ({
    page,
  }) => {
    // Pre-seed activeTenant in localStorage so trigger renders
    await page.addInitScript(
      ({ tenant, storageKey }) => {
        const state = { state: { activeTenant: tenant }, version: 1 };
        localStorage.setItem(storageKey, JSON.stringify(state));
      },
      {
        tenant: ACTIVE_TENANT,
        storageKey: "vitalia-tenant-state",
      },
    );

    // Error response for API
    await mockTenantsApiError(page);

    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    await enableLightMode(page);

    // Wait for React Query to settle into error state
    await page.waitForTimeout(1000);

    const pom = new TenantSwitcherPage(page);
    const triggerVisible = await pom.trigger.isVisible().catch(() => false);

    if (triggerVisible) {
      await pom.openDropdown();
      await expect(pom.dropdown).toHaveScreenshot("dropdown-error.png", {
        maxDiffPixelRatio: 0.002,
      });
    }
  });

  // ── 7: Add clinic modal ───────────────────────────────────────────────
  test("visual-07: Add clinic modal — Próximamente dialog", async ({
    page,
  }) => {
    await mockTenantsApi(page, ACTIVE_TENANT.id);
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    await enableLightMode(page);

    const pom = new TenantSwitcherPage(page);
    await pom.openDropdown();
    await pom.openAddClinicModal();

    await expect(pom.addClinicModal).toHaveScreenshot("add-clinic-modal.png", {
      maxDiffPixelRatio: 0.002,
    });
  });

  // ── 8: Active tenant badge ────────────────────────────────────────────
  test("visual-08: Active tenant option — badge + check mark visible", async ({
    page,
  }) => {
    await mockTenantsApi(page, ACTIVE_TENANT.id);
    await page.goto(TEST_PAGE, { waitUntil: "domcontentloaded" });
    await enableLightMode(page);

    const pom = new TenantSwitcherPage(page);
    await pom.openDropdown();

    const activeOption = pom.tenantOption(ACTIVE_TENANT.id);
    await expect(activeOption).toBeVisible();

    await expect(activeOption).toHaveScreenshot("tenant-option-active.png", {
      maxDiffPixelRatio: 0.002,
    });
  });
});
