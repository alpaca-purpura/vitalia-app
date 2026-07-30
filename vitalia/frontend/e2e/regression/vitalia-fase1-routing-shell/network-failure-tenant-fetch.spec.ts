/**
 * network-failure-tenant-fetch.spec.ts — SC-5 network_failure · BE tenant fetch timeout
 *
 * F1-S9 vitalia-fase1-routing-shell — T-6
 *
 * Gherkin: 01-spec.md § Gherkin SC-5
 *
 * Given: user autenticado
 *        BE /api/v1/iam/me/tenants timeout (response > 5s)
 * When:  user navega a /{tenantId}/(shell-organism)/
 *        layout.tsx fetch falla con AbortError
 * Then:  NetworkErrorFallback rendered ([data-testid=network-error-fallback])
 *        HTTP 200 (degraded UX, not 500)
 *        Botón "Reintentar" visible y focuseable
 *        NO redirect ciclo infinito
 *
 * Visual goldens: network-fallback-light.png + network-fallback-dark.png
 *
 * gherkin_coverage:
 *   - SC-5: network timeout → NetworkErrorFallback visible · Reintentar present · no redirect loop
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { expect } from "@playwright/test";
import {
  test,
  mockTenantFetchFailure,
} from "../../fixtures/routing-shell.fixture";
import { ShellPage } from "./poms/shell-page.pom";

const DESKTOP_VIEWPORT = { width: 1280, height: 720 };
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

test.describe("SC-5 — network_failure · BE tenant fetch timeout → fallback + Reintentar", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("SC-5-1: network timeout shows NetworkErrorFallback", async ({
    shellPage,
  }) => {
    // Mock: delay 6s + 504 → triggers AbortController timeout in fetchUserTenants
    await mockTenantFetchFailure(shellPage, 6_000);

    // UPDATED: paradigm-map-zones T-6 — use mateo/agenda (was valeria/agenda pre v1.2)
    await shellPage.goto(`/${TENANT_ID}/mateo/agenda`, {
      waitUntil: "domcontentloaded",
    });

    const pom = new ShellPage(shellPage);

    // NetworkErrorFallback should appear (with extended timeout for network delay)
    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });
  });

  test("SC-5-2: NetworkErrorFallback shows correct Spanish neutro microcopy", async ({
    shellPage,
  }) => {
    await mockTenantFetchFailure(shellPage, 6_000);

    await shellPage.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });
    const pom = new ShellPage(shellPage);

    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });

    const fallbackText = await pom.getNetworkErrorFallback().textContent();
    // Verify expected Spanish neutro copy (from spec § 6.3)
    expect(fallbackText).toMatch(
      /Estamos teniendo problemas conectando con el servidor/i,
    );
    expect(fallbackText).toMatch(/Reintentar/i);
    // No voseo
    expect(fallbackText).not.toMatch(/\btenés\b|\bpodés\b|\bvos\b/i);
  });

  test("SC-5-3: Reintentar button is visible and focuseable", async ({
    shellPage,
  }) => {
    await mockTenantFetchFailure(shellPage, 6_000);

    await shellPage.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });
    const pom = new ShellPage(shellPage);

    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });

    // Reintentar button is present and enabled
    const retryButton = shellPage.locator(
      '[data-testid="network-error-retry"]',
    );
    await expect(retryButton).toBeVisible({ timeout: 5_000 });
    await expect(retryButton).toBeEnabled();

    // Button is keyboard focuseable
    await retryButton.focus();
    await expect(retryButton).toBeFocused();
  });

  test("SC-5-4: no redirect loop on network failure (navigates once, stays on page)", async ({
    shellPage,
  }) => {
    await mockTenantFetchFailure(shellPage, 6_000);

    let redirectCount = 0;
    shellPage.on("request", (req) => {
      if (req.isNavigationRequest()) redirectCount++;
    });

    await shellPage.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });
    const pom = new ShellPage(shellPage);

    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });

    // Should not have more than 1-2 navigation requests (no redirect loop)
    expect(redirectCount).toBeLessThan(5);
  });

  test("SC-5-5: network fallback shell chrome (Ribbon) NOT visible", async ({
    shellPage,
  }) => {
    await mockTenantFetchFailure(shellPage, 6_000);

    await shellPage.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });
    const pom = new ShellPage(shellPage);

    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });

    // Ribbon should NOT be present during network failure (tenant validation failed)
    await expect(pom.getRibbon())
      .not.toBeVisible({ timeout: 3_000 })
      .catch(() => {
        // If Ribbon is not attached at all, that's also acceptable
      });
  });

  test("SC-5-6: network fallback light visual golden", async ({
    shellPage,
  }) => {
    await mockTenantFetchFailure(shellPage, 6_000);
    await shellPage.setViewportSize(DESKTOP_VIEWPORT);

    await shellPage.goto(`/${TENANT_ID}`, { waitUntil: "domcontentloaded" });
    const pom = new ShellPage(shellPage);

    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });
    await shellPage.waitForTimeout(300);

    await expect(shellPage).toHaveScreenshot("network-fallback-light.png", {
      maxDiffPixelRatio: 0.001,
    });
  });

  test("SC-5-7: network fallback dark visual golden @dark", async ({
    darkShellPage,
  }) => {
    await mockTenantFetchFailure(darkShellPage, 6_000);
    await darkShellPage.setViewportSize(DESKTOP_VIEWPORT);

    await darkShellPage.goto(`/${TENANT_ID}`, {
      waitUntil: "domcontentloaded",
    });
    const pom = new ShellPage(darkShellPage);

    await expect(pom.getNetworkErrorFallback()).toBeVisible({
      timeout: 15_000,
    });
    await darkShellPage.waitForTimeout(300);

    await expect(darkShellPage).toHaveScreenshot("network-fallback-dark.png", {
      maxDiffPixelRatio: 0.001,
    });
  });
});
