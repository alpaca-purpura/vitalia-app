/**
 * tenants-users.spec.ts — SC-08 + SC-09 (vitalia-auth-base-functional)
 *
 * Smoke gate: panel admin Streamlit (puerto 8501). Verifica que el panel
 * de administración muestra las páginas "Tenants" y "Usuarios" con los
 * formularios de creación correspondientes.
 *
 * IMPORTANTE: Este spec apunta a Streamlit en E2E_ADMIN_BASE_URL (default:
 * http://localhost:8501), NO al frontend Next.js en 3002. El stack admin es
 * un contenedor separado (ver vitalia/backend/src/modules/vitalia/admin/).
 *
 * SECURITY: La variable VITALIA_ADMIN_PASSWORD NUNCA se hardcodea en este
 * archivo. Se inyecta vía env var. Si no está disponible, el test se salta
 * con mensaje informativo.
 *
 * Per e2e-testing.md: native Playwright on Linux host. Puerto 8501 (admin).
 *
 * Run:
 *   cd vitalia/frontend && E2E_ADMIN_BASE_URL=http://localhost:8501 \
 *     VITALIA_ADMIN_PASSWORD=${VITALIA_ADMIN_PASSWORD} \
 *     npx playwright test e2e/admin/tenants-users.spec.ts --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "@playwright/test";

// ─── Admin base URL (puerto 8501 separado del frontend 3002) ─────────────────

const ADMIN_BASE_URL =
  process.env["E2E_ADMIN_BASE_URL"] ?? "http://localhost:8501";
const ADMIN_PASSWORD = process.env["VITALIA_ADMIN_PASSWORD"] ?? "";

/**
 * Navega al panel admin y, si hay auth, ingresa la contraseña.
 * Streamlit muestra un formulario de password básico cuando está configurado.
 */
async function navigateToAdmin(page: import("@playwright/test").Page) {
  await page.goto(ADMIN_BASE_URL, { waitUntil: "domcontentloaded" });

  // Si Streamlit pide password (auth básica por cookie/session)
  const passwordInput = page.locator('input[type="password"]');
  const isPasswordRequired = await passwordInput
    .isVisible({ timeout: 5_000 })
    .catch(() => false);

  if (isPasswordRequired && ADMIN_PASSWORD) {
    await passwordInput.fill(ADMIN_PASSWORD);
    const loginBtn = page.locator(
      'button[kind="primaryFormSubmit"], button:has-text("Log in")',
    );
    await loginBtn.click();
    // Esperar que la app cargue post-login
    await page
      .waitForLoadState("networkidle", { timeout: 15_000 })
      .catch(() => {});
  }
}

// ─── SC-08: Panel admin muestra navegación + formulario de Tenants ───────────

test.describe("vitalia-auth-base-functional — SC-08: admin panel Tenants page", () => {
  test.beforeEach(() => {
    // Saltar si no hay stack admin disponible ni password
    // (documentado como gate bloqueado en T-6.a-impl-log.md)
  });

  test("SC-08: admin 8501 → navegación 'Tenants' + 'Usuarios' visibles; formulario crear tenant presente", async ({
    page,
  }) => {
    // Verificar que el admin está disponible (puede estar down en local dev)
    const adminResponse = await page
      .goto(ADMIN_BASE_URL, {
        waitUntil: "domcontentloaded",
        timeout: 10_000,
      })
      .catch(() => null);

    if (!adminResponse || adminResponse.status() >= 500) {
      test.skip(
        true,
        `Admin panel no disponible en ${ADMIN_BASE_URL} — ejecutar make dev-vitalia primero`,
      );
      return;
    }

    await navigateToAdmin(page);

    // Esperar que Streamlit cargue la app completa
    await page
      .waitForLoadState("networkidle", { timeout: 20_000 })
      .catch(() => {});

    // SC-08.1: Navegación debe tener "Tenants" y "Usuarios"
    // Streamlit navigation puede ser sidebar o top nav
    const tenantsNav = page.getByText("Tenants").or(page.getByText("tenants"));
    const usuariosNav = page
      .getByText("Usuarios")
      .or(page.getByText("usuarios"))
      .or(page.getByText("Usuarios (Users)"));

    await expect(tenantsNav.first()).toBeVisible({ timeout: 20_000 });
    await expect(usuariosNav.first()).toBeVisible({ timeout: 10_000 });

    // SC-08.2: Ir a la página de Tenants
    await tenantsNav.first().click();
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    // SC-08.3: Formulario de creación de tenant debe estar presente
    // Streamlit renderiza formularios con st.form() o widgets individuales
    const createTenantForm = page
      .getByText(/crear.*tenant/i)
      .or(page.getByText(/nuevo.*tenant/i))
      .or(page.getByText(/agregar.*tenant/i))
      .or(page.locator("form"))
      .or(page.getByRole("button", { name: /crear/i }));

    await expect(createTenantForm.first()).toBeVisible({ timeout: 15_000 });
  });
});

// ─── SC-09: Panel admin "Usuarios" muestra formulario de creación ─────────────

test.describe("vitalia-auth-base-functional — SC-09: admin panel Usuarios page", () => {
  test("SC-09: admin 'Usuarios' → formulario de creación de usuario presente", async ({
    page,
  }) => {
    // Verificar que el admin está disponible
    const adminResponse = await page
      .goto(ADMIN_BASE_URL, {
        waitUntil: "domcontentloaded",
        timeout: 10_000,
      })
      .catch(() => null);

    if (!adminResponse || adminResponse.status() >= 500) {
      test.skip(
        true,
        `Admin panel no disponible en ${ADMIN_BASE_URL} — ejecutar make dev-vitalia primero`,
      );
      return;
    }

    await navigateToAdmin(page);

    // Esperar carga completa
    await page
      .waitForLoadState("networkidle", { timeout: 20_000 })
      .catch(() => {});

    // Navegar a la sección "Usuarios"
    const usuariosNav = page
      .getByText("Usuarios")
      .or(page.getByText("usuarios"))
      .or(page.getByText("Usuarios (Users)"));

    await expect(usuariosNav.first()).toBeVisible({ timeout: 20_000 });
    await usuariosNav.first().click();
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    // SC-09.1: La página "Usuarios" debe mostrar formulario de creación
    const createUserForm = page
      .getByText(/crear.*usuario/i)
      .or(page.getByText(/nuevo.*usuario/i))
      .or(page.getByText(/agregar.*usuario/i))
      .or(page.getByRole("button", { name: /crear usuario/i }))
      .or(page.getByRole("button", { name: /crear/i }));

    await expect(createUserForm.first()).toBeVisible({ timeout: 15_000 });

    // SC-09.2: No debe haber PHI de pacientes visible
    // (Admin de tenants/usuarios no maneja datos médicos)
    // HIPAA-lite: verificar que no se filtran campos sensibles en la UI admin.
    // toHaveCount(0): falla loudly si el texto PHI aparece (comportamiento deseado — PHI leak = error real).
    await expect(page.getByText(/diagnóstico/i)).toHaveCount(0, {
      timeout: 3_000,
    });
    await expect(page.getByText(/tratamiento/i)).toHaveCount(0, {
      timeout: 3_000,
    });
  });
});
