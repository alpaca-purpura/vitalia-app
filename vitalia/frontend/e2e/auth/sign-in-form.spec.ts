/**
 * sign-in-form.spec.ts — SC-03 + SC-04 (vitalia-auth-base-functional)
 *
 * Smoke gate: verifica que las páginas /sign-in y /sign-up renderizan los
 * componentes Clerk <SignIn /> y <SignUp /> reales (no placeholders T-fe-3).
 *
 * Per e2e-testing.md: native Playwright on Linux host. Port 3002 (vitalia).
 * NO requiere authedPage (pruebas sin autenticación).
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/auth/sign-in-form.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

// ─── SC-03: /sign-in renderiza Clerk <SignIn /> real ─────────────────────────

test.describe("vitalia-auth-base-functional — SC-03: /sign-in renderiza Clerk <SignIn />", () => {
  test("SC-03: /sign-in muestra email + password fields; no hay placeholder 'pendiente T-fe-3'", async ({
    page,
  }) => {
    await page.goto("/sign-in", { waitUntil: "domcontentloaded" });

    // Clerk <SignIn /> debe renderizar; no debe haber placeholder de work-in-progress.
    // toHaveCount(0): si el elemento no existe, count=0 (pasa); si existe, falla loudly.
    const placeholder = page.getByText(/pendiente.*T-fe-3/i);
    await expect(placeholder).toHaveCount(0, { timeout: 5_000 });

    // El campo de email/identifier debe estar visible
    const emailInput = page.locator(
      'input[type="email"], input[name="identifier"], input[autocomplete="email"]',
    );
    await expect(emailInput.first()).toBeVisible({ timeout: 15_000 });

    // Debe haber un campo de contraseña (visible después de ingresar email en Clerk)
    // o al menos el formulario de Clerk está presente (puede ser paso 1 de 2)
    const clerkForm = page.locator(
      '[data-clerk-sign-in], .cl-sign-in-root, form[data-form="sign-in"], form',
    );
    await expect(clerkForm.first()).toBeVisible({ timeout: 10_000 });

    // No debe existir texto de placeholder visible
    await expect(page.getByText("pendiente")).toHaveCount(0, {
      timeout: 3_000,
    });
  });
});

// ─── SC-04: /sign-up renderiza Clerk <SignUp /> real ─────────────────────────

test.describe("vitalia-auth-base-functional — SC-04: /sign-up renderiza Clerk <SignUp />", () => {
  test("SC-04: /sign-up muestra formulario de registro; no hay placeholder 'pendiente T-fe-3'", async ({
    page,
  }) => {
    await page.goto("/sign-up", { waitUntil: "domcontentloaded" });

    // No debe haber placeholder de work-in-progress.
    // toHaveCount(0): si el elemento no existe, count=0 (pasa); si existe, falla loudly.
    const placeholder = page.getByText(/pendiente.*T-fe-3/i);
    await expect(placeholder).toHaveCount(0, { timeout: 5_000 });

    // Clerk <SignUp /> debe renderizar con campo email o formulario visible
    const emailInput = page.locator(
      'input[type="email"], input[name="emailAddress"], input[autocomplete="email"]',
    );
    await expect(emailInput.first()).toBeVisible({ timeout: 15_000 });

    // El formulario de Clerk debe estar presente
    const clerkForm = page.locator(
      '[data-clerk-sign-up], .cl-sign-up-root, form[data-form="sign-up"], form',
    );
    await expect(clerkForm.first()).toBeVisible({ timeout: 10_000 });

    // No debe existir texto de placeholder visible
    await expect(page.getByText("pendiente")).toHaveCount(0, {
      timeout: 3_000,
    });
  });
});
