// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * bug7-helpers.ts — shared helpers for bug7 round-3 real-backend specs.
 *
 * NO route mocks for the surface under test: availability-blocks /
 * availability-occurrences hit the REAL BE:8002 (work-order bug7-round3:
 * "cero mocks", verification-real-not-200).
 *
 * Used by: bug7-r3-d1-save-button.spec.ts · bug7-r3-d2-drag-create.spec.ts ·
 *          bug7-r3-d3-matrix.spec.ts
 */

import type { Page, Locator, Response } from "@playwright/test";
import { expect } from "../../fixtures/base";

export const TENANT_ID =
  process.env["E2E_TENANT_ID"] ?? "e69a691d-070e-5caf-a053-6e74642ec100";
export const DOCTOR_ID =
  process.env["E2E_DOCTOR_ID"] ?? "2464fad7-2124-46a0-9b41-cef9e489cc8d";
export const BLOCKS_PATH = `/api/v1/vitalia/clinics/doctors/${DOCTOR_ID}/availability-blocks`;
export const OCCURRENCES_PATH = `/api/v1/vitalia/clinics/doctors/${DOCTOR_ID}/availability-occurrences`;

// ── Date helpers (TZ-stable — local components, NEVER toISOString) ────────────
// bug7 r4: the previous version MIRRORED the production getCurrentWeekMonday bug
// (toISOString after a local setDate) → the round-3 ground truth agreed with
// broken production → matrix GREEN while Monday painted in the Sunday column.
// These now build dates from LOCAL components only, matching the fixed
// production SSoT (src/lib/format/calendarDates.ts).

function toLocalIso(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function mondayOfCurrentWeek(): string {
  const t = new Date();
  const day = new Date(t.getFullYear(), t.getMonth(), t.getDate());
  const dow = day.getDay(); // 0=Sun..6=Sat
  const diff = dow === 0 ? -6 : 1 - dow;
  day.setDate(day.getDate() + diff);
  return toLocalIso(day);
}

export function addDaysIso(iso: string, days: number): string {
  const [y, m, d] = iso.split("-").map(Number);
  const date = new Date(y!, m! - 1, d!);
  date.setDate(date.getDate() + days);
  return toLocalIso(date);
}

/** ISO date of a day (0=Mon..6=Sun) in the CURRENT calendar week. */
export function dateOfDayThisWeek(dayIndex: number): string {
  return addDaysIso(mondayOfCurrentWeek(), dayIndex);
}

// ── Navigation ───────────────────────────────────────────────────────────────

export async function gotoHorarios(page: Page): Promise<void> {
  await page.setViewportSize({ width: 1600, height: 1000 });
  await page.goto(`/${TENANT_ID}/lisa/staff/${DOCTOR_ID}/horarios`, {
    waitUntil: "domcontentloaded",
  });
  await page
    .getByTestId("availability-calendar")
    .waitFor({ state: "visible", timeout: 20_000 });
  // Let React Query settle (occurrences + blocks initial fetch)
  await page.waitForLoadState("networkidle").catch(() => undefined);
}

// ── Grid interaction ─────────────────────────────────────────────────────────

export function cellOf(page: Page, day: number, hour: number): Locator {
  return page.getByTestId(`cell-${day}-${hour}`);
}

async function cellCenter(
  page: Page,
  day: number,
  hour: number,
): Promise<{ x: number; y: number }> {
  const cell = cellOf(page, day, hour);
  await cell.scrollIntoViewIfNeeded();
  const box = await cell.boundingBox();
  if (!box) throw new Error(`cell-${day}-${hour} sin boundingBox`);
  return { x: box.x + box.width / 2, y: box.y + box.height / 2 };
}

/** Simple click on a cell (GCal: click = 1-hour draft) → popover opens. */
export async function clickCell(
  page: Page,
  day: number,
  hour: number,
): Promise<void> {
  const { x, y } = await cellCenter(page, day, hour);
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.up();
  await page
    .getByTestId("bloque-popover")
    .waitFor({ state: "visible", timeout: 5_000 });
}

/**
 * Drag-create WITHOUT releasing: down on fromHour, move through each hour
 * to toHour. Caller asserts mid-drag state, then calls page.mouse.up().
 */
export async function dragWithoutRelease(
  page: Page,
  day: number,
  fromHour: number,
  toHour: number,
): Promise<void> {
  const start = await cellCenter(page, day, fromHour);
  await page.mouse.move(start.x, start.y);
  await page.mouse.down();
  const step = toHour >= fromHour ? 1 : -1;
  for (let h = fromHour + step; step > 0 ? h <= toHour : h >= toHour; h += step) {
    const pt = await cellCenter(page, day, h);
    await page.mouse.move(pt.x, pt.y, { steps: 4 });
  }
}

/** Full drag-create gesture → popover opens. */
export async function dragCreate(
  page: Page,
  day: number,
  fromHour: number,
  toHour: number,
): Promise<void> {
  await dragWithoutRelease(page, day, fromHour, toHour);
  await page.mouse.up();
  await page
    .getByTestId("bloque-popover")
    .waitFor({ state: "visible", timeout: 5_000 });
}

// ── Popover interaction ──────────────────────────────────────────────────────

/** Open the "Repetir" Shadcn select and choose an option by label regex. */
export async function chooseRepetir(
  page: Page,
  label: RegExp,
): Promise<void> {
  await page.getByTestId("select-repetir").click();
  await page.getByRole("option", { name: label }).click();
}

/** Open the "Termina" select (simple = non-custom presets, custom = sub-editor). */
export async function chooseTermina(
  page: Page,
  variant: "simple" | "custom",
  label: RegExp,
): Promise<void> {
  const testid = variant === "simple" ? "select-termina-simple" : "select-termina";
  await page.getByTestId(testid).click();
  await page.getByRole("option", { name: label }).click();
}

export interface SaveResult {
  status: number;
  body: Record<string, unknown>;
  requestJson: Record<string, unknown>;
}

/**
 * X-User-ID capturado del último write real del app (robustez del cleanup:
 * el fetch in-page a /iam/users/me puede 401 puntualmente — token de testing
 * sin email — y dejaba el DELETE de cleanup con X-User-ID vacío → 422).
 */
let capturedUserId = "";

/** Click Guardar + wait for the real POST to BE. Returns status + payload + body. */
export async function saveAndWaitPost(page: Page): Promise<SaveResult> {
  const respPromise = page.waitForResponse(
    (r: Response) =>
      r.url().includes(BLOCKS_PATH) && r.request().method() === "POST",
    { timeout: 10_000 },
  );
  await page.getByTestId("btn-save-block").click();
  const resp = await respPromise;
  const requestJson = resp.request().postDataJSON() as Record<string, unknown>;
  capturedUserId =
    (await resp.request().headerValue("x-user-id")) ?? capturedUserId;
  let body: Record<string, unknown> = {};
  try {
    body = (await resp.json()) as Record<string, unknown>;
  } catch {
    /* non-json error body */
  }
  return { status: resp.status(), body, requestJson };
}

/** Click Actualizar + wait for the real PATCH to BE. */
export async function saveAndWaitPatch(page: Page): Promise<SaveResult> {
  const respPromise = page.waitForResponse(
    (r: Response) =>
      r.url().includes(BLOCKS_PATH) && r.request().method() === "PATCH",
    { timeout: 10_000 },
  );
  await page.getByTestId("btn-save-block").click();
  const resp = await respPromise;
  const requestJson = resp.request().postDataJSON() as Record<string, unknown>;
  let body: Record<string, unknown> = {};
  try {
    body = (await resp.json()) as Record<string, unknown>;
  } catch {
    /* non-json error body */
  }
  return { status: resp.status(), body, requestJson };
}

/** Toast sonner visible con texto. */
export async function expectToast(page: Page, text: RegExp): Promise<void> {
  await expect(page.locator("[data-sonner-toast]").filter({ hasText: text }).first()).toBeVisible({
    timeout: 5_000,
  });
}

// ── Cleanup (real DELETE via in-page fetch with the live Clerk session) ──────

/**
 * Deletes a block through the REAL BE DELETE endpoint using the browser's
 * live Clerk session (no mocks). Used for per-test cleanup.
 */
export async function apiDeleteBlock(
  page: Page,
  blockId: string,
): Promise<number> {
  return page.evaluate(
    async ({ path, tenantId, fallbackUserId }) => {
      type ClerkWindow = typeof window & {
        Clerk?: {
          session?: { getToken: () => Promise<string | null> };
          user?: { publicMetadata?: Record<string, unknown> };
        };
      };
      const w = window as ClerkWindow;
      const token = await w.Clerk?.session?.getToken();
      if (!token) return -1;
      const clinicId = String(w.Clerk?.user?.publicMetadata?.["clinicId"] ?? "");
      let userId = fallbackUserId;
      if (!userId) {
        const meRes = await fetch("/api/v1/iam/users/me", {
          headers: {
            Authorization: `Bearer ${token}`,
            "X-Tenant-ID": tenantId,
          },
        });
        const me = (await meRes.json()) as { id?: string };
        userId = me.id ?? "";
      }
      const res = await fetch(path, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
          "X-Clinic-ID": clinicId,
          "X-User-ID": userId,
          "X-User-Role": "owner",
        },
      });
      return res.status;
    },
    {
      path: `${BLOCKS_PATH}/${blockId}`,
      tenantId: TENANT_ID,
      fallbackUserId: capturedUserId,
    },
  );
}

/** GET real occurrences count over a window (projection verification, no mocks). */
export async function apiCountOccurrences(
  page: Page,
  fromIso: string,
  toIso: string,
  blockId?: string,
): Promise<number> {
  return page.evaluate(
    async ({ path, tenantId, fromIso: f, toIso: t, blockId: bid, fallbackUserId }) => {
      type ClerkWindow = typeof window & {
        Clerk?: {
          session?: { getToken: () => Promise<string | null> };
          user?: { publicMetadata?: Record<string, unknown> };
        };
      };
      const w = window as ClerkWindow;
      const token = await w.Clerk?.session?.getToken();
      if (!token) return -1;
      const clinicId = String(w.Clerk?.user?.publicMetadata?.["clinicId"] ?? "");
      let userId = fallbackUserId;
      if (!userId) {
        const meRes = await fetch("/api/v1/iam/users/me", {
          headers: { Authorization: `Bearer ${token}`, "X-Tenant-ID": tenantId },
        });
        const me = (await meRes.json()) as { id?: string };
        userId = me.id ?? "";
      }
      const res = await fetch(`${path}?from=${f}&to=${t}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "X-Tenant-ID": tenantId,
          "X-Clinic-ID": clinicId,
          "X-User-ID": userId,
          "X-User-Role": "owner",
        },
      });
      const json = (await res.json()) as {
        occurrences?: { blockId?: string }[];
      };
      const occ = json.occurrences ?? [];
      return bid ? occ.filter((o) => o.blockId === bid).length : occ.length;
    },
    {
      path: OCCURRENCES_PATH,
      tenantId: TENANT_ID,
      fromIso,
      toIso,
      blockId: blockId ?? null,
      fallbackUserId: capturedUserId,
    },
  );
}
