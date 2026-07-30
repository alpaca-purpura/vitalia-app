/**
 * tenant-switcher-modal.smoke.spec.ts — SC-07 AddClinicPlaceholderModal
 * F1-S3 vitalia-fase1-tenant-switcher — T-9
 *
 * Tests:
 * - SC-07: "Agregar clínica" opens modal with "Próximamente" title + "Entendido" closes it
 *
 * 01-spec.md § 4 — AddClinicPlaceholderModal microcopy verbatim.
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

test.describe("SC-07 — AddClinicPlaceholderModal (F1-S3)", () => {
  test.beforeEach(async ({ page }) => {
    await mockTenantsApi(page, ACTIVE_TENANT.id);
  });

  test("SC-07: Agregar clínica opens modal with Próximamente title", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, {
      waitUntil: "domcontentloaded",
    });
    const pom = new TenantSwitcherPage(page);

    await pom.openDropdown();
    await pom.openAddClinicModal();

    // Modal title
    await expect(
      page.getByRole("heading", { name: "Próximamente" }),
    ).toBeVisible();

    // Modal body text
    await expect(
      page.getByText(
        "Próximamente: agregar nueva clínica desde Configurar → Mi cuenta",
      ),
    ).toBeVisible();
  });

  test("SC-07b: Entendido button closes the modal", async ({ page }) => {
    await page.goto(TEST_PAGE, {
      waitUntil: "domcontentloaded",
    });
    const pom = new TenantSwitcherPage(page);

    await pom.openDropdown();
    await pom.openAddClinicModal();

    // Close via Entendido button
    await pom.closeAddClinicModal();
    await expect(pom.addClinicModal).not.toBeVisible();
  });

  test("SC-07c: Modal close button has data-testid='add-clinic-modal-close'", async ({
    page,
  }) => {
    await page.goto(TEST_PAGE, {
      waitUntil: "domcontentloaded",
    });
    const pom = new TenantSwitcherPage(page);

    await pom.openDropdown();
    await pom.openAddClinicModal();

    await expect(pom.addClinicModalClose).toBeVisible();
    await expect(pom.addClinicModalClose).toHaveText("Entendido");
  });
});
