// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * lisa-servicios-autosave.spec.ts — E2E smoke: todo autoguarda sin botón.
 *
 * Covers:
 *   SC-autosave  Editar campo precio → FloatingAutosaveIndicator → "guardado"
 *   SC-autosave-no-boton  No "Guardar" button visible in workspace leaves
 *   SC-autosave-indicator-count  Exactly ONE FloatingAutosaveIndicator per leaf
 *
 * RN-autosave (canon §2.6): debounce 600ms, ONE indicator per page, NO "Guardar" button.
 *
 * Stack requerido: BE :8002 + FE :3002 UP (make dev-vitalia)
 * Requires a servicio in the DB: E2E_OFFER_ID env var
 *
 * spec_anchor: 01-spec.md §Autosave · 03-arch-fe.md §8 Tests · 04-validators.yaml V-FN-autosave
 *
 * ★ STACK-STATUS: PENDING-LIVE-VERIFICATION
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     E2E_OFFER_ID=<offerId> npx playwright test lisa-servicios-autosave --project=shell
 */

import { expect } from "@playwright/test";
import {
  test,
  TENANT_ID,
} from "../fixtures/real-backend-forward.fixture";
import { ServicioWorkspacePage } from "../pages/ServicioWorkspacePage";

// Resolve offer ID from env — tests skip gracefully if not set
const OFFER_ID = process.env["E2E_OFFER_ID"];

// ---------------------------------------------------------------------------
// SC-autosave-no-boton: no "Guardar" button in any leaf
// ---------------------------------------------------------------------------

test.describe("SC-autosave-no-boton — leaves have no explicit Guardar button", () => {
  test.skip(!OFFER_ID, "Requires E2E_OFFER_ID");

  test("Resumen leaf has no Guardar button (autosave canon)", async ({ page }) => {
    const workspace = new ServicioWorkspacePage(page);
    await workspace.goto(TENANT_ID, OFFER_ID!, "resumen");

    // No "Guardar" button (save-on-change canon)
    const guardarBtn = page.getByRole("button", { name: /^Guardar$/i });
    await expect(guardarBtn).not.toBeVisible();
  });

  test("Para Adrián leaf has no Guardar button (autosave canon)", async ({ page }) => {
    const workspace = new ServicioWorkspacePage(page);
    await workspace.goto(TENANT_ID, OFFER_ID!, "para-adrian");

    const guardarBtn = page.getByRole("button", { name: /^Guardar$/i });
    await expect(guardarBtn).not.toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// SC-autosave-indicator-count: exactly one FloatingAutosaveIndicator per leaf
// ---------------------------------------------------------------------------

test.describe("SC-autosave-indicator-count — exactly one indicator per leaf", () => {
  test.skip(!OFFER_ID, "Requires E2E_OFFER_ID");

  const leaves = ["resumen", "para-adrian", "plan-pago", "prueba-social"] as const;

  for (const leaf of leaves) {
    test(`${leaf} leaf renders exactly one FloatingAutosaveIndicator`, async ({ page }) => {
      const workspace = new ServicioWorkspacePage(page);
      await workspace.goto(TENANT_ID, OFFER_ID!, leaf);

      const indicators = page.getByTestId("floating-autosave-indicator");
      await expect(indicators).toHaveCount(1, { timeout: 10_000 });
    });
  }
});

// ---------------------------------------------------------------------------
// SC-autosave: edit price → indicator shows "guardado"
// (write test — skip unless E2E_ENABLE_WRITES=1)
// ---------------------------------------------------------------------------

test.describe("SC-autosave — edit triggers autosave cycle", () => {
  test.skip(!OFFER_ID || !process.env["E2E_ENABLE_WRITES"], "Requires E2E_OFFER_ID + E2E_ENABLE_WRITES=1");

  test("editing price field triggers autosave: indicator reaches 'saved' state", async ({ page }) => {
    const workspace = new ServicioWorkspacePage(page);
    await workspace.goto(TENANT_ID, OFFER_ID!, "plan-pago");

    // Fill price field
    const priceInput = page.getByLabel(/Precio del tratamiento/i);
    await priceInput.fill("1500");

    // Wait for autosave debounce (600ms) + network
    await page.waitForFunction(
      () => {
        const el = document.querySelector('[data-testid="floating-autosave-indicator"]');
        const status = el?.getAttribute("data-status");
        return status === "saved" || status === "saving";
      },
      { timeout: 4_000 }
    );

    // Final state should be "saved"
    await page.waitForFunction(
      () => {
        const el = document.querySelector('[data-testid="floating-autosave-indicator"]');
        return el?.getAttribute("data-status") === "saved";
      },
      { timeout: 5_000 }
    );

    // No console errors during save
    // (anti-burbuja gate from base.ts handles this — already composed via mergeTests)
  });
});
