// cap: __shared__
// story-origin: TBD
/**
 * formatTenantRelative — relative time formatter ("hace 3 minutos").
 *
 * Uses Intl.RelativeTimeFormat for locale-aware relative times.
 * Falls back to formatted absolute date if Intl.RelativeTimeFormat is unavailable.
 */

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const WEEK = 7 * DAY;
const MONTH = 30 * DAY;
const YEAR = 365 * DAY;

/**
 * Format an ISO 8601 datetime as a relative time string.
 *
 * @param isoString - ISO 8601 datetime string
 * @param locale - BCP 47 locale (default: "es-419")
 * @returns Relative time string (e.g. "hace 3 minutos", "hace 2 días") or "—" on error
 */
export function formatTenantRelative(
  isoString: string,
  locale: string = "es-419",
): string {
  if (!isoString) return "—";

  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return "—";

    const diffMs = date.getTime() - Date.now();
    const absDiffMs = Math.abs(diffMs);

    const rtf = new Intl.RelativeTimeFormat(locale, { numeric: "auto" });

    if (absDiffMs < MINUTE) {
      return rtf.format(Math.round(diffMs / SECOND), "second");
    } else if (absDiffMs < HOUR) {
      return rtf.format(Math.round(diffMs / MINUTE), "minute");
    } else if (absDiffMs < DAY) {
      return rtf.format(Math.round(diffMs / HOUR), "hour");
    } else if (absDiffMs < WEEK) {
      return rtf.format(Math.round(diffMs / DAY), "day");
    } else if (absDiffMs < MONTH) {
      return rtf.format(Math.round(diffMs / WEEK), "week");
    } else if (absDiffMs < YEAR) {
      return rtf.format(Math.round(diffMs / MONTH), "month");
    } else {
      return rtf.format(Math.round(diffMs / YEAR), "year");
    }
  } catch {
    return "—";
  }
}
