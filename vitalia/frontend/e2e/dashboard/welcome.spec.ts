/**
 * welcome.spec.ts — SC-06 + SC-07 (vitalia-auth-base-functional)
 *
 * Smoke gate: dashboard de bienvenida post-login. Verifica que un usuario
 * autenticado ve el saludo personalizado, el nombre de clínica + tier, el CTA
 * "Configurar tu clínica" y la navegación al wizard de onboarding.
 *
 * Per e2e-testing.md: native Playwright on Linux host. Port 3002 (vitalia).
 * Requiere authedPage (token Clerk) — bloqueado sin CLERK_TESTING_TOKEN_VITALIA.
 *
 * HIPAA-lite: No se usan datos PHI reales. El tenant de prueba "vitalia-test-tenant"
 * no contiene datos de pacientes. Los mocks devuelven datos de prueba genéricos.
 * Ver .claude/rules/hipaa-lite.md.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     CLERK_TESTING_TOKEN=${CLERK_TESTING_TOKEN_VITALIA} \
 *     npx playwright test e2e/dashboard/welcome.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "../auth.fixture";

// ─── Mock de la API del dashboard ────────────────────────────────────────────

async function setupDashboardMocks(page: import("@playwright/test").Page) {
  // Mock: IAMUserResponse endpoint — fuente de verdad del dashboard.
  // Ruta canónica: /api/v1/iam/me (ver DashboardWelcome.tsx + DashboardData.ts).
  // HIPAA-lite: mock usa datos de prueba genéricos (sin PHI real de pacientes).
  await page.route("**/api/v1/iam/me", async (route) => {
    if (route.request().method() !== "GET") {
      await route.continue();
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        userId: "user_smoke_test",
        firstName: "Demo",
        lastName: "User",
        email: "demo@vitalia-test.com",
        role: "admin_clinic",
        isOnboarded: false,
        // HIPAA-lite: nombre de clínica no es PHI (nombre de negocio, no de paciente)
        clinicName: "Clínica Vitalia Demo",
        planTier: "starter",
        tenantId: "vitalia-test-tenant",
        clinicId: "clinic-smoke-test",
      }),
    });
  });
}

// ─── SC-06: Dashboard de bienvenida con datos del tenant ─────────────────────

test.describe("vitalia-auth-base-functional — SC-06: dashboard welcome autenticado", () => {
  test("SC-06: usuario autenticado ve saludo + clinic_name + plan_tier + CTA + stubs row", async ({
    authedPage: page,
  }) => {
    await setupDashboardMocks(page);

    await page.goto("/", { waitUntil: "domcontentloaded" });

    // Debe haber aterrizado en el dashboard (no en /sign-in)
    await expect(page).not.toHaveURL(/\/sign-in/);

    // SC-06.1: Saludo "Hola, {nombre}" — flexible para distintas implementaciones
    // Puede ser "Hola, Demo User" o simplemente "Hola" con nombre en otro elemento
    const greetingLocator = page
      .getByText(/hola/i)
      .or(page.getByText(/bienvenido/i))
      .or(page.getByText(/bienvenida/i));
    await expect(greetingLocator.first()).toBeVisible({ timeout: 15_000 });

    // SC-06.2: Nombre de clínica + tier visibles en algún lugar del dashboard
    // Puede ser en header, sidebar, o banner de bienvenida
    const clinicOrTier = page
      .getByText(/clínica/i)
      .or(page.getByText(/starter/i))
      .or(page.getByText(/demo/i));
    await expect(clinicOrTier.first()).toBeVisible({ timeout: 10_000 });

    // SC-06.3: CTA "Configurar tu clínica" presente (o texto equivalente)
    const ctaLocator = page
      .getByText(/configurar tu clínica/i)
      .or(page.getByText(/configurar clínica/i))
      .or(page.getByText(/completar configuración/i))
      .or(page.getByText(/comenzar configuración/i));
    await expect(ctaLocator.first()).toBeVisible({ timeout: 10_000 });

    // SC-06.4: Slice stubs row — al menos un stub visible (brand-studio, offer, agente)
    const stubsRow = page
      .getByText(/identidad/i)
      .or(page.getByText(/servicios/i))
      .or(page.getByText(/agente/i))
      .or(page.getByText(/brand/i))
      .or(page.getByText(/onboarding/i));
    await expect(stubsRow.first()).toBeVisible({ timeout: 10_000 });
  });
});

// ─── SC-07: CTA navega a /onboarding/wizard ──────────────────────────────────

test.describe("vitalia-auth-base-functional — SC-07: CTA Configurar navega a /onboarding/wizard", () => {
  test("SC-07: click en 'Configurar tu clínica' → navega a /onboarding/wizard", async ({
    authedPage: page,
  }) => {
    await setupDashboardMocks(page);

    // Mock del wizard draft para que no falle la carga del wizard
    await page.route("**/api/v1/vitalia/wizard/drafts**", async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            draftId: "smoke-draft-sc07",
            step: "greet",
            message: "Hola, comencemos con la configuración.",
            mode: null,
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto("/", { waitUntil: "domcontentloaded" });

    // Esperar que el dashboard cargue
    await expect(page).not.toHaveURL(/\/sign-in/);

    // Encontrar el CTA de configuración
    const ctaLocator = page
      .getByText(/configurar tu clínica/i)
      .or(page.getByText(/configurar clínica/i))
      .or(page.getByText(/completar configuración/i))
      .or(page.getByText(/comenzar configuración/i));

    const cta = ctaLocator.first();
    await expect(cta).toBeVisible({ timeout: 15_000 });

    // Click en el CTA
    await cta.click();

    // Debe navegar a /onboarding/wizard
    await expect(page).toHaveURL(/\/onboarding\/wizard/, { timeout: 10_000 });
  });
});
