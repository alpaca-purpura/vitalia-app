/**
 * lisa-marca-visual.spec.ts — FE visual goldens T-11
 *
 * F2-S7 vitalia-fase2-lisa-marca
 * Ticket: T-11 — FE visual goldens — 3 subsubtabs × 2 themes = 6 PNGs
 *
 * 6 snapshots:
 *   Identidad × 2 themes:
 *     1. identidad-light.png
 *     2. identidad-dark.png
 *   Voz y tono × 2 themes:
 *     3. voz-y-tono-light.png
 *     4. voz-y-tono-dark.png
 *   Presencia × 2 themes:
 *     5. presencia-light.png
 *     6. presencia-dark.png
 *
 * Threshold: maxDiffPixelRatio: 0.001 (0.1% tolerance)
 * Animations disabled (playwright.config.ts project=visual)
 * Tenant: clinica-salud-vitalia-pe (PE locale, PEN currency) — deterministic
 * Data: fixture API mocks via page.route (no real BE required)
 *
 * Snapshot output path (per snapshotPathTemplate):
 *   vitalia/frontend/e2e/__screenshots__/{testFilePath}/{arg}{ext}
 *   → e2e/__screenshots__/visual/lisa-marca-visual.spec.ts/{name}-chromium.png
 *
 * Run to GENERATE baseline (requires app running on E2E_BASE_URL):
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/lisa-marca-visual.spec.ts --project=visual --update-snapshots
 *
 * Run to VERIFY against baseline:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/visual/lisa-marca-visual.spec.ts --project=visual
 *
 * G5 pre-commit smoke gate (no running stack required):
 *   cd vitalia/frontend && npx tsc --noEmit
 *   npx eslint e2e/visual/lisa-marca-visual.spec.ts --cache
 *   npx playwright test --list e2e/visual/lisa-marca-visual.spec.ts
 *
 * NOTES FOR AUDITOR:
 *   - Snapshots are PLACEHOLDERS: 6 PNGs have NOT been generated yet (no running stack).
 *   - First execution on staging MUST use --update-snapshots to establish baseline.
 *   - After baseline generated, subsequent runs enforce maxDiffPixelRatio: 0.001.
 *   - Ratchet rule: once ratified, snapshots shrink-only (per shell-mockup-per-component.md).
 *
 * downstream-regression-na: brand-local vitalia E2E visual spec F2-S7 T-11
 *
 * @see T-10-result.md — POMs + fixtures (dependency)
 * @see 06-tickets.yaml T-11 deliverables
 * @see vitalia/.claude/rules/shell-mockup-per-component.md — ratchet rule
 */

import { expect } from "@playwright/test";
import {
  test,
  LISA_MARCA_FIXTURE,
  gotoMarca,
  setupLisaMarcaMocks,
} from "../regression/vitalia-fase2-lisa-marca/fixtures/lisa-marca.fixture";
import { LisaMarcaPage } from "../regression/vitalia-fase2-lisa-marca/poms/lisa-marca-page.pom";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const { tenantId } = LISA_MARCA_FIXTURE;

/** 0.1% pixel diff tolerance for stable mocked data. */
const THRESHOLD = { maxDiffPixelRatio: 0.001 } as const;

/**
 * Mask dynamic elements that change on every render
 * (autosave badge with timestamps, loading spinners).
 */
const DYNAMIC_MASKS = (page: import("@playwright/test").Page) => [
  page.locator('[data-testid="autosave-badge"]'),
  page.locator('[data-testid="lisa-marca-loading-skeleton"]'),
];

// ---------------------------------------------------------------------------
// Theme helpers
// ---------------------------------------------------------------------------

async function applyLightMode(
  page: import("@playwright/test").Page,
): Promise<void> {
  await page.evaluate(() => {
    document.documentElement.classList.remove("dark");
    document.documentElement.setAttribute("data-theme", "light");
  });
}

async function applyDarkMode(
  page: import("@playwright/test").Page,
): Promise<void> {
  await page.evaluate(() => {
    document.documentElement.classList.add("dark");
    document.documentElement.setAttribute("data-theme", "dark");
  });
}

// ---------------------------------------------------------------------------
// 1–2: Identidad sub-sub-tab × 2 themes
// ---------------------------------------------------------------------------

test.describe("Identidad sub-sub-tab — visual goldens", () => {
  test.beforeEach(async ({ marcaPage }) => {
    await setupLisaMarcaMocks(marcaPage, tenantId);
    await gotoMarca(marcaPage, tenantId, "identidad");
    const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
    await lisaMarcaPage.waitForLoaded();
  });

  test("identidad-light — identidad sub-sub-tab, light mode", async ({
    marcaPage,
  }) => {
    await applyLightMode(marcaPage);

    await expect(marcaPage).toHaveScreenshot("identidad-light.png", {
      ...THRESHOLD,
      mask: DYNAMIC_MASKS(marcaPage),
    });
  });

  test("identidad-dark — identidad sub-sub-tab, dark mode", async ({
    marcaPage,
  }) => {
    await applyDarkMode(marcaPage);

    await expect(marcaPage).toHaveScreenshot("identidad-dark.png", {
      ...THRESHOLD,
      mask: DYNAMIC_MASKS(marcaPage),
    });
  });
});

// ---------------------------------------------------------------------------
// 3–4: Voz y tono sub-sub-tab × 2 themes
// ---------------------------------------------------------------------------

test.describe("Voz y tono sub-sub-tab — visual goldens", () => {
  test.beforeEach(async ({ marcaPage }) => {
    await setupLisaMarcaMocks(marcaPage, tenantId);
    await gotoMarca(marcaPage, tenantId, "voz-y-tono");
    const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
    await lisaMarcaPage.waitForLoaded();
  });

  test("voz-y-tono-light — voz y tono sub-sub-tab, light mode", async ({
    marcaPage,
  }) => {
    await applyLightMode(marcaPage);

    await expect(marcaPage).toHaveScreenshot("voz-y-tono-light.png", {
      ...THRESHOLD,
      mask: DYNAMIC_MASKS(marcaPage),
    });
  });

  test("voz-y-tono-dark — voz y tono sub-sub-tab, dark mode", async ({
    marcaPage,
  }) => {
    await applyDarkMode(marcaPage);

    await expect(marcaPage).toHaveScreenshot("voz-y-tono-dark.png", {
      ...THRESHOLD,
      mask: DYNAMIC_MASKS(marcaPage),
    });
  });
});

// ---------------------------------------------------------------------------
// 5–6: Presencia sub-sub-tab × 2 themes
// ---------------------------------------------------------------------------

test.describe("Presencia sub-sub-tab — visual goldens", () => {
  test.beforeEach(async ({ marcaPage }) => {
    await setupLisaMarcaMocks(marcaPage, tenantId);
    await gotoMarca(marcaPage, tenantId, "presencia");
    const lisaMarcaPage = new LisaMarcaPage(marcaPage, tenantId);
    await lisaMarcaPage.waitForLoaded();
  });

  test("presencia-light — presencia sub-sub-tab, light mode", async ({
    marcaPage,
  }) => {
    await applyLightMode(marcaPage);

    await expect(marcaPage).toHaveScreenshot("presencia-light.png", {
      ...THRESHOLD,
      mask: DYNAMIC_MASKS(marcaPage),
    });
  });

  test("presencia-dark — presencia sub-sub-tab, dark mode", async ({
    marcaPage,
  }) => {
    await applyDarkMode(marcaPage);

    await expect(marcaPage).toHaveScreenshot("presencia-dark.png", {
      ...THRESHOLD,
      mask: DYNAMIC_MASKS(marcaPage),
    });
  });
});
