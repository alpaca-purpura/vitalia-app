// cap: __shared__
// story-origin: TBD
/**
 * formatTenantTime — time-only formatter in tenant timezone.
 *
 * Per .claude/rules/master-data.md:
 *   - NEVER `toLocaleTimeString()` — use this helper
 *   - BE stores UTC, FE displays in tenant timezone
 *   - Timezone comes from `useTenantLocale().timezone`
 */

/**
 * Format an ISO 8601 datetime string into a localized time-only string (HH:MM:SS)
 * using the tenant's configured timezone.
 *
 * @param isoString - ISO 8601 datetime string (UTC or with offset)
 * @param timezone - IANA timezone (e.g. "America/Argentina/Buenos_Aires")
 * @param locale - BCP 47 locale (default: "es-419")
 * @returns Formatted time string (e.g. "11:30:45") or "—" on error
 */
export function formatTenantTime(
  isoString: string,
  timezone: string = "UTC",
  locale: string = "es-419",
): string {
  if (!isoString) return "—";

  try {
    const date = new Date(isoString);
    if (isNaN(date.getTime())) return "—";

    return new Intl.DateTimeFormat(locale, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
      timeZone: timezone,
    }).format(date);
  } catch {
    return "—";
  }
}
