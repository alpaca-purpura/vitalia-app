// cap: __shared__
// story-origin: TBD
/**
 * formatTenantDate — date formatter in tenant timezone.
 *
 * Per .claude/rules/master-data.md:
 *   - NEVER `toLocaleDateString()` — use this helper
 *   - BE stores UTC, FE displays in tenant timezone
 *   - Timezone comes from `useTenantLocale().timezone`
 */

/**
 * Format an ISO 8601 date string into a localized date string
 * using the tenant's configured timezone.
 *
 * @param isoString - ISO 8601 date/datetime string (UTC or with offset)
 * @param timezone - IANA timezone (e.g. "America/Argentina/Buenos_Aires", "America/Mexico_City")
 * @param locale - BCP 47 locale (default: "es-419")
 * @returns Formatted date string (e.g. "15 de marzo de 2026") or "—" on error
 */
export function formatTenantDate(
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
      timeZone: timezone,
    }).format(date);
  } catch {
    return "—";
  }
}
