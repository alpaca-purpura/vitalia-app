// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * lisa-recurrencia-chips.spec.ts — SC-D3F-5: day chips keyboard a11y.
 *
 * Covers:
 *   SC-D3F-5: "Personalizado…" sub-editor day chips respond to tab/space/enter.
 *     - Selecting "Personalizado…" shows the sub-editor with day chips.
 *     - Space bar toggles a chip (aria-checked flips).
 *     - Enter toggles a chip.
 *     - Cannot deselect the last remaining chip (min 1 day enforced).
 *     - Summary updates reactively as chips are toggled.
 *
 * Network: staff endpoints mocked via page.route — no live BE required.
 * Auth: Clerk testing token bypass via auth.fixture.
 *
 * Comando nativo:
 *   cd vitalia/frontend && E2E_BASE_URL=http://localhost:3002 \
 *     npx playwright test e2e/specs/vitalia/lisa-recurrencia-chips.spec.ts --project=smoke
 * NUNCA: make e2e / make e2e-smoke (Docker — crashea laptop).
 *
 * spec_anchor: 01-spec.md § SC-D3F-5 + 04-validators.yaml § e2e_required
 * T-FE-recurrencia-editor vitalia-fase2-lisa-doctores
 */

import { test, expect } from "../../fixtures/base";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DOCTOR_ID = "doctor-ana-001";
const TENANT_ID = process.env["E2E_TENANT_ID"] ?? "vitalia-test-tenant";

// ---------------------------------------------------------------------------
// Helpers: mock staff API routes
// ---------------------------------------------------------------------------

async function mockStaffRoutes(page: import("@playwright/test").Page) {
  // Mock blocks endpoint (empty — calendar starts clean)
  await page.route("**/api/v1/vitalia/clinics/doctors/*/availability-blocks", (route) => {
    if (route.request().method() === "GET") {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    }
    // POST → return mock block
    return route.fulfill({
      status: 201,
      contentType: "application/json",
      body: JSON.stringify({
        id: "block-test-001",
        kind: "recurrent",
        days_of_week: [0, 3],
        interval: 2,
        start_time: "09:00",
        end_time: "13:00",
        end_condition_kind: "occurrences",
        occurrences: 8,
        end_date: null,
      }),
    });
  });

  // Mock occurrences endpoint (empty)
  await page.route("**/api/v1/vitalia/clinics/doctors/*/availability-occurrences*", (route) => {
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ occurrences: [] }),
    });
  });

  // Mock doctor detail
  await page.route(`**/api/v1/vitalia/clinics/doctors/${DOCTOR_ID}`, (route) => {
    if (route.request().method() !== "GET") return route.continue();
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: DOCTOR_ID,
        first_name: "Ana",
        last_name: "García",
        specialty: "Odontología",
        active: true,
        visible_en_landing: true,
        credential: "12345",
        credential_country: "PE",
        email: "ana@example.com",
        dni: "***4521",
        languages: [],
        bio_links: [],
      }),
    });
  });

  // Mock doctor list (needed by EntityPicker if rendered)
  await page.route(`**/api/v1/vitalia/clinics/doctors**`, (route) => {
    if (route.request().method() !== "GET") return route.continue();
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        items: [{
          id: DOCTOR_ID,
          first_name: "Ana",
          last_name: "García",
          specialty: "Odontología",
          dni_masked: "***4521",
          active: true,
          visible_en_landing: true,
          years_experience: 8,
          patients_count: 320,
          nps_score: 72,
          avatar_url: null,
        }],
        total: 1,
        page: 1,
        page_size: 24,
        pages: 1,
      }),
    });
  });
}

/**
 * Helper: navigate to horarios, wait for calendar, trigger popover via
 * proper mouse drag on a cell (mousedown + mousemove + mouseup on same cell).
 */
async function openPopoverViaNewBlock(page: import("@playwright/test").Page) {
  const baseUrl = process.env["E2E_BASE_URL"] ?? "http://localhost:3002";
  const url = `${baseUrl}/${TENANT_ID}/lisa/staff/${DOCTOR_ID}/horarios`;

  await page.goto(url, { waitUntil: "networkidle" });

  // Wait for calendar to render
  const calendar = page.locator('[data-testid="availability-calendar"]');
  await expect(calendar).toBeVisible({ timeout: 15_000 });

  // Use cell-0-9 (Monday at 09:00) for reliable positioning
  const cell = page.locator('[data-testid="cell-0-9"]');
  await expect(cell).toBeVisible({ timeout: 10_000 });

  // Get cell bounding box for precise mouse events
  const bbox = await cell.boundingBox();
  if (!bbox) throw new Error("cell-0-9 not found or not rendered");

  const cx = bbox.x + bbox.width / 2;
  const cy = bbox.y + bbox.height / 2;

  // Simulate drag: mousedown on cell → small move → mouseup on same cell
  // This triggers handleCellMouseDown + handleCellMouseUp on same cell → popover opens
  await page.mouse.move(cx, cy);
  await page.mouse.down();
  // Small move to register isDragging
  await page.mouse.move(cx, cy + 2);
  // Mouseup on the same cell area to fire onMouseUp → opens popover
  await page.mouse.up();

  // Wait for popover
  const popover = page.locator('[data-testid="bloque-popover"]');
  await expect(popover).toBeVisible({ timeout: 8_000 });

  return popover;
}

// ---------------------------------------------------------------------------
// SC-D3F-5 — day chips keyboard a11y
// ---------------------------------------------------------------------------

test.describe("SC-D3F-5 — BloquePopover day chips keyboard a11y", () => {
  test.beforeEach(async ({ page }) => {
    await mockStaffRoutes(page);
  });

  test("SC-D3F-5a: selecting Personalizado shows day chips sub-editor", async ({ page }) => {
    await openPopoverViaNewBlock(page);

    // Select "Personalizado…" via the Repetir select
    const selectTrigger = page.locator('[data-testid="select-repetir"]');
    await expect(selectTrigger).toBeVisible();
    await selectTrigger.click();

    // Select "Personalizado…"
    await page.getByRole("option", { name: "Personalizado…" }).click();

    // Custom sub-editor should appear
    const customEditor = page.locator('[data-testid="custom-recurrence-editor"]');
    await expect(customEditor).toBeVisible();

    // Day chips group should be visible
    const dayChipsGroup = page.locator('[data-testid="day-chips-group"]');
    await expect(dayChipsGroup).toBeVisible();
  });

  test("SC-D3F-5b: space key toggles day chip aria-checked", async ({ page }) => {
    await openPopoverViaNewBlock(page);

    const selectTrigger = page.locator('[data-testid="select-repetir"]');
    await selectTrigger.click();
    await page.getByRole("option", { name: "Personalizado…" }).click();

    // Day chips should be visible
    const dayChipsGroup = page.locator('[data-testid="day-chips-group"]');
    await expect(dayChipsGroup).toBeVisible();

    // Monday (index 0) should be selected (default from drag on Monday col)
    const mondayChip = page.locator('[data-testid="day-chip-0"]');
    await expect(mondayChip).toHaveAttribute("aria-checked", "true");

    // Tuesday chip (index 1) should NOT be selected
    const tuesdayChip = page.locator('[data-testid="day-chip-1"]');
    await expect(tuesdayChip).toHaveAttribute("aria-checked", "false");

    // Focus Tuesday chip and press Space to select it
    await tuesdayChip.focus();
    await tuesdayChip.press(" ");
    await expect(tuesdayChip).toHaveAttribute("aria-checked", "true");

    // Press Space again to deselect Tuesday (Monday still selected, so allowed)
    await tuesdayChip.press(" ");
    await expect(tuesdayChip).toHaveAttribute("aria-checked", "false");
  });

  test("SC-D3F-5c: enter key toggles day chip", async ({ page }) => {
    await openPopoverViaNewBlock(page);

    const selectTrigger = page.locator('[data-testid="select-repetir"]');
    await selectTrigger.click();
    await page.getByRole("option", { name: "Personalizado…" }).click();

    // Wednesday chip (index 2 = X)
    const wednesdayChip = page.locator('[data-testid="day-chip-2"]');
    await wednesdayChip.focus();
    await wednesdayChip.press("Enter");
    await expect(wednesdayChip).toHaveAttribute("aria-checked", "true");
  });

  test("SC-D3F-5d: cannot deselect last chip (min 1 day)", async ({ page }) => {
    await openPopoverViaNewBlock(page);

    const selectTrigger = page.locator('[data-testid="select-repetir"]');
    await selectTrigger.click();
    await page.getByRole("option", { name: "Personalizado…" }).click();

    // Monday (index 0) is the only selected chip
    const mondayChip = page.locator('[data-testid="day-chip-0"]');
    await expect(mondayChip).toHaveAttribute("aria-checked", "true");

    // Try to deselect it — should remain selected (min 1 enforcement)
    await mondayChip.click();
    await expect(mondayChip).toHaveAttribute("aria-checked", "true");
  });

  test("SC-D3F-5e: recurrence summary updates as chips are selected", async ({ page }) => {
    await openPopoverViaNewBlock(page);

    const selectTrigger = page.locator('[data-testid="select-repetir"]');
    await selectTrigger.click();
    await page.getByRole("option", { name: "Personalizado…" }).click();

    // Summary should be visible and contain "semana"
    const summary = page.locator('[data-testid="recurrence-summary"]');
    await expect(summary).toBeVisible();
    await expect(summary).toContainText("semana");

    // Set interval to 2
    const intervalInput = page.locator('[data-testid="input-interval"]');
    await intervalInput.fill("2");
    await intervalInput.press("Tab");

    // Summary should update to "2 semanas"
    await expect(summary).toContainText("2 semanas");

    // Select Thursday chip (index 3 = J)
    const thursdayChip = page.locator('[data-testid="day-chip-3"]');
    await thursdayChip.click();
    await expect(thursdayChip).toHaveAttribute("aria-checked", "true");

    // Summary should now mention "lunes" and "jueves"
    await expect(summary).toContainText("lunes");
    await expect(summary).toContainText("jueves");
  });
});
