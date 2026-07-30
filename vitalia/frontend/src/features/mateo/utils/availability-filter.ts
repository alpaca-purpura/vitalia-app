// cap: scheduling.mateo-agenda
/**
 * availability-filter.ts — Advisory client-side hour filter for T-D3.
 *
 * isDoctorFreeAt: advisory only — server availability/check + EXCLUDE constraint
 * is the AUTHORITY (RN-10). This filter is for UX pre-selection only.
 *
 * Half-open [start, end) semantics per RN-2: back-to-back appointments are free.
 * A block [10:00, 11:00) does NOT block a query for 11:00.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE utils; no cross-brand consumers
 * spec_anchor: 03-arch-delta-availability.md § 4 filter-1c + § RN-2 + § RN-10
 */

import type { DayBlockItem, ServiceDayDoctor } from "../types/agenda-schema";

// ── Helpers ────────────────────────────────────────────────────────────────

/** Parse "HH:mm" to minutes since midnight. Returns -1 on invalid input. */
function hhmmToMinutes(hhmm: string): number {
  const [hStr, mStr] = hhmm.split(":");
  const h = parseInt(hStr ?? "", 10);
  const m = parseInt(mStr ?? "", 10);
  if (Number.isNaN(h) || Number.isNaN(m)) return -1;
  return h * 60 + m;
}

/**
 * Convert ISO datetime to minutes since midnight in the given timezone.
 * Uses Intl.DateTimeFormat (same approach as isoToStripMinutes in DayAvailabilityStrip).
 * ponytail: duplicated intentionally (2 consumers < threshold for extraction).
 */
function isoToLocalMinutes(iso: string, timezone: string): number {
  try {
    const parts = new Intl.DateTimeFormat("en", {
      timeZone: timezone,
      hour: "numeric",
      minute: "numeric",
      hourCycle: "h23",
    }).formatToParts(new Date(iso));
    const h = parseInt(parts.find((p) => p.type === "hour")?.value ?? "", 10);
    const m = parseInt(parts.find((p) => p.type === "minute")?.value ?? "", 10);
    if (Number.isNaN(h) || Number.isNaN(m)) return -1;
    return h * 60 + m;
  } catch {
    return -1;
  }
}

// ── Exports ────────────────────────────────────────────────────────────────

/**
 * isDoctorFreeAt — advisory check: is the HH:mm time within working_hours
 * and NOT overlapping any busy block?
 *
 * Half-open [start, end): start <= target < end.
 * back-to-back: block ending at targetMin is NOT busy at targetMin (RN-2).
 *
 * Advisory only — server is the authority for real booking (RN-10).
 */
export function isDoctorFreeAt(
  blocks: DayBlockItem[],
  timeHHMM: string,
  timezone: string,
): boolean {
  const targetMin = hhmmToMinutes(timeHHMM);
  if (targetMin < 0) return false;

  const inWorking = blocks.some((b) => {
    if (b.kind !== "working_hours") return false;
    const s = isoToLocalMinutes(b.startTime, timezone);
    const e = isoToLocalMinutes(b.endTime, timezone);
    if (s < 0 || e <= s) return false;
    return s <= targetMin && targetMin < e; // half-open [s, e)
  });

  if (!inWorking) return false;

  const isBusy = blocks.some((b) => {
    if (b.kind !== "busy") return false;
    const s = isoToLocalMinutes(b.startTime, timezone);
    const e = isoToLocalMinutes(b.endTime, timezone);
    if (s < 0 || e <= s) return false;
    return s <= targetMin && targetMin < e; // half-open [s, e)
  });

  return !isBusy;
}

/**
 * filterFreeDoctors — returns doctors free at the given HH:mm time.
 * Returns [] when timeHHMM is empty (no hour selected yet).
 * Advisory only (RN-10).
 */
export function filterFreeDoctors(
  doctors: ServiceDayDoctor[],
  timeHHMM: string,
  timezone: string,
): ServiceDayDoctor[] {
  if (!timeHHMM) return [];
  return doctors.filter((d) => isDoctorFreeAt(d.blocks, timeHHMM, timezone));
}
