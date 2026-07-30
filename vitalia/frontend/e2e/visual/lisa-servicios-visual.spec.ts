// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-8
/**
 * lisa-servicios-visual.spec.ts — Visual goldens for lisa-servicios.
 *
 * 8 snapshots (4 views × 2 themes = 8 PNGs):
 *   catalogo-light.png / catalogo-dark.png
 *   escalera-light.png / escalera-dark.png
 *   servicio-workspace-light.png / servicio-workspace-dark.png
 *   nuevo-servicio-light.png / nuevo-servicio-dark.png
 *
 * Threshold: maxDiffPixelRatio: 0.001 (ADR-vitalia-003)
 * Animations disabled (playwright.config.ts project=visual)
 * Tenant: E2E_TENANT_ID (falls back to aurora-dental-ar fixture)
 *
 * ★ PLACEHOLDER STATUS: PNGs not generated yet (no live stack at test-author time).
 * FIRST EXECUTION: must use --update-snapshots to establish baseline.
 * After baseline established, subsequent runs enforce maxDiffPixelRatio: 0.001.
 *
 * Run to GENERATE baseline (stack UP required):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     E2E_OFFER_ID=<offerId> npx playwright test lisa-servicios-visual --project=visual --update-snapshots
 *
 * Run to VERIFY against baseline:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     E2E_OFFER_ID=<offerId> npx playwright test lisa-servicios-visual --project=visual
 *
 * G5 pre-commit gate (no stack required — just spec lint):
 *   cd vitalia/frontend && npx tsc --noEmit && npx eslint e2e/visual/lisa-servicios-visual.spec.ts
 *
 * downstream-regression-na: brand-local vitalia E2E visual spec T-8
 *
 * @see 06-tickets.yaml T-8 deliverables (visual goldens)
 * @see vitalia/.claude/rules/shell-mockup-per-component.md — ratchet rule (shrink-only)
 * @see vitalia/docs/architecture/ADR-vitalia-003-shell-mockup-per-component-protocol.md
 */

import { expect } from "@playwright/test";
import {
  test,
  TENANT_ID,
} from "../fixtures/real-backend-forward.fixture";
import { ServiciosCatalogoPage } from "../pages/ServiciosCatalogoPage";
import { EscaleraPage } from "../pages/EscaleraPage";
import { ServicioWorkspacePage } from "../pages/ServicioWorkspacePage";
import { NuevoServicioPage } from "../pages/NuevoServicioPage";

const OFFER_ID = process.env["E2E_OFFER_ID"];

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function setTheme(page: import("@playwright/test").Page, theme: "light" | "dark"): Promise<void> {
  await page.evaluate((t) => {
    document.documentElement.classList.remove("light", "dark");
    document.documentElement.classList.add(t);
    localStorage.setItem("theme", t);
  }, theme);
  // Brief wait for CSS transitions
  await page.waitForTimeout(200);
}

// ---------------------------------------------------------------------------
// Catálogo goldens
// ---------------------------------------------------------------------------

test.describe("Catálogo — visual goldens", () => {
  for (const theme of ["light", "dark"] as const) {
    test(`catalogo-${theme}.png`, async ({ page }) => {
      const catalogo = new ServiciosCatalogoPage(page);
      await catalogo.goto(TENANT_ID);
      await setTheme(page, theme);

      // Wait for content to stabilize
      await page.waitForLoadState("networkidle", { timeout: 15_000 });

      await expect(page).toHaveScreenshot(`catalogo-${theme}.png`, {
        maxDiffPixelRatio: 0.001,
        // Clip to the main content area — avoid flaky topbar/sidebar changes
        clip: { x: 0, y: 0, width: 1280, height: 900 },
        animations: "disabled",
      });
    });
  }
});

// ---------------------------------------------------------------------------
// Escalera goldens
// ---------------------------------------------------------------------------

test.describe("Escalera — visual goldens", () => {
  for (const theme of ["light", "dark"] as const) {
    test(`escalera-${theme}.png`, async ({ page }) => {
      const escalera = new EscaleraPage(page);
      await escalera.goto(TENANT_ID);
      await setTheme(page, theme);

      await escalera.waitForBoard();
      await page.waitForLoadState("networkidle", { timeout: 15_000 });

      await expect(page).toHaveScreenshot(`escalera-${theme}.png`, {
        maxDiffPixelRatio: 0.001,
        clip: { x: 0, y: 0, width: 1280, height: 900 },
        animations: "disabled",
      });
    });
  }
});

// ---------------------------------------------------------------------------
// Servicio workspace goldens
// ---------------------------------------------------------------------------

test.describe("Servicio workspace — visual goldens", () => {
  test.skip(!OFFER_ID, "Requires E2E_OFFER_ID");

  for (const theme of ["light", "dark"] as const) {
    test(`servicio-workspace-${theme}.png`, async ({ page }) => {
      const workspace = new ServicioWorkspacePage(page);
      await workspace.goto(TENANT_ID, OFFER_ID!, "resumen");
      await setTheme(page, theme);

      await workspace.isWorkspaceVisible();
      await page.waitForLoadState("networkidle", { timeout: 15_000 });

      await expect(page).toHaveScreenshot(`servicio-workspace-${theme}.png`, {
        maxDiffPixelRatio: 0.001,
        clip: { x: 0, y: 0, width: 1280, height: 900 },
        animations: "disabled",
      });
    });
  }
});

// ---------------------------------------------------------------------------
// Nuevo servicio goldens
// ---------------------------------------------------------------------------

test.describe("Nuevo servicio picker — visual goldens", () => {
  for (const theme of ["light", "dark"] as const) {
    test(`nuevo-servicio-${theme}.png`, async ({ page }) => {
      const catalogo = new ServiciosCatalogoPage(page);
      const picker = new NuevoServicioPage(page);

      await catalogo.goto(TENANT_ID);
      await catalogo.openNuevoServicio();
      await setTheme(page, theme);

      await picker.isPickerVisible();
      await page.waitForTimeout(300); // Wait for picker animation

      await expect(page).toHaveScreenshot(`nuevo-servicio-${theme}.png`, {
        maxDiffPixelRatio: 0.001,
        clip: { x: 0, y: 0, width: 1280, height: 900 },
        animations: "disabled",
      });
    });
  }
});
