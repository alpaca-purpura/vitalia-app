// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * bug7-r3-d3-matrix.spec.ts — D-3: matriz COMPLETA de escenarios de guardado
 * (clon Google Calendar) contra backend REAL (FE:3002 + BE:8002, cero mocks
 * del surface availability-blocks/occurrences).
 *
 * Matriz WORK-ORDER-bug7-round3.md § D-3 (casos 1–14; #15 vive en
 * bug7-r3-d1-save-button.spec.ts):
 *   1  click simple → "No se repite" → POST one_off 201 + SOLO esa fecha
 *   2  drag 9-12 → "No se repite" → one_off rango exacto
 *   3  weekly open_ended → semana actual + siguiente
 *   4  "Todos los días" → 7 días pintados
 *   5  "Cada 2 semanas" → semana siguiente vacía, subsiguiente pintada
 *   6  custom chips L+J interval=2 occurrences=8 → payload + resumen + corte a 8
 *   7  end_date inclusivo
 *   8  occurrences=2 exacto (regresión D3-C)
 *   9  editar recurrente (PATCH) + 9b editar one_off (PATCH — hoy no-op FE)
 *   10 eliminar → desaparece
 *   11 validación Zod → toast "Revisa los campos" + NO POST
 *   12 error server real (end<start → 422) → toast error + popover abierto
 *   13 toast success en creates (asertado en 1/2/3)
 *   14 vista mes refleja lo creado
 *
 * Cleanup: cada test borra los bloques que creó vía DELETE real (apiDeleteBlock).
 */

import { test, expect } from "../../fixtures/authed-runtime";
import {
  gotoHorarios,
  clickCell,
  dragCreate,
  chooseRepetir,
  chooseTermina,
  saveAndWaitPost,
  saveAndWaitPatch,
  expectToast,
  apiDeleteBlock,
  dateOfDayThisWeek,
  addDaysIso,
  BLOCKS_PATH,
} from "./bug7-helpers";
import { dbBlockTruth, localWeekdayIndex } from "./bug7-r4-helpers";

const SAT = 5; // sábado — libre de bloques pre-existentes del doctor demo

let createdIds: string[] = [];

test.beforeEach(() => {
  createdIds = [];
});

test.afterEach(async ({ page }) => {
  for (const id of createdIds) {
    const status = await apiDeleteBlock(page, id);
    if (status !== 200) {
      console.warn(`[bug7-cleanup] DELETE ${id} → ${status}`);
    }
  }
});

function blockOnPage(page: import("@playwright/test").Page, id: string) {
  return page.getByTestId(`block-${id}`);
}

// ── Caso 1 + 13: click simple → "No se repite" → one_off SOLO esa fecha ──────

test("caso 1 — click simple → 'No se repite' → POST one_off 201, visible SOLO esa fecha", async ({
  page,
}) => {
  await gotoHorarios(page);
  await clickCell(page, SAT, 9);

  await chooseRepetir(page, /No se repite/);
  const { status, body, requestJson } = await saveAndWaitPost(page);

  expect(status, "POST one_off debe dar 201 (★ nunca visto en logs)").toBe(201);
  expect(requestJson["kind"]).toBe("one_off");
  expect(requestJson["specific_date"]).toBe(dateOfDayThisWeek(SAT));
  expect(requestJson["start_time"]).toBe("09:00");
  expect(requestJson["end_time"]).toBe("10:00");

  const id = String(body["id"]);
  createdIds.push(id);

  // Caso 13: toast success
  await expectToast(page, /Bloque guardado/);

  // El calendario REFRESCA sin reload: bloque visible en sábado
  await expect(
    blockOnPage(page, id),
    "tras crear, el bloque debe aparecer SIN recargar (invalidación occurrences)",
  ).toBeVisible({ timeout: 10_000 });

  // No aparece otra semana
  await page.getByTestId("week-nav-next").click();
  await expect(blockOnPage(page, id)).toHaveCount(0);
});

// ── Caso 2: drag 9-12 → "No se repite" → rango exacto ────────────────────────

test("caso 2 — drag 09→12 → 'No se repite' → one_off rango exacto 09:00-12:00", async ({
  page,
}) => {
  await gotoHorarios(page);
  await dragCreate(page, SAT, 9, 11); // celdas 9,10,11 → 09:00–12:00

  await chooseRepetir(page, /No se repite/);
  const { status, body, requestJson } = await saveAndWaitPost(page);

  expect(status).toBe(201);
  expect(requestJson["kind"]).toBe("one_off");
  expect(requestJson["start_time"]).toBe("09:00");
  expect(requestJson["end_time"]).toBe("12:00");
  expect(requestJson["specific_date"]).toBe(dateOfDayThisWeek(SAT));

  const id = String(body["id"]);
  createdIds.push(id);
  await expectToast(page, /Bloque guardado/);
  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });
});

// ── Caso 3: weekly open_ended → semana actual + siguiente ────────────────────

test("caso 3 — 'Cada semana el sábado' open_ended → interval=1, visible esta semana y la siguiente", async ({
  page,
}) => {
  await gotoHorarios(page);
  await clickCell(page, SAT, 10);

  // default del draft ya es weekly open_ended — aserto el payload igual
  const { status, body, requestJson } = await saveAndWaitPost(page);

  expect(status).toBe(201);
  expect(requestJson["kind"]).toBe("recurrent");
  expect(requestJson["days_of_week"]).toEqual([SAT]);
  expect(requestJson["interval"]).toBe(1);
  expect(requestJson["end_condition_kind"]).toBe("open_ended");

  const id = String(body["id"]);
  createdIds.push(id);
  await expectToast(page, /Bloque guardado/);

  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });

  await page.getByTestId("week-nav-next").click();
  await expect(
    blockOnPage(page, id),
    "weekly open_ended debe pintar también la semana siguiente",
  ).toBeVisible({ timeout: 10_000 });
});

// ── Caso 4: "Todos los días" → 7 días ────────────────────────────────────────

test("caso 4 — 'Todos los días' → days_of_week 7 elementos, semana siguiente pinta L-D", async ({
  page,
}) => {
  await gotoHorarios(page);
  await clickCell(page, SAT, 15);

  await chooseRepetir(page, /Todos los días/);
  const { status, body, requestJson } = await saveAndWaitPost(page);

  expect(status).toBe(201);
  expect(requestJson["days_of_week"]).toEqual([0, 1, 2, 3, 4, 5, 6]);

  const id = String(body["id"]);
  createdIds.push(id);

  // Semana siguiente (completa, sin anclaje a la fecha de creación): 7 columnas pintadas
  await page.getByTestId("week-nav-next").click();
  await expect(blockOnPage(page, id)).toHaveCount(7, { timeout: 10_000 });
});

// ── Caso 5: "Cada 2 semanas" → semana siguiente VACÍA, subsiguiente pintada ──

test("caso 5 — 'Cada 2 semanas el sábado' → interval=2, semana+1 vacía, semana+2 pintada", async ({
  page,
}) => {
  await gotoHorarios(page);
  await clickCell(page, SAT, 11);

  await chooseRepetir(page, /Cada 2 semanas/);
  const { status, body, requestJson } = await saveAndWaitPost(page);

  expect(status).toBe(201);
  expect(requestJson["interval"]).toBe(2);
  expect(requestJson["days_of_week"]).toEqual([SAT]);

  const id = String(body["id"]);
  createdIds.push(id);

  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });

  await page.getByTestId("week-nav-next").click();
  await expect(
    blockOnPage(page, id),
    "biweekly: semana siguiente debe estar VACÍA",
  ).toHaveCount(0);

  await page.getByTestId("week-nav-next").click();
  await expect(
    blockOnPage(page, id),
    "biweekly: semana subsiguiente debe estar pintada",
  ).toBeVisible({ timeout: 10_000 });
});

// ── Caso 6: Personalizado chips L+J interval=2 occurrences=8 ─────────────────

test("caso 6 — Personalizado L+J cada 2 semanas, termina tras 8 → payload + resumen + proyección corta a 8", async ({
  page,
}) => {
  await gotoHorarios(page);
  await clickCell(page, SAT, 12);

  await chooseRepetir(page, /Personalizado/);
  await expect(page.getByTestId("custom-recurrence-editor")).toBeVisible();

  // interval = 2
  await page.getByTestId("input-interval").fill("2");

  // chips: + L (0), + J (3), − S (5 — el ancla del click)
  await page.getByTestId("day-chip-0").click();
  await page.getByTestId("day-chip-3").click();
  await page.getByTestId("day-chip-5").click();

  // Termina: después de 8 repeticiones
  await chooseTermina(page, "custom", /Después de N repeticiones/);
  await page.getByTestId("input-occurrences").fill("8");

  // Resumen humano exacto (RN-D3F-1)
  await expect(page.getByTestId("recurrence-summary")).toHaveText(
    "Se repite cada 2 semanas los lunes y jueves, 8 repeticiones",
  );

  const { status, body, requestJson } = await saveAndWaitPost(page);
  expect(status).toBe(201);
  expect(requestJson["days_of_week"]).toEqual([0, 3]);
  expect(requestJson["interval"]).toBe(2);
  expect(requestJson["end_condition_kind"]).toBe("occurrences");
  expect(requestJson["occurrences"]).toBe(8);

  const id = String(body["id"]);
  createdIds.push(id);

  // bug7 round-6 (Chris 2026-06-15): "8 repeticiones" = 8 CICLOS completos del
  // patrón [L,J] → 16 ocurrencias (8 lunes + 8 jueves). Ground truth = DB
  // (la ventana de occurrences está capada a 62d y no captura 16 quincenales).
  const db = dbBlockTruth(id);
  expect(db.count, "8 repeticiones × 2 días = 16 ocurrencias materializadas").toBe(16);
  expect(db.dates.filter((d) => localWeekdayIndex(d) === 0).length, "8 lunes").toBe(8);
  expect(db.dates.filter((d) => localWeekdayIndex(d) === 3).length, "8 jueves").toBe(8);
});

// ── Caso 7: termina en fecha (end_date inclusivo) ────────────────────────────

test("caso 7 — weekly con end_date = sábado próximo → último día PINTA (inclusivo), semana+2 no", async ({
  page,
}) => {
  await gotoHorarios(page);
  await clickCell(page, SAT, 13);

  const nextSat = addDaysIso(dateOfDayThisWeek(SAT), 7);
  await chooseTermina(page, "simple", /El \(fecha\)/);
  await page.locator("#endDateSimple").fill(nextSat);

  const { status, body, requestJson } = await saveAndWaitPost(page);
  expect(status).toBe(201);
  expect(requestJson["end_condition_kind"]).toBe("end_date");
  expect(requestJson["end_date"]).toBe(nextSat);

  const id = String(body["id"]);
  createdIds.push(id);

  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });

  await page.getByTestId("week-nav-next").click();
  await expect(
    blockOnPage(page, id),
    "end_date inclusivo: el último sábado DEBE pintar",
  ).toBeVisible({ timeout: 10_000 });

  await page.getByTestId("week-nav-next").click();
  await expect(blockOnPage(page, id)).toHaveCount(0);
});

// ── Caso 8: occurrences=2 EXACTO (regresión D3-C) ────────────────────────────

test("caso 8 — weekly occurrences=2 → exactamente 2 semanas pintadas, tercera vacía", async ({
  page,
}) => {
  await gotoHorarios(page);
  await clickCell(page, SAT, 14);

  await chooseTermina(page, "simple", /Después de N repeticiones/);
  await page.getByTestId("input-occurrences-simple").fill("2");

  const { status, body, requestJson } = await saveAndWaitPost(page);
  expect(status).toBe(201);
  expect(requestJson["occurrences"]).toBe(2);

  const id = String(body["id"]);
  createdIds.push(id);

  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });

  await page.getByTestId("week-nav-next").click();
  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });

  await page.getByTestId("week-nav-next").click();
  await expect(
    blockOnPage(page, id),
    "regresión D3-C: la tercera semana debe estar VACÍA con occurrences=2",
  ).toHaveCount(0);
});

// ── Caso 9: editar bloque recurrente (PATCH) ─────────────────────────────────

test("caso 9 — editar recurrente: cambiar hora → PATCH 200 + calendario actualiza", async ({
  page,
}) => {
  await gotoHorarios(page);

  // Seed por UI: weekly sábado 14:00-15:00
  await clickCell(page, SAT, 14);
  const created = await saveAndWaitPost(page);
  expect(created.status).toBe(201);
  const id = String(created.body["id"]);
  createdIds.push(id);
  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });

  // Editar: click en el bloque → popover en modo edición
  await blockOnPage(page, id).first().click();
  await expect(page.getByTestId("bloque-popover")).toBeVisible();
  await expect(page.getByTestId("btn-save-block")).toHaveText("Actualizar");

  await page.locator("#endTime").fill("16:00");
  const patched = await saveAndWaitPatch(page);
  expect(patched.status, "PATCH del bloque debe dar 200").toBe(200);

  // Calendario refresca con la hora nueva
  await expect(
    blockOnPage(page, id).first(),
    "tras editar, el bloque debe mostrar el rango nuevo sin recargar",
  ).toContainText("14:00–16:00", { timeout: 10_000 });
});

test("caso 9b — editar one_off: cambiar hora → PATCH 200 (hoy: no-op silencioso FE)", async ({
  page,
}) => {
  await gotoHorarios(page);

  // Seed one_off sábado 17:00-18:00
  await clickCell(page, SAT, 17);
  await chooseRepetir(page, /No se repite/);
  const created = await saveAndWaitPost(page);
  expect(created.status).toBe(201);
  const id = String(created.body["id"]);
  createdIds.push(id);
  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });

  // Editar hora fin → DEBE disparar PATCH real (BE lo soporta)
  await blockOnPage(page, id).first().click();
  await expect(page.getByTestId("bloque-popover")).toBeVisible();
  await page.locator("#endTime").fill("19:00");

  const patched = await saveAndWaitPatch(page);
  expect(
    patched.status,
    "editar un bloque one_off debe PATCHear (no no-op con toast de éxito mentiroso)",
  ).toBe(200);

  await expect(blockOnPage(page, id).first()).toContainText("17:00–19:00", {
    timeout: 10_000,
  });
});

// ── Caso 10: eliminar bloque ─────────────────────────────────────────────────

test("caso 10 — eliminar bloque → DELETE 200 + desaparece del calendario", async ({
  page,
}) => {
  await gotoHorarios(page);

  await clickCell(page, SAT, 18);
  const created = await saveAndWaitPost(page);
  expect(created.status).toBe(201);
  const id = String(created.body["id"]);
  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });

  await blockOnPage(page, id).first().click();
  await expect(page.getByTestId("bloque-popover")).toBeVisible();
  await page.getByTestId("btn-delete-block").click();

  // Dialog de confirmación
  const deleteResp = page.waitForResponse(
    (r) => r.url().includes(BLOCKS_PATH) && r.request().method() === "DELETE",
    { timeout: 10_000 },
  );
  await page.getByRole("button", { name: "Sí, eliminar" }).click();
  const resp = await deleteResp;
  expect(resp.status()).toBe(200);

  await expect(
    blockOnPage(page, id),
    "tras eliminar, el bloque debe desaparecer SIN recargar",
  ).toHaveCount(0, { timeout: 10_000 });
});

// ── Caso 11: validación Zod → toast + NO POST ────────────────────────────────

test("caso 11 — occurrences vacío → toast 'Revisa los campos del bloque' y NO se postea", async ({
  page,
}) => {
  await gotoHorarios(page);
  await clickCell(page, SAT, 19);

  await chooseTermina(page, "simple", /Después de N repeticiones/);
  // input-occurrences-simple queda VACÍO a propósito

  let posted = false;
  page.on("request", (req) => {
    if (req.url().includes(BLOCKS_PATH) && req.method() === "POST") {
      posted = true;
    }
  });

  await page.getByTestId("btn-save-block").click();
  await expectToast(page, /Revisa los campos del bloque/);
  await page.waitForTimeout(1_000);

  expect(posted, "con Zod inválido NO debe dispararse POST").toBe(false);
  await expect(
    page.getByTestId("bloque-popover"),
    "el popover queda abierto para corregir",
  ).toBeVisible();
});

// ── Caso 12: error server REAL (422) → toast error + popover abierto ─────────

test.describe("caso 12 — error de server real", () => {
  // El 422 del BE es PROVOCADO por el test → opt-out del gate anti-burbuja
  test.use({ failOnRuntimeError: false });

  test("end_time < start_time pasa Zod pero el BE responde 422 → toast error + popover abierto", async ({
    page,
  }) => {
    await gotoHorarios(page);
    await clickCell(page, SAT, 10);

    // Zod solo valida formato HH:mm — el invariante start<end vive en el BE
    await page.locator("#startTime").fill("12:00");
    await page.locator("#endTime").fill("09:00");

    const respPromise = page.waitForResponse(
      (r) => r.url().includes(BLOCKS_PATH) && r.request().method() === "POST",
      { timeout: 10_000 },
    );
    await page.getByTestId("btn-save-block").click();
    const resp = await respPromise;

    expect(resp.status(), "el BE debe rechazar end<=start con 422").toBe(422);
    await expectToast(page, /No pudimos guardar el bloque/);
    await expect(
      page.getByTestId("bloque-popover"),
      "tras error de server el popover queda abierto",
    ).toBeVisible();
  });
});

// ── Caso 14: vista mes refleja lo creado ─────────────────────────────────────

test("caso 14 — bloque creado visible en vista MES (MonthCalendar)", async ({
  page,
}) => {
  await gotoHorarios(page);

  await clickCell(page, SAT, 8);
  const created = await saveAndWaitPost(page);
  expect(created.status).toBe(201);
  const id = String(created.body["id"]);
  createdIds.push(id);
  await expect(blockOnPage(page, id)).toBeVisible({ timeout: 10_000 });

  // Cambiar a vista mes
  await page.getByTestId("toggle-mes").click();
  await expect(page.getByTestId("month-calendar")).toBeVisible({
    timeout: 10_000,
  });

  const satIso = dateOfDayThisWeek(SAT);
  await expect(
    page.getByTestId(`month-chip-${satIso}-${id}`),
    "la vista mes debe mostrar el chip del bloque recién creado",
  ).toBeVisible({ timeout: 10_000 });
});
