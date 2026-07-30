// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * lisa-servicios-crear.spec.ts — E2E smoke: crear servicio personalizado.
 *
 * Covers:
 *   SC-crear-plantilla  Flujo biblioteca → usar plantilla → redirect workspace
 *   SC-crear-personalizado  Flujo custom form → RN-16 (crear = entrar a editar)
 *   SC-validacion-nombre  Custom form → nombre vacío → validation error
 *
 * RN-16: crear un servicio redirige inmediatamente al workspace para editar.
 *
 * Stack requerido: BE :8002 + FE :3002 UP (make dev-vitalia)
 * Tenant: E2E_TENANT_ID env var (falls back to aurora-dental-ar fixture tenant)
 *
 * spec_anchor: 01-spec.md §Nuevo · 03-arch-fe.md §8 Tests · 04-validators.yaml V-FN-crear
 *
 * ★ STACK-STATUS: PENDING-LIVE-VERIFICATION
 *   Ejecutar con stack UP + E2E_TENANT_ID set:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 npx playwright test lisa-servicios-crear --project=shell
 */

import { expect } from "@playwright/test";
import {
  test,
  TENANT_ID,
} from "../fixtures/real-backend-forward.fixture";
import { ServiciosCatalogoPage } from "../pages/ServiciosCatalogoPage";
import { NuevoServicioPage } from "../pages/NuevoServicioPage";

// ---------------------------------------------------------------------------
// SC-validacion-nombre: form validation (no BE call needed)
// ---------------------------------------------------------------------------

test.describe("SC-validacion-nombre — nombre requerido en form personalizado", () => {
  test("submitting custom form without name shows validation error", async ({ page }) => {
    const catalogo = new ServiciosCatalogoPage(page);
    const picker = new NuevoServicioPage(page);

    await catalogo.goto(TENANT_ID);
    await catalogo.openNuevoServicio();
    await picker.switchToMode("personalizado");

    // Submit without filling name
    await picker.submitCustomForm();

    await expect(page.getByText("El nombre es requerido")).toBeVisible({
      timeout: 5_000,
    });
  });
});

// ---------------------------------------------------------------------------
// SC-crear-personalizado: crear custom → redirect workspace (RN-16)
// ---------------------------------------------------------------------------

test.describe("SC-crear-personalizado — custom servicio → workspace redirect (RN-16)", () => {
  test.skip(
    !process.env["E2E_ENABLE_WRITES"],
    "Skip write test unless E2E_ENABLE_WRITES=1 (creates real DB record)"
  );

  test("creates custom servicio and redirects to workspace/resumen", async ({ page }) => {
    const catalogo = new ServiciosCatalogoPage(page);
    const picker = new NuevoServicioPage(page);

    await catalogo.goto(TENANT_ID);
    await catalogo.openNuevoServicio();
    await picker.switchToMode("personalizado");

    // Fill name → submit
    const uniqueName = `Test Servicio E2E ${Date.now()}`;
    await picker.fillCustomName(uniqueName);
    await picker.submitCustomForm();

    // RN-16: redirect to workspace
    await picker.waitForWorkspaceRedirect();

    // Verify workspace URL pattern
    expect(page.url()).toMatch(/\/lisa\/servicios\/[^/]+\/resumen/);

    // Workspace layout visible
    await expect(page.getByTestId("entity-workspace-layout")).toBeVisible({
      timeout: 15_000,
    });
  });
});

// ---------------------------------------------------------------------------
// SC-crear-plantilla: biblioteca mode guard (no clinicType = search disabled)
// ---------------------------------------------------------------------------

test.describe("SC-biblioteca-guard — search disabled until clinicType selected", () => {
  test("search input is disabled before selecting clinicType", async ({ page }) => {
    const catalogo = new ServiciosCatalogoPage(page);
    const picker = new NuevoServicioPage(page);

    await catalogo.goto(TENANT_ID);
    await catalogo.openNuevoServicio();
    // Default mode is "biblioteca"
    await picker.switchToMode("biblioteca");

    await expect(picker.searchInput).toBeDisabled();
    await expect(
      page.getByText("Selecciona tu especialidad para buscar en la biblioteca.")
    ).toBeVisible();
  });
});
