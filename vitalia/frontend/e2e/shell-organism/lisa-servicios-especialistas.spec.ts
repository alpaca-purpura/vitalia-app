// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * lisa-servicios-especialistas.spec.ts — E2E smoke: vincular especialista.
 *
 * Covers:
 *   SC-especialistas-empty  RN-9: servicio sin especialistas → aviso con link a /lisa/doctores
 *   SC-especialistas-link   Abrir picker → checklist de doctores disponibles
 *   SC-especialistas-rn9-link  Link "Lisa → Especialistas" apunta a /{tenantId}/lisa/doctores
 *
 * Stack requerido: BE :8002 + FE :3002 UP (make dev-vitalia)
 * Requires E2E_OFFER_ID pointing to a servicio sin especialistas vinculados
 *
 * spec_anchor: 01-spec.md §Especialistas · RN-9 · RN-20 · 04-validators.yaml V-FN-especialistas
 *
 * ★ STACK-STATUS: PENDING-LIVE-VERIFICATION
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     E2E_OFFER_ID=<offerId> npx playwright test lisa-servicios-especialistas --project=shell
 */

import { expect } from "@playwright/test";
import {
  test,
  TENANT_ID,
} from "../fixtures/real-backend-forward.fixture";
import { ServicioWorkspacePage } from "../pages/ServicioWorkspacePage";

const OFFER_ID = process.env["E2E_OFFER_ID"];

// ---------------------------------------------------------------------------
// SC-especialistas-empty: RN-9 empty state
// ---------------------------------------------------------------------------

test.describe("SC-especialistas-empty — RN-9: empty state with link to doctores", () => {
  test.skip(!OFFER_ID, "Requires E2E_OFFER_ID (servicio without linked specialists)");

  test("shows empty state warning + link to lisa/doctores when no specialists linked", async ({
    page,
  }) => {
    const workspace = new ServicioWorkspacePage(page);
    await workspace.goto(TENANT_ID, OFFER_ID!, "especialistas");

    // Empty state messaging (RN-9)
    const emptyText = page.getByText("No hay especialistas vinculados todavía.");
    await expect(emptyText).toBeVisible({ timeout: 10_000 });

    // Link to doctores directory
    const doctoresLink = page.getByRole("link", {
      name: /Agrega especialistas en Lisa → Especialistas/i,
    });
    await expect(doctoresLink).toBeVisible();
    await expect(doctoresLink).toHaveAttribute(
      "href",
      `/${TENANT_ID}/lisa/doctores`
    );
  });
});

// ---------------------------------------------------------------------------
// SC-especialistas-link: open picker
// ---------------------------------------------------------------------------

test.describe("SC-especialistas-link — Vincular especialista opens picker", () => {
  test.skip(!OFFER_ID, "Requires E2E_OFFER_ID");

  test("clicking 'Vincular especialista' opens doctor picker with search", async ({ page }) => {
    const workspace = new ServicioWorkspacePage(page);
    await workspace.goto(TENANT_ID, OFFER_ID!, "especialistas");

    await workspace.openEspecialistaPicker();

    // Picker should show a search input
    const searchInput = page.getByPlaceholder("Buscar por nombre o especialidad…");
    await expect(searchInput).toBeVisible({ timeout: 5_000 });
  });

  test("closing picker with X hides it (RN-picker-close)", async ({ page }) => {
    const workspace = new ServicioWorkspacePage(page);
    await workspace.goto(TENANT_ID, OFFER_ID!, "especialistas");

    await workspace.openEspecialistaPicker();

    // Close the picker
    await workspace.closeEspecialistaPicker();

    // Picker search input should be hidden
    const searchInput = page.getByPlaceholder("Buscar por nombre o especialidad…");
    await expect(searchInput).not.toBeVisible({ timeout: 3_000 });
  });
});

// ---------------------------------------------------------------------------
// SC-rn9-link: navigate to doctores from RN-9 link
// ---------------------------------------------------------------------------

test.describe("SC-rn9-link — RN-9 link navigates to doctores directory", () => {
  test.skip(!OFFER_ID, "Requires E2E_OFFER_ID (servicio without linked specialists)");

  test("clicking 'Lisa → Especialistas' link navigates to doctores", async ({ page }) => {
    const workspace = new ServicioWorkspacePage(page);
    await workspace.goto(TENANT_ID, OFFER_ID!, "especialistas");

    const doctoresLink = page.getByRole("link", {
      name: /Agrega especialistas en Lisa → Especialistas/i,
    });

    await expect(doctoresLink).toBeVisible({ timeout: 10_000 });

    // Click and verify navigation to doctores
    await doctoresLink.click();
    await page.waitForURL(`**/${TENANT_ID}/lisa/doctores`, { timeout: 10_000 });
    expect(page.url()).toContain(`/${TENANT_ID}/lisa/doctores`);
  });
});
