// cap: scheduling.mateo-agenda
/**
 * datetime-utils — tz-correct date/time helpers for the nueva-cita Fecha/Hora split.
 * Extracted from NuevaCitaView (T-D2) for testability + to fix the tz regression
 * (G#1 round 1: 08:00 inicio mostraba fin 05:30 = +30min −3h porque la hora wall-clock
 * se trataba como UTC al pegarle "Z" en vez de convertir tenant-local→UTC).
 */

/**
 * Build a UTC ISO string from a local wall-clock `date` ("YYYY-MM-DD") + `time` ("HH:mm")
 * interpreted in `timezone`.
 *   "2026-06-29" + "08:00" @ America/Argentina/Buenos_Aires (UTC-3) → "2026-06-29T11:00:00.000Z".
 *
 * ponytail: single-pass offset via Intl (dependency-free, matches isoToHHMM; date-fns-tz is
 * NOT a direct dep of vitalia/frontend, only hoisted via the kit). Off by ≤1h only on the ~2
 * DST-transition instants/year — clinics don't book across the spring-forward gap. If exact
 * DST-edge handling is ever needed, add date-fns-tz as a direct dep and swap to fromZonedTime.
 */
export function buildIsoFromDateAndTime(
  date: string | undefined,
  time: string | undefined,
  timezone: string,
): string | undefined {
  if (!date || !time) return undefined;
  try {
    const [y, mo, d] = date.split("-").map(Number);
    const [h, mi] = time.split(":").map(Number);
    if ([y, mo, d, h, mi].some(Number.isNaN)) return undefined;
    const utcGuess = Date.UTC(y, mo - 1, d, h, mi, 0);
    // What wall-clock does `timezone` show at the guessed instant? The diff is the offset.
    const parts = new Intl.DateTimeFormat("en-US", {
      timeZone: timezone,
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hourCycle: "h23",
    }).formatToParts(new Date(utcGuess));
    const f: Record<string, number> = {};
    for (const p of parts) if (p.type !== "literal") f[p.type] = Number(p.value);
    const tzWallAsUtc = Date.UTC(f.year, f.month - 1, f.day, f.hour, f.minute, f.second);
    const offsetMs = tzWallAsUtc - utcGuess; // tz is ahead of UTC by offsetMs (negative if behind)
    return new Date(utcGuess - offsetMs).toISOString();
  } catch {
    return undefined;
  }
}

/** Add `minutes` to an ISO string → new ISO string. */
export function addMinutesToIso(isoStart: string, minutes: number): string {
  const d = new Date(isoStart);
  d.setMinutes(d.getMinutes() + minutes);
  return d.toISOString();
}

/** Format a UTC ISO to "HH:mm" wall-clock in `timezone`. */
export function isoToHHMM(isoString: string, timezone: string): string {
  try {
    return new Intl.DateTimeFormat("es", {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).format(new Date(isoString));
  } catch {
    return "";
  }
}
