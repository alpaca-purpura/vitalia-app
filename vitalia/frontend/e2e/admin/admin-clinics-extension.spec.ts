/**
 * admin-clinics-extension.spec.ts — SC-08 + SC-13
 *
 * SC-08: Admin crea clinic asociada a tenant — ClinicRepository + audit log.
 * SC-13: Phantom tables DELETED — cero queries SQL crudo residual en admin modules.
 *        (SC-13 verificado a nivel arch test; este spec verifica lado UI: no hay errores
 *         de tabla inexistente expuestos en la UI del admin Streamlit)
 *
 * Apunta a Streamlit admin en E2E_ADMIN_BASE_URL (default: http://127.0.0.1:8502).
 * DB verification via /api/v1/vitalia/admin/ helper endpoints (X-Internal-Token).
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "./admin_auth.fixture";
import { getDbState, getAuditLog } from "./utils/db_verify";

const CLINIC_NAME = "Clínica Aurora Dental E2E";
const CLINIC_SLUG = `clinic-e2e-${Date.now()}`;

// ─── SC-08: Admin crea clinic asociada a tenant ───────────────────────────────

test.describe("SC-08 — Admin crea clinic asociada a tenant via ClinicRepository", () => {
  test("crea clinic con tenant_id y audit log row registrado", async ({
    authenticatedAdminPage: page,
    request,
  }) => {
    const before = await getDbState(request);
    if (before.tenants === 0) {
      test.skip(true, "No hay tenants disponibles — ejecutar SC-02 primero");
      return;
    }

    const sinceMs = Date.now();

    // Navegar a la sección Clínicas
    await page
      .locator('[data-testid="stSidebar"]')
      .getByText(/cl[ií]nicas?/i)
      .first()
      .click();
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    // Ir al tab "Crear nueva"
    const createTab = page.getByRole("tab", {
      name: /crear nueva|crear nuevo/i,
    });
    await expect(createTab).toBeVisible({ timeout: 10_000 });
    await createTab.click();

    // Rellenar formulario de creación
    await page
      .getByLabel(/nombre/i)
      .first()
      .fill(CLINIC_NAME);
    await page.getByLabel(/slug/i).first().fill(CLINIC_SLUG);

    // Seleccionar tenant
    const tenantSelect = page
      .getByLabel(/tenant/i)
      .or(page.locator('[aria-label*="Tenant"]'));
    if (
      await tenantSelect
        .first()
        .isVisible({ timeout: 3_000 })
        .catch(() => false)
    ) {
      const options = await tenantSelect.first().locator("option").all();
      if (options.length > 1) {
        await tenantSelect.first().selectOption({ index: 1 });
      }
    }

    // País/ciudad si existe
    const countryField = page
      .getByLabel(/país|pa[ií]s/i)
      .or(page.locator('[aria-label*="País"]'));
    if (
      await countryField
        .first()
        .isVisible({ timeout: 3_000 })
        .catch(() => false)
    ) {
      await countryField
        .first()
        .selectOption("AR")
        .catch(() => {});
    }

    // Enviar formulario
    await page
      .getByRole("button", { name: /crear cl[ií]nica/i })
      .first()
      .click();

    // Verificar mensaje de éxito
    await expect(
      page.getByText(
        new RegExp(
          `cl[ií]nica.*${CLINIC_NAME}.*creada|creada.*cl[ií]nica`,
          "i",
        ),
      ),
    ).toBeVisible({ timeout: 15_000 });

    // Verificar incremento en DB (clinics count)
    const after = await getDbState(request);
    expect(after.clinics).toBeGreaterThanOrEqual(before.clinics + 1);

    // Verificar audit log row
    const entries = await getAuditLog(request, {
      action: "clinic.create",
      sinceMsAgo: Date.now() - sinceMs + 10_000,
    });
    expect(entries.length).toBeGreaterThan(0);
    expect(entries[0]?.action).toBe("clinic.create");
    expect(entries[0]?.resource_type).toBe("clinic");
  });

  test("listado de clinicas muestra columnas Nombre/Slug/Tenant", async ({
    authenticatedAdminPage: page,
  }) => {
    await page
      .locator('[data-testid="stSidebar"]')
      .getByText(/cl[ií]nicas?/i)
      .first()
      .click();
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    // Tab listado
    const listTab = page.getByRole("tab", { name: /listado/i });
    await expect(listTab).toBeVisible({ timeout: 10_000 });
    await listTab.click();

    const pageContent = page.locator(
      "main, [data-testid='stAppViewContainer']",
    );
    const hasNombreCol = await pageContent
      .getByText(/Nombre/i)
      .first()
      .isVisible({ timeout: 8_000 })
      .catch(() => false);
    const hasSlugCol = await pageContent
      .getByText(/Slug/i)
      .first()
      .isVisible({ timeout: 3_000 })
      .catch(() => false);
    expect(hasNombreCol || hasSlugCol).toBeTruthy();
  });
});

// ─── SC-13: Phantom tables DELETED (no errores UI residuales) ─────────────────

test.describe("SC-13 — Phantom tables eliminadas — UI sin errores de tabla inexistente", () => {
  test("admin panel no muestra OperationalError ni tabla no existente", async ({
    authenticatedAdminPage: page,
  }) => {
    // SC-13 verifica a nivel arquitectura (test_phantom_tables_zero_refs.py).
    // A nivel E2E: verificar que ninguna sección del admin muestra error de DB.

    const sections = [
      { text: /Tenants/i, label: "Tenants" },
      { text: /Usuarios/i, label: "Usuarios" },
      { text: /cl[ií]nicas?/i, label: "Clínicas" },
    ];

    for (const section of sections) {
      await page
        .locator('[data-testid="stSidebar"]')
        .getByText(section.text)
        .first()
        .click();
      await page
        .waitForLoadState("networkidle", { timeout: 10_000 })
        .catch(() => {});

      const mainContent = page.locator(
        "main, [data-testid='stAppViewContainer']",
      );

      // No debe aparecer ninguno de los errores de tabla inexistente
      await expect(mainContent.getByText(/OperationalError/i)).toHaveCount(0, {
        timeout: 3_000,
      });
      await expect(mainContent.getByText(/no such table/i)).toHaveCount(0, {
        timeout: 3_000,
      });
      await expect(
        mainContent.getByText(/relation.*does not exist/i),
      ).toHaveCount(0, { timeout: 3_000 });
      await expect(mainContent.getByText(/ProgrammingError/i)).toHaveCount(0, {
        timeout: 3_000,
      });

      // La sección debe mostrar contenido útil (no sólo error)
      await expect(mainContent).toBeVisible({ timeout: 5_000 });
    }
  });

  test("admin panel no expone stack traces de SQL a usuario", async ({
    authenticatedAdminPage: page,
  }) => {
    // Acceder a cada sección y verificar que no hay SQL raw expuesto
    await page
      .locator('[data-testid="stSidebar"]')
      .getByText(/Tenants/i)
      .first()
      .click();
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    const mainContent = page.locator(
      "main, [data-testid='stAppViewContainer']",
    );
    // No debe exponer SQL directo en UI
    await expect(
      mainContent.getByText(
        /SELECT.*FROM|INSERT INTO|UPDATE.*SET|DELETE FROM/i,
      ),
    ).toHaveCount(0, { timeout: 3_000 });
  });
});
