// cap: __shared__
// story-origin: TBD
/**
 * formatTenantDateTime — datetime formatter in tenant timezone.
 *
 * Per .claude/rules/master-data.md:
 *   - NEVER `toLocaleDateString()` or `toLocaleTimeString()` — use this helper
 *   - BE stores UTC, FE displays in tenant timezone
 */

/**
 * Format an ISO 8601 datetime string into a localized date+time string
 * using the tenant's configured timezone.
 *
 * @param isoString - ISO 8601 datetime string (UTC or with offset)
 * @param timezone - IANA timezone (e.g. "America/Argentina/Buenos_Aires")
 * @param locale - BCP 47 locale (default: "es-419")
 * @returns Formatted datetime string (e.g. "15 de marzo de 2026, 11:30") or "—" on error
 */
export function formatTenantDateTime(
  isoString: string,
  timezone: string = "UTC",
  locale: string = "es-419",
): string {
  if (!isoString) return "—";

  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return "—";

    return new Intl.DateTimeFormat(locale, {
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      timeZone: timezone,
    }).format(date);
  } catch {
    return "—";
  }
}
