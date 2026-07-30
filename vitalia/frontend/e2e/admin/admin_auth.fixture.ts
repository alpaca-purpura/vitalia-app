/**
 * admin_auth.fixture.ts — Playwright fixture for Vitalia admin panel (Streamlit).
 *
 * Authenticates against the Streamlit admin panel (port 8502) using bcrypt
 * password auth. NOT Clerk — admin panel uses its own password gate.
 *
 * SECURITY: VITALIA_ADMIN_PASSWORD NEVER hardcoded. Injected via env var.
 * Tests that require this fixture SKIP if env var is absent.
 *
 * Per e2e-testing.md: native Playwright on Linux host. Port 8502 (admin).
 * Run: E2E_ADMIN_BASE_URL=http://localhost:8502 VITALIA_ADMIN_PASSWORD=... npx playwright test e2e/admin/ --project=admin-smoke
 *
 * downstream-regression-na: brand-local E2E fixture; no cross-brand consumers
 */

import { test as base, expect, type Page } from "@playwright/test";

export type AdminFixtures = {
  /** Authenticated Streamlit admin page. Skips if VITALIA_ADMIN_PASSWORD absent. */
  authenticatedAdminPage: Page;
};

const ADMIN_BASE_URL =
  process.env["E2E_ADMIN_BASE_URL"] ?? "http://127.0.0.1:8502";
const ADMIN_PASSWORD = process.env["VITALIA_ADMIN_PASSWORD"] ?? "";

/**
 * Navigate to admin panel and handle Streamlit password gate if present.
 */
async function loginToAdmin(page: Page): Promise<void> {
  await page.goto(ADMIN_BASE_URL, { waitUntil: "domcontentloaded" });

  // Streamlit password auth shows an input[type=password]
  const passwordInput = page.locator('input[type="password"]');
  const isPasswordRequired = await passwordInput
    .isVisible({ timeout: 8_000 })
    .catch(() => false);

  if (isPasswordRequired && ADMIN_PASSWORD) {
    await passwordInput.fill(ADMIN_PASSWORD);
    // Streamlit submit button for password form
    const loginBtn = page.locator(
      'button[kind="primaryFormSubmit"], button:has-text("Log in"), button:has-text("Ingresar"), button:has-text("Entrar")',
    );
    await loginBtn.first().click();
    // Wait for sidebar to appear — indicates successful login
    await page.waitForSelector('[data-testid="stSidebar"]', {
      timeout: 20_000,
    });
  } else if (!isPasswordRequired) {
    // No password gate — app loaded directly
    await page
      .waitForLoadState("networkidle", { timeout: 20_000 })
      .catch(() => {});
  }
}

export const test = base.extend<AdminFixtures>({
  authenticatedAdminPage: async ({ page }, use) => {
    if (!ADMIN_PASSWORD) {
      test.skip(
        true,
        "VITALIA_ADMIN_PASSWORD env var required for admin-smoke tests. " +
          "Set it and run: E2E_ADMIN_BASE_URL=http://127.0.0.1:8502 " +
          "VITALIA_ADMIN_PASSWORD=... npx playwright test e2e/admin/ --project=admin-smoke",
      );
      return;
    }
    await loginToAdmin(page);
    await use(page);
  },
});

export { expect };
export { ADMIN_BASE_URL };
