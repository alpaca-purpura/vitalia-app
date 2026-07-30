// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * bug7-r5-dow.spec.ts — round-5 follow-ups, real-backend + DB ground truth.
 *
 * #1 borrar bloque recurrente: "Solo este turno" (scope=occurrence) vs
 *    "Este y los siguientes" (scope=this_and_future). API + UI dialog.
 * #2 no crear bloques en el pasado (BE 422 + FE celda deshabilitada).
 * #3 regresión: bloque multi-día (L+X+V) pinta los 3 días en la MISMA semana
 *    (cierra el hueco del sweep de round-4: el matrix unía semanas y podía pasar
 *    aunque no todos los días aparecieran en una sola).
 *
 * Ground truth INDEPENDIENTE: DB (slot ISODOW / excluded_dates / end_date) +
 * geometría DOM. Cero mocks del surface. Cleanup por caso.
 */

import { test, expect } from "../../fixtures/base";
import { gotoHorarios } from "./bug7-helpers";
import {
  apiCreateBlock,
  apiDeleteBlockR4,
  apiDeleteScoped,
  dbBlockTruth,
  dbBlockMeta,
  paintedColumnsOf,
  sweepPaintedOccurrences,
  recurrentPayload,
  oneOffPayload,
  reloadHorarios,
  navNextWeek,
  navPrevWeek,
  localWeekdayIndex,
} from "./bug7-r4-helpers";

const SWEEP = 5;

// ── #3 regression: multi-day paints all days in the SAME visible week ─────────

test("#3 multi-día [L,X,V] pinta los 3 días en una MISMA semana", async ({ page }) => {
  await gotoHorarios(page);
  const { status, blockId } = await apiCreateBlock(page, recurrentPayload({ days: [0, 2, 4] }));
  expect(status).toBe(201);
  try {
    expect(dbBlockTruth(blockId).isodows).toEqual([1, 3, 5]);
    await reloadHorarios(page);
    // find a week where this block has occurrences, assert ALL of {0,2,4} appear together
    let foundWeekWithAll = false;
    for (let w = 0; w < SWEEP; w++) {
      const painted = await paintedColumnsOf(page, blockId);
      for (const p of painted) expect(p.col).toBe(localWeekdayIndex(p.occurrenceDate));
      const cols = new Set(painted.map((p) => p.col));
      if (cols.has(0) && cols.has(2) && cols.has(4)) foundWeekWithAll = true;
      if (w < SWEEP - 1) await navNextWeek(page);
    }
    expect(foundWeekWithAll, "una semana debe mostrar Lun+Mié+Vie juntos").toBe(true);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

// ── round-6: "N repeticiones" = N ciclos COMPLETOS del patrón ─────────────────

test("#R6 occurrences = ciclos completos: Mar+Jue ×3 = 6 turnos (3 Mar + 3 Jue)", async ({ page }) => {
  // Chris 2026-06-15 (dev-app): "Mar y Jue, 3 veces" → solo pintaba semana 1 completa
  // y la 2 a medias. Ratificó que N repeticiones = N semanas completas (cada una
  // con TODOS los días). 3 repeticiones × [Mar,Jue] = 6 turnos.
  await gotoHorarios(page);
  const { status, blockId } = await apiCreateBlock(
    page,
    recurrentPayload({ days: [1, 3], end: "occurrences", occurrences: 3, start: "14:00:00", end_t: "17:00:00" }),
  );
  expect(status).toBe(201);
  try {
    const db = dbBlockTruth(blockId);
    expect(db.count, "3 repeticiones × 2 días = 6 ocurrencias").toBe(6);
    expect(db.isodows, "martes(2) + jueves(4)").toEqual([2, 4]);
    const tue = db.dates.filter((d) => localWeekdayIndex(d) === 1).length; // Mar = idx 1
    const thu = db.dates.filter((d) => localWeekdayIndex(d) === 3).length; // Jue = idx 3
    expect(tue, "3 martes").toBe(3);
    expect(thu, "3 jueves").toBe(3);
    // FE: cada ocurrencia pintada en su columna real; ambos días aparecen
    await reloadHorarios(page);
    const painted = await sweepPaintedOccurrences(page, blockId, SWEEP);
    for (const p of painted) expect(p.col).toBe(localWeekdayIndex(p.occurrenceDate));
    const cols = new Set(painted.map((p) => p.col));
    expect(cols.has(1) && cols.has(3), "Mar y Jue pintan").toBe(true);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

// ── #1a "Solo este turno" (scope=occurrence) via API ──────────────────────────

test("#1a scope=occurrence excluye SOLO esa fecha; el resto de la serie sigue", async ({ page }) => {
  await gotoHorarios(page);
  const { blockId } = await apiCreateBlock(page, recurrentPayload({ days: [0] }));
  try {
    const before = dbBlockTruth(blockId);
    const target = before.dates[1]!; // 2da ocurrencia (lunes futuro real)
    const res = await apiDeleteScoped(page, blockId, "occurrence", target);
    expect(res.status, "DELETE scope=occurrence → 200").toBe(200);
    expect(res.json["scope"]).toBe("occurrence");
    const meta = dbBlockMeta(blockId);
    expect(meta.deleted, "bloque sigue activo").toBe(false);
    expect(meta.excludedDates, "excluded_dates incluye la fecha").toContain(target);
    const after = dbBlockTruth(blockId);
    expect(after.dates, "fecha excluida ya no tiene slots").not.toContain(target);
    expect(after.dates.length, "resto de la serie intacto").toBeGreaterThan(0);
    // FE: la fecha excluida NO pinta; otras sí
    await reloadHorarios(page);
    const painted = await sweepPaintedOccurrences(page, blockId, SWEEP);
    const dates = painted.map((p) => p.occurrenceDate);
    expect(dates, "FE no pinta la ocurrencia excluida").not.toContain(target);
    for (const p of painted) expect(p.col).toBe(localWeekdayIndex(p.occurrenceDate));
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

// ── #1b "Este y los siguientes" (scope=this_and_future) via API ───────────────

test("#1b scope=this_and_future trunca desde la fecha; pasado intacto", async ({ page }) => {
  await gotoHorarios(page);
  const { blockId } = await apiCreateBlock(page, recurrentPayload({ days: [0] }));
  try {
    const before = dbBlockTruth(blockId);
    const cut = before.dates[2]!; // 3ra ocurrencia
    const res = await apiDeleteScoped(page, blockId, "this_and_future", cut);
    expect(res.status).toBe(200);
    expect(res.json["scope"]).toBe("this_and_future");
    const meta = dbBlockMeta(blockId);
    expect(meta.deleted).toBe(false);
    expect(meta.endDate, "end_date = fecha de corte − 1 día").not.toBeNull();
    expect(meta.endDate! < cut, "end_date anterior al corte").toBe(true);
    const after = dbBlockTruth(blockId);
    expect(after.dates.every((d) => d < cut), "no quedan slots >= corte").toBe(true);
    expect(after.dates.length, "ocurrencias previas al corte intactas").toBeGreaterThan(0);
    await reloadHorarios(page);
    const painted = await sweepPaintedOccurrences(page, blockId, SWEEP);
    expect(painted.every((p) => p.occurrenceDate < cut), "FE no pinta >= corte").toBe(true);
    for (const p of painted) expect(p.col).toBe(localWeekdayIndex(p.occurrenceDate));
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

// ── #1c UI: recurrente muestra diálogo de scope; one_off NO ───────────────────

test("#1c UI: borrar recurrente abre diálogo 'solo este / este y los siguientes'", async ({ page }) => {
  await gotoHorarios(page);
  // Miércoles (col 2): los bloques manuales de Chris son Lun/Mar/Jue → sin solape
  // → el click aterriza en NUESTRO bloque (no en uno superpuesto por z-order).
  const { blockId } = await apiCreateBlock(page, recurrentPayload({ days: [2], start: "16:00:00", end_t: "17:00:00" }));
  try {
    await reloadHorarios(page);
    // navigate to a week where the block paints, then open it
    let painted = await paintedColumnsOf(page, blockId);
    for (let w = 0; w < SWEEP && painted.length === 0; w++) {
      await navNextWeek(page);
      painted = await paintedColumnsOf(page, blockId);
    }
    expect(painted.length, "el bloque debe pintar en alguna semana").toBeGreaterThan(0);
    await page.locator(`[data-testid="block-${blockId}"]`).first().click();
    await page.getByTestId("bloque-popover").waitFor({ state: "visible" });
    await page.getByTestId("btn-delete-block").click();
    await page.getByTestId("dialog-delete-scope").waitFor({ state: "visible" });
    await expect(page.getByTestId("btn-delete-occurrence")).toBeVisible();
    await expect(page.getByTestId("btn-delete-this-and-future")).toBeVisible();
    // ejecutar "Solo este turno" → DELETE scope=occurrence real
    const respPromise = page.waitForResponse(
      (r) => r.url().includes("availability-blocks") && r.request().method() === "DELETE",
    );
    await page.getByTestId("btn-delete-occurrence").click();
    const resp = await respPromise;
    expect(resp.status()).toBe(200);
    expect(resp.url()).toContain("scope=occurrence");
    expect(resp.url()).toContain("occurrence_date=");
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

test("#1c UI: borrar one_off NO abre diálogo de scope", async ({ page }) => {
  await gotoHorarios(page);
  // one_off en una fecha FUTURA (no past — #2)
  const today = new Date();
  const fut = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 3);
  const iso = `${fut.getFullYear()}-${String(fut.getMonth() + 1).padStart(2, "0")}-${String(fut.getDate()).padStart(2, "0")}`;
  const { blockId } = await apiCreateBlock(page, oneOffPayload(iso, "16:00:00", "17:00:00"));
  try {
    await reloadHorarios(page);
    let painted = await paintedColumnsOf(page, blockId);
    for (let w = 0; w < SWEEP && painted.length === 0; w++) {
      await navNextWeek(page);
      painted = await paintedColumnsOf(page, blockId);
    }
    expect(painted.length).toBeGreaterThan(0);
    await page.locator(`[data-testid="block-${blockId}"]`).first().click();
    await page.getByTestId("bloque-popover").waitFor({ state: "visible" });
    await page.getByTestId("btn-delete-block").click();
    // one_off → NO scope dialog (warning de confirmación directa)
    await expect(page.getByTestId("dialog-delete-scope")).toHaveCount(0);
  } finally {
    await apiDeleteBlockR4(page, blockId);
  }
});

// ── #2 no crear en el pasado ──────────────────────────────────────────────────

// #2 BE (one_off past → 422) is covered by the builder's pytest
// (tests/modules/vitalia/clinics — create_block past one_off → ValueError → 422).
// An e2e here would deliberately provoke a 422, which the base.ts anti-bubble
// fixture (correctly) flags as a runtime error — so BE-422 lives in pytest.

test("#2 FE: celda pasada deshabilitada (no abre popover); futura sí", async ({ page }) => {
  await gotoHorarios(page);
  // Date-robust (no depende de la hora del día): SEMANA ANTERIOR = todo pasado;
  // +2 semanas = todo futuro. Columna miércoles (col 2): sin bloques de Chris encima.
  await navPrevWeek(page);
  const pastCell = page.getByTestId("cell-2-9");
  await expect(pastCell, "celda de semana anterior = pasada (data-past)").toHaveAttribute("data-past", "true");
  await pastCell.click({ force: true });
  await expect(page.getByTestId("bloque-popover"), "no abre popover en el pasado").toHaveCount(0);
  // volver a la semana actual y avanzar 2 → futuro garantizado a cualquier hora
  await navNextWeek(page);
  await navNextWeek(page);
  await navNextWeek(page);
  const futureCell = page.getByTestId("cell-2-16");
  await expect(futureCell, "celda 2 semanas adelante = futura").not.toHaveAttribute("data-past", "true");
  await futureCell.click();
  await expect(page.getByTestId("bloque-popover")).toBeVisible();
});
