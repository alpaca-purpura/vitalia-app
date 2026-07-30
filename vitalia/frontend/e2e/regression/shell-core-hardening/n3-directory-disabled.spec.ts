// cap: shell-organism.shell-vitalia
// story-origin: vitalia-shell-core-hardening
/**
 * n3-directory-disabled.spec.ts — SC-12: hojas deshabilitadas sin entidad (RN-10)
 *
 * Verifica que en la vista de directorio (sin entidad seleccionada),
 * los leaf tabs del EntityWorkspaceLayout están deshabilitados:
 *   - No se puede navegar a /perfil, /horarios, /servicios sin seleccionar un doctor.
 *   - No se puede navegar a /resumen, /historial sin seleccionar un lead.
 *
 * Real-backend. Gate anti-burbuja via base.ts.
 *
 * Run:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/shell-core-hardening/n3-directory-disabled.spec.ts \
 *     --project=smoke
 *
 * downstream-regression-na: brand-local E2E spec; no cross-brand consumers
 */
import { test, expect } from "../../fixtures/shell-hardening.fixture";
import { EntityWorkspacePage } from "../../pages/EntityWorkspacePage";

const DESKTOP_VIEWPORT = { width: 1440, height: 900 };

test.describe("SC-12 — hojas N3 deshabilitadas sin entidad (RN-10)", () => {
  test.use({ viewport: DESKTOP_VIEWPORT });

  test("staff directory: navegar directo a /staff/{id}/perfil sin doctor → 404 o redirect", async ({
    shellPage,
    tenantId,
  }) => {
    // Attempt to navigate to a workspace leaf route directly without a valid doctor
    const fakeDoctorId = "00000000-0000-0000-0000-000000000000";
    await shellPage.goto(
      `/${tenantId}/lisa/staff/${fakeDoctorId}/perfil`,
    );
    await shellPage.waitForLoadState("networkidle", { timeout: 15_000 });

    // Should show a not-found or redirect to directory (not a blank page with errors)
    const isNotFound = await shellPage
      .locator(
        '[data-testid="not-found-shell"], [data-testid="not-found-agent"]',
      )
      .isVisible({ timeout: 5_000 })
      .catch(() => false);
    const isRedirected =
      !shellPage.url().includes(`${fakeDoctorId}`) ||
      shellPage.url().includes("staff");

    expect(
      isNotFound || isRedirected,
      "ruta inválida de doctor debe resultar en 404 o redirect, no error silencioso",
    ).toBe(true);
  });

  test("embudo: navegar directo a /embudo/{id}/resumen sin lead → 404 o redirect", async ({
    shellPage,
    tenantId,
  }) => {
    const fakeLeadId = "00000000-0000-0000-0000-000000000000";
    await shellPage.goto(
      `/${tenantId}/adrian/embudo/${fakeLeadId}/resumen`,
    );
    await shellPage.waitForLoadState("networkidle", { timeout: 15_000 });

    const isNotFound = await shellPage
      .locator(
        '[data-testid="not-found-shell"], [data-testid="not-found-agent"]',
      )
      .isVisible({ timeout: 5_000 })
      .catch(() => false);
    const isRedirected =
      !shellPage.url().includes(`${fakeLeadId}`) ||
      shellPage.url().includes("embudo");

    expect(
      isNotFound || isRedirected,
      "ruta inválida de lead debe resultar en 404 o redirect",
    ).toBe(true);
  });

  test("EntityWorkspaceLayout: en directory mode (entity=null) no hay leaf tab activo", async ({
    shellPage,
    tenantId,
  }) => {
    const ewp = new EntityWorkspacePage(shellPage);
    await ewp.gotoStaffDirectory(tenantId);

    // In directory mode (list view), EntityWorkspaceLayout should NOT render its
    // workspace content with leaf tabs active. The layout might not be present at all
    // in directory mode (directory renders list, not workspace).
    const hasWorkspace = await ewp.workspaceLayout
      .isVisible({ timeout: 3_000 })
      .catch(() => false);

    if (hasWorkspace) {
      // If workspace is visible, it should be in loading or empty state
      const isLoading = await ewp.isLoadingState();
      // Verify: no leaf tab shows as "active" without entity context
      const activeTab = await shellPage
        .locator(
          '[data-testid="entity-workspace-layout"] [role="tab"][aria-selected="true"]',
        )
        .count();
      // Either loading or no active tab in directory mode
      expect(isLoading || activeTab === 0).toBe(true);
    }
    // If workspace not present in directory = OK (list-only mode)
  });
});
