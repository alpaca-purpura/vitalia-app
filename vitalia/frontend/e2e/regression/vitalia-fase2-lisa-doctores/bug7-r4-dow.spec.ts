// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * bug7-r4-dow.spec.ts — day-of-week paint regression (G round-3 PARCIAL).
 *
 * SYMPTOM (Chris, live dev-app, evening America/Lima): create a WEEKLY MONDAY
 * block → it paints in the SUNDAY column at the right hour. one_off works.
 *
 * ROOT CAUSE (FE paint): getCurrentWeekMonday() did `monday.toISOString()` after
 * a LOCAL setDate → in evening hours under a negative UTC offset (Lima -05) the
 * UTC date is the NEXT day → calendarWeek anchored on TUESDAY, not Monday → the
 * whole grid shifts one day → the real Monday occurrence lands at diff=6 = the
 * "Dom" column. Clamp Math.min(6,diff) masked out-of-window leaks too. The BE is
 * correct (DB slot_date ISODOW matches days_of_week).
 *
 * ROUND-3 ESCAPE: bug7-helpers.ts::mondayOfCurrentWeek() MIRRORED the production
 * bug, so the matrix agreed with broken production → GREEN. Here ground truth is
 * INDEPENDENT: the DB (ISODOW) + rendered column geometry. See bug7-r4-helpers.ts.
 *
 * METHOD: real BE (no mocks), assert (a) DB slot_date ISODOW == selected days,
 * (b) count == end condition, (c) FE paints each occurrence in column ==
 * localWeekdayIndex(occurrenceDate). Cleanup DELETE per case.
 */

import { test, expect } from "../../fixtures/base";
import { gotoHorarios } from "./bug7-helpers";
import {
  apiCreateBlock,
  apiPatchBlock,
  apiDeleteBlockR4,
  dbBlockTruth,
  sweepPaintedOccurrences,
  localWeekdayIndex,
  recurrentPayload,
  oneOffPayload,
  reloadHorarios,
} from "./bug7-r4-helpers";

const SWEEP_WEEKS = 4;
const isodowOf = (days: number[]): number[] => [...new Set(days.map((d) => d + 1))].sort((a, b) => a - b);

/** Core honest assertion: every painted occurrence sits in the column that
 *  matches its own real weekday; the BE stored the selected weekdays. */
async function assertDayOfWeekPaint(
  page: import("@playwright/test").Page,
  blockId: string,
  expectedDays: number[],
): Promise<{ occurrenceDate: string; col: number }[]> {
  const db = dbBlockTruth(blockId);
  expect(db.count, "DB: block must materialize slots").toBeGreaterThan(0);
  expect(db.isodows, "DB: slot ISODOW must equal selected weekdays (BE truth)").toEqual(isodowOf(expectedDays));

  await reloadHorarios(page);
  const painted = await sweepPaintedOccurrences(page, blockId, SWEEP_WEEKS);
  expect(painted.length, "FE: block must paint at least one occurrence in the swept weeks").toBeGreaterThan(0);
  for (const p of painted) {
    expect(
      p.col,
      `FE: occurrence ${p.occurrenceDate} (weekday idx ${localWeekdayIndex(p.occurrenceDate)}) painted in column ${p.col}`,
    ).toBe(localWeekdayIndex(p.occurrenceDate));
  }
  // every selected weekday actually rendered at least once across the sweep
  const observedCols = new Set(painted.map((p) => p.col));
  for (const d of new Set(expectedDays)) {
    expect(observedCols.has(d), `FE: selected weekday col ${d} must render at least once`).toBe(true);
  }
  return painted;
}

// ── Cases 2-15: weekly / biweekly / custom open_ended (data-driven) ───────────

interface MatrixCase {
  n: number;
  name: string;
  days: number[];
  interval?: number;
}

const OPEN_ENDED: MatrixCase[] = [
  { n: 2, name: "weekly lunes [0]", days: [0] },
  { n: 3, name: "weekly martes [1]", days: [1] },
  { n: 4, name: "weekly miércoles [2]", days: [2] },
  { n: 5, name: "weekly jueves [3]", days: [3] },
  { n: 6, name: "weekly viernes [4]", days: [4] },
  { n: 7, name: "weekly sábado [5]", days: [5] },
  { n: 8, name: "weekly DOMINGO real [6]", days: [6] },
  { n: 9, name: "biweekly lunes [0]", days: [0], interval: 2 },
  { n: 10, name: "biweekly domingo [6]", days: [6], interval: 2 },
  { n: 11, name: "daily [0..6]", days: [0, 1, 2, 3, 4, 5, 6] },
  { n: 12, name: "custom L+J [0,3]", days: [0, 3] },
  { n: 13, name: "custom L+J biweekly [0,3]", days: [0, 3], interval: 2 },
  { n: 14, name: "custom fin-de-semana [4,5,6]", days: [4, 5, 6] },
  { n: 15, name: "custom días hábiles [0,1,2,3,4]", days: [0, 1, 2, 3, 4] },
];

test.describe("bug7-r4 day-of-week paint — recurrent open_ended (DB + geometry)", () => {
  for (const c of OPEN_ENDED) {
    test(`case ${c.n}: ${c.name} paints in correct columns`, async ({ page }) => {
      await gotoHorarios(page);
      const { status, blockId } = await apiCreateBlock(
        page,
        recurrentPayload({ days: c.days, interval: c.interval ?? 1 }),
      );
      expect(status, "POST availability-blocks → 201").toBe(201);
      expect(blockId).not.toBe("");
      try {
        await assertDayOfWeekPaint(page, blockId, c.days);
      } finally {
        await apiDeleteBlockR4(page, blockId);
      }
    });
  }
});

// ── Case 1: one_off ───────────────────────────────────────────────────────────

test("case 1: one_off paints exactly its date, only that week", async ({ page }) => {
  await gotoHorarios(page);
  // pick a date in the CURRENT week independent of production date math:
  // next Wednesday from today (deterministic, real date).
  const today = new Date();
  const wed = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  while (wed.getDay() !== 3) wed.setDate(wed.getDate() + 1); // 3 = Wed (local)
  const dateIso = `${wed.getFullYear()}-${String(wed.getMonth() + 1).padStart(2, "0")}-${String(wed.getDate()).padStart(2, "0")}`;
  const { status, blockId } = await apiCreateBlock(page, oneOffPayload(dateIso));
  expect(status).toBe(201);
  try {
    const db = dbBlockTruth(blockId);
    expect(db.count, "one_off → exactly 1 slot").toBe(1);
    expect(db.dates[0]).toBe(dateIso);
    expect(db.isodows).toEqual([localWeekdayIndex(dateIso) + 1]);
    await reloadHorarios(page);
    const painted = await sweepPaintedOccurrences(page, blockId, SWEEP_WEEKS);
    expect(painted.length, "one_off paints once").toBe(1);
    expect(painted[0]!.occurrenceDate).toBe(dateIso);
    expect(painted[0]!.col).toBe(localWeekdayIndex(dateIso));
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

// ── Cases 16-18: end conditions (exact count) ─────────────────────────────────

test("case 16: weekly + end_date — last slot <= end_date, ISODOW=lunes", async ({ page }) => {
  await gotoHorarios(page);
  const today = new Date();
  const end = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  while (end.getDay() !== 1) end.setDate(end.getDate() + 1); // next Monday
  end.setDate(end.getDate() + 21); // a Monday ~3 weeks later
  const endIso = `${end.getFullYear()}-${String(end.getMonth() + 1).padStart(2, "0")}-${String(end.getDate()).padStart(2, "0")}`;
  const { status, blockId } = await apiCreateBlock(
    page,
    recurrentPayload({ days: [0], end: "end_date", endDate: endIso }),
  );
  expect(status).toBe(201);
  try {
    const db = dbBlockTruth(blockId);
    expect(db.isodows).toEqual([1]);
    expect(db.count).toBeGreaterThan(0);
    expect(db.dates[db.dates.length - 1]! <= endIso, "last slot <= end_date (inclusive)").toBe(true);
    await assertDayOfWeekPaint(page, blockId, [0]);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

test("case 17: weekly + occurrences=2 — EXACTLY 2 mondays", async ({ page }) => {
  await gotoHorarios(page);
  const { status, blockId } = await apiCreateBlock(
    page,
    recurrentPayload({ days: [0], end: "occurrences", occurrences: 2 }),
  );
  expect(status).toBe(201);
  try {
    const db = dbBlockTruth(blockId);
    expect(db.count, "occurrences=2 → exactly 2 slots").toBe(2);
    expect(db.isodows).toEqual([1]);
    await assertDayOfWeekPaint(page, blockId, [0]);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

test("case 18: custom L+J biweekly + occurrences=8 — 8 CICLOS completos (16 turnos)", async ({ page }) => {
  // bug7 round-6 (Chris 2026-06-15): "N repeticiones" = N ciclos completos del
  // patrón (cada repetición incluye TODOS los días). 8 repeticiones × [L,J] = 16 turnos.
  await gotoHorarios(page);
  const { status, blockId } = await apiCreateBlock(
    page,
    recurrentPayload({ days: [0, 3], interval: 2, end: "occurrences", occurrences: 8 }),
  );
  expect(status).toBe(201);
  try {
    const db = dbBlockTruth(blockId);
    expect(db.count, "8 repeticiones × 2 días = 16 ocurrencias (ciclos completos)").toBe(16);
    expect(db.isodows).toEqual([1, 4]);
    // cada día aparece exactamente 8 veces (8 ciclos)
    const mon = db.dates.filter((d) => localWeekdayIndex(d) === 0).length;
    const thu = db.dates.filter((d) => localWeekdayIndex(d) === 3).length;
    expect(mon, "8 lunes").toBe(8);
    expect(thu, "8 jueves").toBe(8);
    await assertDayOfWeekPaint(page, blockId, [0, 3]);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

// ── Cases 20-22: edits re-project + re-paint ──────────────────────────────────

test("case 20: edit recurrent days [0]→[2] re-projects + re-paints", async ({ page }) => {
  await gotoHorarios(page);
  const created = await apiCreateBlock(page, recurrentPayload({ days: [0] }));
  expect(created.status).toBe(201);
  const blockId = created.blockId;
  try {
    expect(dbBlockTruth(blockId).isodows).toEqual([1]);
    const patch = await apiPatchBlock(page, blockId, recurrentPayload({ days: [2] }));
    expect(patch.status, "PATCH → 200").toBe(200);
    const db = dbBlockTruth(blockId);
    expect(db.isodows, "future slots re-projected to miércoles").toEqual([3]);
    await assertDayOfWeekPaint(page, blockId, [2]);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

test("case 21: edit interval 1→2 — still lunes, parity changes", async ({ page }) => {
  await gotoHorarios(page);
  const created = await apiCreateBlock(page, recurrentPayload({ days: [0], interval: 1 }));
  expect(created.status).toBe(201);
  const blockId = created.blockId;
  try {
    const before = dbBlockTruth(blockId);
    const patch = await apiPatchBlock(page, blockId, recurrentPayload({ days: [0], interval: 2 }));
    expect(patch.status).toBe(200);
    const after = dbBlockTruth(blockId);
    expect(after.isodows, "still lunes after interval change").toEqual([1]);
    expect(after.count, "biweekly → fewer slots than weekly").toBeLessThan(before.count);
    await assertDayOfWeekPaint(page, blockId, [0]);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

test("case 22: edit one_off date moves the slot", async ({ page }) => {
  await gotoHorarios(page);
  const today = new Date();
  const a = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  while (a.getDay() !== 2) a.setDate(a.getDate() + 1); // Tue
  const b = new Date(a);
  b.setDate(b.getDate() + 2); // Thu
  const iso = (x: Date) => `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, "0")}-${String(x.getDate()).padStart(2, "0")}`;
  const created = await apiCreateBlock(page, oneOffPayload(iso(a)));
  expect(created.status).toBe(201);
  const blockId = created.blockId;
  try {
    expect(dbBlockTruth(blockId).dates).toEqual([iso(a)]);
    const patch = await apiPatchBlock(page, blockId, oneOffPayload(iso(b)));
    expect(patch.status).toBe(200);
    const db = dbBlockTruth(blockId);
    expect(db.dates, "slot moved to new date").toEqual([iso(b)]);
    await reloadHorarios(page);
    const painted = await sweepPaintedOccurrences(page, blockId, SWEEP_WEEKS);
    expect(painted.length).toBe(1);
    expect(painted[0]!.occurrenceDate).toBe(iso(b));
    expect(painted[0]!.col).toBe(localWeekdayIndex(iso(b)));
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

// ── Cases 2/8/19: REAL UI create path (click + chips + save) ──────────────────

/** Switch popover to weekly-custom + select exactly the given day chips. */
async function selectWeeklyChips(page: import("@playwright/test").Page, days: number[]): Promise<void> {
  await page.getByTestId("select-repetir").click();
  await page.getByRole("option", { name: /[Pp]ersonalizado/ }).click();
  await page.getByTestId("custom-recurrence-editor").waitFor({ state: "visible" });
  // Ensure exactly `days` are selected. DayChip is role="checkbox" with
  // aria-checked (NOT aria-pressed). The popover pre-selects the anchor day and
  // the form forbids ZERO days — so ADD wanted days FIRST, then REMOVE unwanted
  // (never drop to zero, which would block deselecting the anchor).
  const isChecked = async (d: number) =>
    (await page.getByTestId(`day-chip-${d}`).getAttribute("aria-checked")) === "true";
  for (const d of days) {
    if (!(await isChecked(d))) await page.getByTestId(`day-chip-${d}`).click();
  }
  for (let d = 0; d < 7; d++) {
    if (!days.includes(d) && (await isChecked(d))) await page.getByTestId(`day-chip-${d}`).click();
  }
}

test("case 2-UI: real click → weekly lunes saves + paints in Lun (not Dom)", async ({ page }) => {
  await gotoHorarios(page);
  // click any empty cell to open the popover (GCal click = 1h draft)
  await page.getByTestId("cell-2-9").click();
  await page.getByTestId("bloque-popover").waitFor({ state: "visible" });
  await selectWeeklyChips(page, [0]);
  const respPromise = page.waitForResponse(
    (r) => r.url().includes("availability-blocks") && r.request().method() === "POST",
  );
  await page.getByTestId("btn-save-block").click();
  const resp = await respPromise;
  expect(resp.status()).toBe(201);
  const blockId = String(((await resp.json()) as { id?: string }).id ?? "");
  try {
    await assertDayOfWeekPaint(page, blockId, [0]);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

test("case 19-UI: anchor (drag Lun) ≠ selection (Mié) → paints Mié, not Lun", async ({ page }) => {
  await gotoHorarios(page);
  await page.getByTestId("cell-0-9").click(); // anchor on Monday column
  await page.getByTestId("bloque-popover").waitFor({ state: "visible" });
  await selectWeeklyChips(page, [2]); // select Wednesday only
  const respPromise = page.waitForResponse(
    (r) => r.url().includes("availability-blocks") && r.request().method() === "POST",
  );
  await page.getByTestId("btn-save-block").click();
  const resp = await respPromise;
  expect(resp.status()).toBe(201);
  const blockId = String(((await resp.json()) as { id?: string }).id ?? "");
  try {
    expect(dbBlockTruth(blockId).isodows, "BE stores Wednesday, not the dragged Monday").toEqual([3]);
    await assertDayOfWeekPaint(page, blockId, [2]);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});
