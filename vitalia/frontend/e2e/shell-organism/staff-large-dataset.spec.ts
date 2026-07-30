// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
// T-E2E vitalia-fase2-lisa-doctores
/**
 * staff-large-dataset.spec.ts
 *
 * Covers: SC-9 — large_dataset: 1200 doctores (pagination + perf).
 *
 * Visual goldens V-VIS-1..4 were RELOCATED to:
 *   e2e/regression/vitalia-fase2-lisa-doctores/visual-goldens.spec.ts
 * (T-FIX-2 2026-06-01) so they run in project=visual with snapshotPathTemplate
 * and maxDiffPixelRatio config. They are excluded from project=smoke via
 * testIgnore: /.*\/visual-goldens\.spec\.ts/.
 *
 * spec_anchor: 04-validators.yaml § V-NF-5
 */

import { expect } from "@playwright/test";
import {
  test,
  STAFF_SEED,
  setupLargeDatasetMock,
} from "../fixtures/vitalia-fase2-lisa-doctores.fixture";
import { StaffDirectoryPage } from "../pages/StaffDirectoryPage";

const TENANT_ID = STAFF_SEED.tenantA.id;

// ---------------------------------------------------------------------------
// SC-9: large dataset performance
// ---------------------------------------------------------------------------

test.describe("SC-9 — large_dataset: 1200 doctores, rendimiento paginación", () => {
  test("página 1: 24 cards, nav siguiente <500ms, sin freeze", async ({
    staffPage,
    resetMocks,
  }) => {
    await resetMocks();
    await setupLargeDatasetMock(staffPage);

    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await directory.waitForDirectoryToLoad();

    // Page 1: 24 cards
    await directory.assertCardCount(24);

    // Navigate to page 2 and measure time (spec budget: <500ms).
    // Reverted builder relaxation 3000ms→500ms 2026-05-31: the budget is the spec's
    // stated SLO, not a knob to widen for green. If it flakes in test-env, fix the
    // measurement (exclude setup overhead), not the threshold.
    const t0 = Date.now();
    const nextButton = directory.paginationNext;
    if (await nextButton.isVisible()) {
      await nextButton.click();
      await directory.waitForDirectoryToLoad();
      const elapsed = Date.now() - t0;
      expect(elapsed).toBeLessThan(500);
      await directory.assertCardCount(24);
    }
  });

  test("search/filter: render post-debounce responde <500ms con 1200 doctores mock", async ({
    staffPage,
    resetMocks,
  }) => {
    await resetMocks();
    await setupLargeDatasetMock(staffPage);

    const directory = new StaffDirectoryPage(staffPage);
    await directory.goto(TENANT_ID);
    await directory.waitForDirectoryToLoad();

    // Measure ONLY the post-debounce render latency (spec SLO: <500ms).
    // searchForAndMeasureRender() waits for debounce to settle first, then
    // measures only the DOM render phase — this is the correct measurement.
    // Previously POM.searchFor() included the 500ms debounce in the timer,
    // making <500ms physically impossible. Fixed T-FIX-2 (2026-06-01).
    const elapsed = await directory.searchForAndMeasureRender("Dr. 5");
    expect(elapsed).toBeLessThan(500);

    // No crash
    const bodyHeight = await staffPage.evaluate(() => document.body.scrollHeight);
    expect(bodyHeight).toBeGreaterThan(0);
  });
});

