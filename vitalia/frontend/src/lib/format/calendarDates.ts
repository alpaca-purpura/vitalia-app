// cap: clinics.lisa.doctores
/**
 * calendarDates — TZ-stable local-calendar date math (single SSoT).
 *
 * WHY THIS EXISTS (bug7 round-4): the staff calendar computed week anchors with
 * `someDate.toISOString().split("T")[0]` AFTER doing arithmetic on a LOCAL Date.
 * Under a negative UTC offset (e.g. America/Lima −05) in the evening, the LOCAL
 * date and the UTC date differ by one day → `getCurrentWeekMonday()` returned a
 * TUESDAY → the whole week grid shifted one column → a Monday block painted in
 * the Sunday column (Chris's report). The BE was always correct.
 *
 * RULE: never derive a calendar Y-M-D from `toISOString()`. Build it from LOCAL
 * components (`getFullYear`/`getMonth`/`getDate`). These helpers do exactly that
 * and are the ONE place the staff calendar (week view, month view, popover,
 * store) computes dates — so the bug class cannot reappear piecemeal.
 *
 * All inputs/outputs are `YYYY-MM-DD` strings interpreted in LOCAL time.
 */

/** Parse a `YYYY-MM-DD` string into a LOCAL Date at local midnight (no UTC parse). */
export function parseLocalDate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y ?? 1970, (m ?? 1) - 1, d ?? 1);
}

/** Format a Date to `YYYY-MM-DD` using LOCAL components (never toISOString). */
export function toLocalIsoDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** Add (or subtract) whole days to a `YYYY-MM-DD` string. TZ-stable. */
export function addLocalDays(iso: string, days: number): string {
  const d = parseLocalDate(iso);
  d.setDate(d.getDate() + days);
  return toLocalIsoDate(d);
}

/**
 * ISO Monday (`YYYY-MM-DD`) of the week containing `input`.
 * Accepts a Date (its time-of-day is discarded) or a `YYYY-MM-DD` string.
 * ISO week: Monday … Sunday.
 */
export function mondayOfWeek(input: Date | string): string {
  const base = typeof input === "string" ? parseLocalDate(input) : input;
  // Rebuild at local midnight to discard any time-of-day on a realtime Date.
  const day = new Date(base.getFullYear(), base.getMonth(), base.getDate());
  const dow = day.getDay(); // 0=Sun..6=Sat (LOCAL)
  const diff = dow === 0 ? -6 : 1 - dow; // back to Monday
  day.setDate(day.getDate() + diff);
  return toLocalIsoDate(day);
}

/**
 * Day index 0=Mon..6=Sun for a `YYYY-MM-DD` date (local, TZ-stable).
 * Inverse mapping of the calendar's column order.
 */
export function localWeekdayIndex(iso: string): number {
  const dow = parseLocalDate(iso).getDay(); // 0=Sun..6=Sat
  return dow === 0 ? 6 : dow - 1;
}
