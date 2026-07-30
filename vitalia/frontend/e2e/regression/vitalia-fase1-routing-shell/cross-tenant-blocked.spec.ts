/**
 * cross-tenant-blocked.spec.ts — SC-4 adversarial · cross-tenant access blocked
 *
 * F1-S9 vitalia-fase1-routing-shell — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-4
 *
 * Given: user A con JWT tenant_id=clinic-A
 *        user A intenta acceder a /clinic-B/(shell-organism)/mateo/agenda (UPDATED v1.2)
 * When:  proxy.ts pasa request (auth Clerk válida)
 *        layout.tsx server-side fetch GET /api/v1/iam/me/tenants → [{id:"clinic-A"}]
 *        layout detecta params.tenantId="clinic-B" ∉ user.tenants
 * Then:  redirect a /clinic-A/mateo/agenda (UPDATED v1.2 default landing)
 *        browser final URL contains "clinic-A"
 *        NO chrome de clinic-B rendered
 *        audit log row emitted (HIPAA-lite: userId + attemptedTenant + timestamp, NO PHI)
 *
 * Note: Audit log DB assertion is omitted in E2E scope (no direct DB access in Playwright).
 *       The unit test in lib/iam/__tests__/audit.test.ts covers logCrossTenantAttempt.
 *
 * gherkin_coverage:
 *   - SC-4: cross-tenant attempt → redirect to valid tenant + no chrome leak
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import {
  test,
  mockCrossTenantList,
} from "../../fixtures/routing-shell.fixture";
import { ShellPage } from "./poms/shell-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 720 };
const TENANT_A = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";
const TENANT_B = "other-clinic-tenant-99";

test.describe("SC-4 — adversarial · cross-tenant access blocked", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-4-1: cross-tenant access redirects to valid first tenant", async ({
    shellPage,
  }) => {
    // Mock: user's tenant list = only TENANT_A (not TENANT_B)
    await mockCrossTenantList(shellPage, {
      id: TENANT_A,
      name: "Clínica Test",
    });

    // Attempt to access TENANT_B (user does not belong there)
    // UPDATED: paradigm-map-zones T-6 — use mateo/agenda (was valeria/agenda pre v1.2)
    await shellPage.goto(`/${TENANT_B}/mateo/agenda`);

    // Should redirect to TENANT_A (first valid tenant)
    await shellPage.waitForURL(`**/${TENANT_A}/**`, { timeout: 15_000 });

    // Final URL must NOT contain TENANT_B
    const finalUrl = shellPage.url();
    expect(finalUrl).not.toContain(TENANT_B);
    expect(finalUrl).toContain(TENANT_A);
  });

  test("SC-4-2: no clinic-B chrome rendered after redirect", async ({
    shellPage,
  }) => {
    await mockCrossTenantList(shellPage, {
      id: TENANT_A,
      name: "Clínica Test",
    });

    const pom = new ShellPage(shellPage);

    // UPDATED: paradigm-map-zones T-6 — use mateo/agenda (was valeria/agenda pre v1.2)
    await shellPage.goto(`/${TENANT_B}/mateo/agenda`);
    await shellPage.waitForURL(`**/${TENANT_A}/**`, { timeout: 15_000 });

    // Shell chrome should render for TENANT_A, not be blank or TENANT_B
    await pom.assertChromeVisible();

    // Verify no reference to TENANT_B in the DOM
    const bodyText = await shellPage.locator("body").textContent();
    // The body should not leak TENANT_B slug in user-visible elements
    // (layout titles, breadcrumbs, etc.)
    if (bodyText) {
      expect(bodyText).not.toContain(TENANT_B);
    }
  });

  test("SC-4-3: redirect lands on valid agent route within TENANT_A", async ({
    shellPage,
  }) => {
    await mockCrossTenantList(shellPage, { id: TENANT_A });

    await shellPage.goto(`/${TENANT_B}/lisa/marca`);
    await shellPage.waitForURL(`**/${TENANT_A}/**`, { timeout: 15_000 });

    // The shell should be functional at TENANT_A
    const pom = new ShellPage(shellPage);
    await pom.assertChromeVisible();
  });
});
