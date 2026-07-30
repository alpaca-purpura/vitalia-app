// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * bug7-r4-helpers.ts — round-4 helpers for the day-of-week paint regression.
 *
 * ROUND-3 ESCAPE LESSON: bug7-helpers.ts::mondayOfCurrentWeek() REPLICATED the
 * production getCurrentWeekMonday() bug (toISOString after a local setDate) →
 * the test ground truth was a MIRROR of the production bug → matrix went GREEN
 * while the calendar painted Monday in the Sunday column.
 *
 * Round 4 uses INDEPENDENT ground truth ONLY:
 *   - the DATABASE (vitalia_availability_slots ISODOW) — what the BE actually stored
 *   - the RENDERED column geometry — where the FE actually painted
 *   - localWeekdayIndex() computed from the occurrence date with a pure,
 *     TZ-stable calculation (NO toISOString anywhere)
 *
 * NO route mocks for availability-blocks / availability-occurrences (real BE:8002).
 */

import { execSync } from "node:child_process";
import type { Page } from "@playwright/test";
import { TENANT_ID, BLOCKS_PATH } from "./bug7-helpers";

const PG_CONTAINER = process.env["E2E_PG_CONTAINER"] ?? "luana-dev-luana_postgres_dev-1";
const PG_DB = process.env["E2E_PG_DB"] ?? "vitalia_dev";

// ── Independent date math (TZ-stable; NO toISOString — never mirror production) ──

/** Day index 0=Mon..6=Sun for a YYYY-MM-DD date, computed locally (no UTC drift). */
export function localWeekdayIndex(iso: string): number {
  const [y, m, d] = iso.split("-").map(Number);
  const dow = new Date(y!, m! - 1, d!).getDay(); // 0=Sun..6=Sat
  return dow === 0 ? 6 : dow - 1;
}

export const DAY_LABELS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

// ── In-page authenticated writes (real Clerk session, real BE) ───────────────

interface ClerkWin {
  Clerk?: {
    session?: { getToken: () => Promise<string | null> };
    user?: { publicMetadata?: Record<string, unknown> };
  };
}

async function authedFetch(
  page: Page,
  path: string,
  method: string,
  body: Record<string, unknown> | null,
): Promise<{ status: number; json: Record<string, unknown> }> {
  return page.evaluate(
    async ({ path: p, method: mth, body: b, tenantId }) => {
      const w = window as typeof window & ClerkWin;
      const token = await w.Clerk?.session?.getToken();
      if (!token) return { status: -1, json: {} };
      const clinicId = String(w.Clerk?.user?.publicMetadata?.["clinicId"] ?? "");
      const meRes = await fetch("/api/v1/iam/users/me", {
        headers: { Authorization: `Bearer ${token}`, "X-Tenant-ID": tenantId },
      });
      const me = (await meRes.json()) as { id?: string };
      const res = await fetch(p, {
        method: mth,
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
          "X-Clinic-ID": clinicId,
          "X-User-ID": me.id ?? "",
          "X-User-Role": "owner",
          ...(b ? { "Content-Type": "application/json" } : {}),
        },
        ...(b ? { body: JSON.stringify(b) } : {}),
      });
      let json: Record<string, unknown> = {};
      try {
        json = (await res.json()) as Record<string, unknown>;
      } catch {
        /* empty / non-json */
      }
      return { status: res.status, json };
    },
    { path, method, body, tenantId: TENANT_ID } as {
      path: string;
      method: string;
      body: Record<string, unknown> | null;
      tenantId: string;
    },
  ) as Promise<{ status: number; json: Record<string, unknown> }>;
}

/** Create a block via the REAL BE. Returns { status, blockId }. */
export async function apiCreateBlock(
  page: Page,
  payload: Record<string, unknown>,
): Promise<{ status: number; blockId: string }> {
  const { status, json } = await authedFetch(page, BLOCKS_PATH, "POST", payload);
  return { status, blockId: String(json["id"] ?? "") };
}

/** PATCH a block via the REAL BE. */
export async function apiPatchBlock(
  page: Page,
  blockId: string,
  payload: Record<string, unknown>,
): Promise<{ status: number }> {
  const { status } = await authedFetch(page, `${BLOCKS_PATH}/${blockId}`, "PATCH", payload);
  return { status };
}

/** DELETE a block via the REAL BE (cleanup). */
export async function apiDeleteBlockR4(page: Page, blockId: string): Promise<number> {
  const { status } = await authedFetch(page, `${BLOCKS_PATH}/${blockId}`, "DELETE", null);
  return status;
}

// ── DATABASE ground truth (independent of the FE entirely) ────────────────────

export interface DbBlockTruth {
  /** number of OCCURRENCES = distinct slot dates (the matrix's "condición de fin").
   *  NB: a 1-hour block materializes 2 half-hour slot ROWS per date — we dedupe
   *  to dates so `count` means occurrences, not raw 30-min slot rows. */
  count: number;
  /** distinct ISODOW present in slots (1=Mon..7=Sun), sorted */
  isodows: number[];
  /** distinct slot dates YYYY-MM-DD, sorted ascending (one per occurrence) */
  dates: string[];
}

/** Query vitalia_availability_slots directly — the BE's source of truth. */
export function dbBlockTruth(blockId: string): DbBlockTruth {
  const sql = `SELECT to_char(slot_date,'YYYY-MM-DD') AS d, EXTRACT(ISODOW FROM slot_date)::int AS iso FROM vitalia_availability_slots WHERE block_id='${blockId}' AND deleted_at IS NULL ORDER BY slot_date;`;
  const out = execSync(
    `docker exec ${PG_CONTAINER} psql -U postgres -d ${PG_DB} -t -A -F',' -c "${sql}"`,
    { encoding: "utf8" },
  ).trim();
  const rows = out
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);
  const dateSet = new Set<string>();
  const isoSet = new Set<number>();
  for (const r of rows) {
    const [d, iso] = r.split(",");
    if (d) dateSet.add(d);
    if (iso) isoSet.add(Number(iso));
  }
  const dates = [...dateSet].sort();
  return { count: dates.length, isodows: [...isoSet].sort((a, b) => a - b), dates };
}

// ── RENDERED geometry ground truth (where the FE actually painted) ────────────

/**
 * For each painted occurrence of `blockId` currently VISIBLE in the week grid,
 * return its occurrenceDate (read from the DOM attribute the BE supplied) and
 * the column index it is geometrically painted in (matched against the rendered
 * day-col header x-ranges). NO production date math involved.
 */
export async function paintedColumnsOf(
  page: Page,
  blockId: string,
): Promise<{ occurrenceDate: string; col: number }[]> {
  // Header column x-ranges (0..6)
  const colBoxes: { x: number; w: number }[] = [];
  for (let i = 0; i < 7; i++) {
    const box = await page.getByTestId(`day-col-${i}`).boundingBox();
    if (!box) throw new Error(`day-col-${i} sin boundingBox`);
    colBoxes.push({ x: box.x, w: box.width });
  }
  const blocks = page.locator(`[data-testid="block-${blockId}"]`);
  const n = await blocks.count();
  const result: { occurrenceDate: string; col: number }[] = [];
  for (let i = 0; i < n; i++) {
    const el = blocks.nth(i);
    const date = (await el.getAttribute("data-occurrence-date")) ?? "";
    const box = await el.boundingBox();
    if (!box) continue;
    const cx = box.x + box.width / 2;
    const col = colBoxes.findIndex((c) => cx >= c.x && cx < c.x + c.w);
    result.push({ occurrenceDate: date, col });
  }
  return result;
}

/**
 * HONEST header check: the column LABELED "Lun" must show a date that really is
 * a Monday, etc. Reads each header's day-number + the visible week to rebuild
 * the full date is brittle; instead we verify via painted occurrences in
 * paintedColumnsOf (occurrenceDate carries the full date). This helper asserts
 * the column→weekday invariant for a set of painted occurrences.
 */
export function colMatchesWeekday(occurrenceDate: string, col: number): boolean {
  return localWeekdayIndex(occurrenceDate) === col;
}

// ── Week navigation (deterministic; reads what is actually rendered) ───────────

export async function navNextWeek(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Semana siguiente" }).click();
  await page.waitForLoadState("networkidle").catch(() => undefined);
  await page.waitForTimeout(250);
}

export async function navPrevWeek(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Semana anterior" }).click();
  await page.waitForLoadState("networkidle").catch(() => undefined);
  await page.waitForTimeout(250);
}

/**
 * Sweep `weeks` consecutive weeks (current + forward), collecting every painted
 * occurrence of blockId with its column. The CORE honest assertion runs over
 * the union: every painted occurrence must satisfy col == localWeekdayIndex(date).
 */
export async function sweepPaintedOccurrences(
  page: Page,
  blockId: string,
  weeks: number,
): Promise<{ occurrenceDate: string; col: number }[]> {
  const all: { occurrenceDate: string; col: number }[] = [];
  for (let w = 0; w < weeks; w++) {
    const painted = await paintedColumnsOf(page, blockId);
    all.push(...painted);
    if (w < weeks - 1) await navNextWeek(page);
  }
  // back to start
  for (let w = 0; w < weeks - 1; w++) await navPrevWeek(page);
  return all;
}

export async function reloadHorarios(page: Page): Promise<void> {
  await page.reload({ waitUntil: "domcontentloaded" });
  await page.getByTestId("availability-calendar").waitFor({ state: "visible", timeout: 20_000 });
  await page.waitForLoadState("networkidle").catch(() => undefined);
}

/** Standard recurrent payload builder. days = 0=Mon..6=Sun. */
export function recurrentPayload(opts: {
  days: number[];
  interval?: number;
  end?: "open_ended" | "end_date" | "occurrences";
  endDate?: string;
  occurrences?: number;
  start?: string;
  end_t?: string;
}): Record<string, unknown> {
  return {
    kind: "recurrent",
    start_time: opts.start ?? "08:00:00",
    end_time: opts.end_t ?? "09:00:00",
    days_of_week: opts.days,
    interval: opts.interval ?? 1,
    end_condition_kind: opts.end ?? "open_ended",
    end_date: opts.endDate ?? null,
    occurrences: opts.occurrences ?? null,
  };
}

export function oneOffPayload(specificDate: string, start = "08:00:00", end = "09:00:00"): Record<string, unknown> {
  return { kind: "one_off", start_time: start, end_time: end, specific_date: specificDate };
}

// ── round-5: scoped delete + block metadata (DB ground truth) ─────────────────

/** Scoped DELETE via real BE: scope=series|occurrence|this_and_future. */
export async function apiDeleteScoped(
  page: Page,
  blockId: string,
  scope: "series" | "occurrence" | "this_and_future",
  occurrenceDate?: string,
): Promise<{ status: number; json: Record<string, unknown> }> {
  const qs = new URLSearchParams({ scope });
  if (occurrenceDate) qs.set("occurrence_date", occurrenceDate);
  return authedFetch(page, `${BLOCKS_PATH}/${blockId}?${qs.toString()}`, "DELETE", null);
}

export interface DbBlockMeta {
  excludedDates: string[];
  endDate: string | null;
  endConditionKind: string | null;
  deleted: boolean;
}

/** Read block-level metadata directly from DB (independent of the FE). */
export function dbBlockMeta(blockId: string): DbBlockMeta {
  const sql = `SELECT COALESCE(excluded_dates::text,'[]'), COALESCE(to_char(end_date,'YYYY-MM-DD'),''), COALESCE(end_condition_kind,''), (deleted_at IS NOT NULL) FROM vitalia_availability_blocks WHERE id='${blockId}';`;
  const out = execSync(
    `docker exec ${PG_CONTAINER} psql -U postgres -d ${PG_DB} -t -A -F'|' -c "${sql}"`,
    { encoding: "utf8" },
  ).trim();
  const [excl, end, eck, del] = out.split("|");
  let excludedDates: string[] = [];
  try {
    excludedDates = JSON.parse(excl || "[]") as string[];
  } catch {
    excludedDates = [];
  }
  return {
    excludedDates,
    endDate: end ? end : null,
    endConditionKind: eck ? eck : null,
    deleted: del === "t",
  };
}
