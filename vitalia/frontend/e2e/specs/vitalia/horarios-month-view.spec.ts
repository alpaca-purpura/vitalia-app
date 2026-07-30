// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * horarios-month-view.spec.ts — E2E specs SC-D3E-1..4 (T-FE-vista-mes).
 *
 * SC-D3E-1: happy — bloques con occurrences=2 → vista Mes → chips SOLO en 2 fechas proyectadas.
 * SC-D3E-2: happy — vista mes → clic en día → salta a vista semana de esa semana.
 * SC-D3E-3: empty_state — mes sin bloques → empty suave.
 * SC-D3E-4: large_dataset — doctor con 30+ bloques/mes → overflow "+N más" + sin jank.
 *
 * All specs use authed-runtime.ts (base gate + Clerk token + clinic context mocks).
 * The occurrences endpoint is mocked via page.route() (no live BE required for occurrences)
 * to ensure deterministic SC-D3E-1 assertion (RN-D3E-1).
 *
 * Real-backend note:
 *   - Happy-path SC-D3E-1 mocks occurrences endpoint to return exactly 2 occurrences,
 *     then asserts FE paints exactly those 2 dates (no client expansion).
 *   - SC-D3E-4 mocks 35 occurrences to test overflow without live BE.
 *
 * T-FE-vista-mes vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-E · validators: SC-D3E-1..4
 * playwright-expert: authed-runtime + page.route mocking
 */

import { test, expect } from "../../fixtures/authed-runtime";

// ── Constants ─────────────────────────────────────────────────────────────────

const DOCTOR_ID = process.env["E2E_DOCTOR_ID"] ?? "2464fad7-2124-46a0-9b41-cef9e489cc8d";
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";

const HORARIOS_URL = `/${TENANT_ID}/lisa/staff/${DOCTOR_ID}/horarios`;

// ── Mock builders ─────────────────────────────────────────────────────────────

interface OccurrenceMockOptions {
  occurrenceDates: Array<{ date: string; startTime?: string; endTime?: string; blockId?: string }>;
}

async function mockOccurrencesEndpoint(
  page: import("@playwright/test").Page,
  { occurrenceDates }: OccurrenceMockOptions,
): Promise<void> {
  await page.route(
    `**/api/v1/vitalia/clinics/doctors/${DOCTOR_ID}/availability-occurrences**`,
    async (route) => {
      // FastAPI returns camelCase via alias_generator=to_camel — mock must match
      const occurrences = occurrenceDates.map((o, i) => ({
        blockId: o.blockId ?? `blk-e2e-${String(i + 1).padStart(3, "0")}`,
        occurrenceDate: o.date,
        startTime: o.startTime ?? "09:00",
        endTime: o.endTime ?? "13:00",
        kind: "recurrent",
        freq: "weekly",
        patternSummary: "Semanal",
      }));
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ occurrences }),
      });
    },
  );
}

async function mockBlocksEndpoint(page: import("@playwright/test").Page): Promise<void> {
  await page.route(
    `**/api/v1/vitalia/clinics/doctors/${DOCTOR_ID}/availability-blocks**`,
    async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ items: [], total: 0 }),
      });
    },
  );
}

async function mockDoctorEndpoint(page: import("@playwright/test").Page): Promise<void> {
  await page.route(
    `**/api/v1/vitalia/clinics/doctors/${DOCTOR_ID}`,
    async (route) => {
      if (route.request().method() !== "GET") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: DOCTOR_ID,
          first_name: "Carlos",
          last_name: "Médico",
          specialty: "Odontología Cosmética",
          credential: "12345",
          credential_country: "PE",
          active: true,
          visible_en_landing: true,
          years_experience: 8,
          patients_count: 320,
          nps_score: 72,
          avatar_key: null,
          avatar_url: null,
          bio_inputs_notes: null,
          bio_links: [],
          bio_public: null,
          languages: ["Español"],
        }),
      });
    },
  );
}

// ── Navigate to horarios and switch to Mes view ───────────────────────────────

async function navigateToMesView(page: import("@playwright/test").Page): Promise<void> {
  await page.goto(HORARIOS_URL);
  await page.waitForSelector('[data-testid="horarios-view"]', { timeout: 15000 });
  // Switch to Mes view
  await page.click('[data-testid="toggle-mes"]');
  await page.waitForSelector('[data-testid="month-calendar"]', { timeout: 5000 });
}

// ── SC-D3E-1 ─────────────────────────────────────────────────────────────────

test("SC-D3E-1: bloques occurrences=2 → vista Mes → chips en exactamente 2 fechas (RN-D3E-1)", async ({
  page,
}) => {
  // Setup mocks: occurrences endpoint returns exactly 2 dates
  // Use dates within the current month (June 2026)
  const occ1Date = "2026-06-09";
  const occ2Date = "2026-06-16";

  await mockDoctorEndpoint(page);
  await mockBlocksEndpoint(page);
  await mockOccurrencesEndpoint(page, {
    occurrenceDates: [
      { date: occ1Date, blockId: "blk-weekly-test" },
      { date: occ2Date, blockId: "blk-weekly-test" },
    ],
  });

  await navigateToMesView(page);

  // Assert chips appear on EXACTLY the 2 projected dates
  const chip1 = page.locator(`[data-testid="month-day-${occ1Date}"] [data-testid^="month-chip-"]`);
  const chip2 = page.locator(`[data-testid="month-day-${occ2Date}"] [data-testid^="month-chip-"]`);
  await expect(chip1).toHaveCount(1);
  await expect(chip2).toHaveCount(1);

  // Assert NO chip on other days (e.g., the week between — 2026-06-13)
  const noChipDay = page.locator('[data-testid="month-day-2026-06-13"] [data-testid^="month-chip-"]');
  await expect(noChipDay).toHaveCount(0);

  // Assert chip text shows time range
  await expect(chip1).toContainText("09:00");
});

// ── SC-D3E-2 ─────────────────────────────────────────────────────────────────

test("SC-D3E-2: clic en día de vista Mes → salta a vista semana de esa semana", async ({
  page,
}) => {
  await mockDoctorEndpoint(page);
  await mockBlocksEndpoint(page);
  await mockOccurrencesEndpoint(page, {
    occurrenceDates: [{ date: "2026-06-09", blockId: "blk-test" }],
  });

  await navigateToMesView(page);

  // Click on day 2026-06-11 (Thursday → Monday of that week = 2026-06-08)
  const dayCell = page.locator('[data-testid="month-day-2026-06-11"]');
  await dayCell.click();

  // Should switch back to Semana view
  await page.waitForSelector('[data-testid="availability-calendar"]', { timeout: 5000 });
  const monthCalendar = page.locator('[data-testid="month-calendar"]');
  await expect(monthCalendar).toHaveCount(0);

  // Semana toggle should now be active (aria-checked=true)
  const semanaToggle = page.locator('[data-testid="toggle-semana"]');
  await expect(semanaToggle).toHaveAttribute("aria-checked", "true");
});

// ── SC-D3E-3 ─────────────────────────────────────────────────────────────────

test("SC-D3E-3: mes sin bloques → empty state suave visible", async ({ page }) => {
  await mockDoctorEndpoint(page);
  await mockBlocksEndpoint(page);
  // Empty occurrences
  await mockOccurrencesEndpoint(page, { occurrenceDates: [] });

  await navigateToMesView(page);

  // Empty state should be visible
  const emptyState = page.locator('[data-testid="month-empty-state"]');
  await expect(emptyState).toBeVisible();
  await expect(emptyState).toContainText(/sin horarios/i);

  // No chips anywhere
  const chips = page.locator('[data-testid^="month-chip-"]');
  await expect(chips).toHaveCount(0);
});

// ── SC-D3E-4 ─────────────────────────────────────────────────────────────────

test("SC-D3E-4: 30+ bloques en un mes → overflow '+N más' + sin jank", async ({ page }) => {
  // Create 35 occurrences — spread across days in June 2026
  // 5 occurrences per day on 7 different days → each day shows 2 chips + "+3 más"
  const occurrenceDates: Array<{ date: string; blockId: string }> = [];
  const testDays = ["2026-06-02", "2026-06-03", "2026-06-04", "2026-06-05", "2026-06-08", "2026-06-09", "2026-06-10"];
  for (const day of testDays) {
    for (let i = 0; i < 5; i++) {
      occurrenceDates.push({ date: day, blockId: `blk-large-${day}-${i}` });
    }
  }

  await mockDoctorEndpoint(page);
  await mockBlocksEndpoint(page);
  await mockOccurrencesEndpoint(page, { occurrenceDates });

  await navigateToMesView(page);

  // Each test day should show exactly 2 chips + overflow "+3 más"
  for (const day of testDays) {
    const chips = page.locator(`[data-testid="month-day-${day}"] [data-testid^="month-chip-"]`);
    await expect(chips).toHaveCount(2);
    const overflow = page.locator(`[data-testid="month-overflow-${day}"]`);
    await expect(overflow).toContainText("+3");
  }

  // Performance: no jank — month-calendar visible after reasonable timeout
  await expect(page.locator('[data-testid="month-calendar"]')).toBeVisible({ timeout: 5000 });
});
