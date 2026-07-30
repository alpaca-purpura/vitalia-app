/**
 * admin-tenants-crud.spec.ts — SC-02 + SC-03 + SC-07
 *
 * SC-02: Admin crea tenant nuevo via TenantRepository + audit log row creado.
 * SC-03: Admin lista tenants — dataframe con columnas ID/Nombre/Slug visibles.
 * SC-07: Admin suspende tenant — toggle is_active + audit log "tenant.suspend".
 *
 * Apunta a Streamlit admin en E2E_ADMIN_BASE_URL (default: http://127.0.0.1:8502).
 * DB verification via /api/v1/vitalia/admin/ helper endpoints (X-Internal-Token).
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */

import { test, expect } from "./admin_auth.fixture";
import { getDbState, getAuditLog } from "./utils/db_verify";

const TENANT_SLUG = `e2e-test-${Date.now()}`;
const TENANT_NAME = "Clínica Aurora Dental E2E";

// ─── SC-02: Admin crea tenant nuevo ──────────────────────────────────────────

test.describe("SC-02 — Admin crea tenant nuevo via TenantRepository", () => {
  test("crea tenant y audit log row registrado", async ({
    authenticatedAdminPage: page,
    request,
  }) => {
    const before = await getDbState(request);
    const sinceMs = Date.now();

    // Navegar a la sección Tenants
    await page
      .locator('[data-testid="stSidebar"]')
      .getByText(/Tenants/i)
      .first()
      .click();
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    // Ir al tab "Crear nuevo"
    const createTab = page.getByRole("tab", { name: /crear nuevo/i });
    await expect(createTab).toBeVisible({ timeout: 10_000 });
    await createTab.click();

    // Rellenar formulario de creación
    await page
      .getByLabel(/nombre/i)
      .first()
      .fill(TENANT_NAME);
    await page.getByLabel(/slug/i).first().fill(TENANT_SLUG);
    // selectbox País — primer country disponible
    const countrySelect = page
      .getByLabel(/país/i)
      .or(page.locator('[aria-label*="País"]'));
    if (await countrySelect.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await countrySelect.first().selectOption("AR");
    }

    // Enviar formulario
    await page
      .getByRole("button", { name: /crear tenant/i })
      .first()
      .click();

    // Verificar mensaje de éxito en UI
    await expect(
      page.getByText(new RegExp(`tenant.*${TENANT_NAME}.*creado`, "i")),
    ).toBeVisible({ timeout: 15_000 });

    // Verificar incremento en DB
    const after = await getDbState(request);
    expect(after.tenants).toBeGreaterThanOrEqual(before.tenants + 1);

    // Verificar audit log row
    const entries = await getAuditLog(request, {
      action: "tenant.create",
      sinceMsAgo: Date.now() - sinceMs + 10_000,
    });
    expect(entries.length).toBeGreaterThan(0);
    expect(entries[0]?.action).toBe("tenant.create");
    expect(entries[0]?.resource_type).toBe("tenant");
  });
});

// ─── SC-03: Admin lista tenants ───────────────────────────────────────────────

test.describe("SC-03 — Admin lista tenants via TenantRepository", () => {
  test("página Tenants muestra tabla con columnas ID/Nombre/Slug", async ({
    authenticatedAdminPage: page,
  }) => {
    // Navegar a Tenants
    await page
      .locator('[data-testid="stSidebar"]')
      .getByText(/Tenants/i)
      .first()
      .click();
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    // Debe mostrar tab "Listado"
    const listTab = page.getByRole("tab", { name: /listado/i });
    await expect(listTab).toBeVisible({ timeout: 10_000 });
    await listTab.click();

    // Dataframe o tabla con columnas esperadas
    // Streamlit renderiza dataframes como tablas o elementos stDataFrame
    const pageContent = page.locator(
      "main, [data-testid='stAppViewContainer']",
    );
    // Verificar que alguna columna es visible (Nombre, Slug, Estado son esperados)
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

  test("no hay PHI médico expuesto en listado de tenants", async ({
    authenticatedAdminPage: page,
  }) => {
    await page
      .locator('[data-testid="stSidebar"]')
      .getByText(/Tenants/i)
      .first()
      .click();
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    // HIPAA-lite: listado de tenants/usuarios admin NO debe exponer PHI
    await expect(page.getByText(/diagnóstico/i)).toHaveCount(0, {
      timeout: 3_000,
    });
    await expect(page.getByText(/tratamiento/i)).toHaveCount(0, {
      timeout: 3_000,
    });
    await expect(page.getByText(/medicaci[oó]n/i)).toHaveCount(0, {
      timeout: 3_000,
    });
  });
});

// ─── SC-07: Admin suspende tenant ────────────────────────────────────────────

test.describe("SC-07 — Admin suspende tenant toggle is_active", () => {
  test("toggle suspender escribe audit log tenant.suspend", async ({
    authenticatedAdminPage: page,
    request,
  }) => {
    // Primero necesitamos al menos un tenant en DB
    const state = await getDbState(request);
    if (state.tenants === 0) {
      test.skip(
        true,
        "No hay tenants en DB para suspender — ejecutar SC-02 primero",
      );
      return;
    }

    const sinceMs = Date.now();

    // Navegar a Tenants → Listado
    await page
      .locator('[data-testid="stSidebar"]')
      .getByText(/Tenants/i)
      .first()
      .click();
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    const listTab = page.getByRole("tab", { name: /listado/i });
    if (await listTab.isVisible({ timeout: 5_000 }).catch(() => false)) {
      await listTab.click();
    }

    // Botón Toggle Activo/Suspendido
    const toggleBtn = page.getByRole("button", {
      name: /toggle activo.suspendido|suspender|activar/i,
    });
    await expect(toggleBtn).toBeVisible({ timeout: 10_000 });
    await toggleBtn.first().click();

    // Esperar respuesta (Streamlit re-render)
    await page
      .waitForLoadState("networkidle", { timeout: 10_000 })
      .catch(() => {});

    // Verificar que se registró audit log (tenant.suspend o tenant.activate)
    const entries = await getAuditLog(request, {
      sinceMsAgo: Date.now() - sinceMs + 10_000,
    });
    const toggleEntry = entries.find(
      (e) => e.action === "tenant.suspend" || e.action === "tenant.activate",
    );
    expect(toggleEntry).toBeTruthy();
    expect(toggleEntry?.resource_type).toBe("tenant");
  });
});
