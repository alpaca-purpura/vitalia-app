// cap: clinics.lisa.doctores
// story-origin: vitalia-bugfix-horarios-toolbar-sticky
/**
 * toolbar-sticky.spec.ts — BEHAVIOURAL guard for the Horarios toolbar-sticky bug.
 *
 * This is the guard that the jsdom structural test could NOT be (verde-fantasma):
 * a REAL browser with a REAL layout engine. It scrolls the actual hour-grid
 * scroller and asserts that the page toolbars + day-header DO NOT move (their
 * boundingBox().top stays put) while the grid content scrolls under them — the
 * exact behaviour Chris asked for ("la barra de opciones debería ser fixed,
 * igual que N2/N3").
 *
 * BUG (verified live 2026-06-15, root cause = CORE @luana/ui-kit AppPanelSlot):
 *   The panel content host was a CSS `block`, so EWL sheets (flex-1 root) didn't
 *   clamp → the whole panel scrolled and dragged the toolbars. Fixed by making
 *   the content host a flex-column (`flex flex-col flex-1 min-h-0 overflow-y-auto`)
 *   so EWL clamps and the inner grid becomes the scroller. See T-1-LIVE-VERIFY.md.
 *
 * Layout-behaviour, NOT data-contract: toolbar fixity depends on the CSS scroll
 * chain, not on real availability data. We mock the occurrences endpoint with a
 * tall set so the grid genuinely overflows even in reduced (07–21) view, and we
 * activate "Mostrar 24 horas" (24×48 = 1152px) to guarantee overflow on small
 * viewports. The grid scroller comes from CSS; if the chain regresses, the panel
 * scrolls and these asserts fail (toolbars move) — which is the whole point.
 *
 * Run (native host — NEVER `make e2e*`):
 *   cd vitalia/frontend && bash ../../scripts/e2e-preflight.sh
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/regression/vitalia-bugfix-horarios-toolbar-sticky/toolbar-sticky.spec.ts \
 *     --project=smoke
 *
 * spec_anchor: story-origin checkpoint § "Bar de verificación (DONE)"
 * downstream-regression-na: brand-local vitalia regression spec (consumes core fix)
 */

import { test, expect } from "../../fixtures/vitalia-fase2-lisa-doctores.fixture";
import type { Page } from "@playwright/test";

const TENANT_ID =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";
const DOCTOR_ID = process.env["E2E_DOCTOR_ID"] ?? "doctor-ana-001";

// Movement tolerance: a fixed element's rect.top must not drift more than this
// (px) while the grid scrolls. Sub-pixel rounding/layout jitter < 2px is benign;
// the bug moved toolbars by hundreds of px (heading 209 → -627 live).
const MAX_DRIFT_PX = 2;

/**
 * Mock the availability-occurrences endpoint with a block on every weekday so
 * the grid always has content. Overflow is guaranteed by the 24h toggle, not by
 * the data — but having blocks makes the scroll exercise realistic.
 */
async function mockTallOccurrences(page: Page): Promise<void> {
  await page.route(
    `**/api/v1/vitalia/clinics/doctors/*/availability-occurrences**`,
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      const url = new URL(route.request().url());
      const from = url.searchParams.get("from") ?? "2026-01-05"; // a Monday
      const occurrences = Array.from({ length: 5 }, (_, dow) => {
        const d = new Date(`${from}T00:00:00`);
        d.setDate(d.getDate() + dow);
        const iso = d.toISOString().slice(0, 10);
        return {
          blockId: `blk-sticky-${dow}`,
          occurrenceDate: iso,
          startTime: "08:00",
          endTime: "18:00",
          kind: "recurrent" as const,
          freq: "weekly" as const,
          patternSummary: "Cada semana",
        };
      });
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ occurrences }),
      });
    },
  );
}

test.describe("Horarios toolbar stays fixed while the hour grid scrolls", () => {
  test("page toolbar + day-header keep their top while the grid scrolls (24h)", async ({
    staffPage,
  }) => {
    const page = staffPage;
    await mockTallOccurrences(page);

    // Small viewport forces overflow even more aggressively than 1440×900.
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto(`/${TENANT_ID}/lisa/staff/${DOCTOR_ID}/horarios`, {
      waitUntil: "domcontentloaded",
    });

    // Wait for the calendar to mount (skeleton → grid).
    const grid = page.getByRole("grid", {
      name: /calendario de disponibilidad/i,
    });
    await grid.waitFor({ state: "visible", timeout: 20_000 });

    // Activate "Mostrar 24 horas" → 24×48 = 1152px → guaranteed overflow @720h.
    const toggle24 = page.getByTestId("toggle-24h");
    await toggle24.click();
    await expect(toggle24).toHaveAttribute("aria-pressed", "true");

    // Fixed-frame elements whose top must NOT move when the grid scrolls.
    const heading = page.getByRole("heading", { name: "Disponibilidad" });
    const toggleSemana = page.getByTestId("toggle-semana");
    const weekNavPrev = page.getByTestId("week-nav-prev");
    const dayHeader = page.getByTestId("day-col-0"); // lives in the sticky day-header row

    // Sanity: everything is on-screen before scrolling.
    for (const loc of [heading, toggleSemana, weekNavPrev, toggle24, dayHeader]) {
      await expect(loc).toBeVisible();
    }

    const before = {
      heading: (await heading.boundingBox())!,
      toggleSemana: (await toggleSemana.boundingBox())!,
      weekNavPrev: (await weekNavPrev.boundingBox())!,
      toggle24: (await toggle24.boundingBox())!,
      dayHeader: (await dayHeader.boundingBox())!,
    };

    // Confirm the grid is actually a scroller (scrollHeight > clientHeight) and
    // scroll it. If the chain regressed, the grid is NOT the scroller and the
    // panel scrolls instead — the toolbars would then move (caught below).
    const scrollAmount = 600;
    const gridMetrics = await grid.evaluate((el, amount) => {
      const before = {
        scrollHeight: el.scrollHeight,
        clientHeight: el.clientHeight,
      };
      el.scrollTop = amount;
      return { ...before, scrollTop: el.scrollTop };
    }, scrollAmount);

    // The grid must overflow and must have actually scrolled (the fix moved the
    // scroll into this element). scrollTop > 0 proves the grid owns the scroll.
    expect(gridMetrics.scrollHeight).toBeGreaterThan(gridMetrics.clientHeight);
    expect(gridMetrics.scrollTop).toBeGreaterThan(0);

    // Let layout settle after the scroll.
    await page.waitForTimeout(150);

    const after = {
      heading: (await heading.boundingBox())!,
      toggleSemana: (await toggleSemana.boundingBox())!,
      weekNavPrev: (await weekNavPrev.boundingBox())!,
      toggle24: (await toggle24.boundingBox())!,
      dayHeader: (await dayHeader.boundingBox())!,
    };

    // The ASSERTION that the jsdom guard could not make: toolbars stay put.
    expect(Math.abs(after.heading.y - before.heading.y)).toBeLessThanOrEqual(
      MAX_DRIFT_PX,
    );
    expect(
      Math.abs(after.toggleSemana.y - before.toggleSemana.y),
    ).toBeLessThanOrEqual(MAX_DRIFT_PX);
    expect(
      Math.abs(after.weekNavPrev.y - before.weekNavPrev.y),
    ).toBeLessThanOrEqual(MAX_DRIFT_PX);
    expect(Math.abs(after.toggle24.y - before.toggle24.y)).toBeLessThanOrEqual(
      MAX_DRIFT_PX,
    );

    // The day-header row is `sticky top-0` inside the grid — it stays atop the
    // scrolling hours (its top should not move beyond tolerance either).
    expect(
      Math.abs(after.dayHeader.y - before.dayHeader.y),
    ).toBeLessThanOrEqual(MAX_DRIFT_PX);
  });
});
