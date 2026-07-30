// cap: __shared__
// story-origin: TBD
/**
 * formatMoney — tenant-aware money formatter.
 *
 * NEVER hardcode 'USD'. Currency comes from tenant locale or API response.
 * Fallback chain: data.currency → tenantLocale.currency → 'ARS' (safest LatAm default).
 *
 * Per .claude/rules/master-data.md:
 *   - NEVER `currency || 'USD'`
 *   - Use `useTenantLocale()` for fallback in components
 *   - This helper is a pure function — caller provides currency
 */

/**
 * Format a monetary amount with the given currency code.
 *
 * @param amount - The numeric amount (e.g. 15000)
 * @param currency - ISO 4217 currency code (e.g. "ARS", "MXN", "USD", "COP")
 *                   Pass null to use a neutral fallback display.
 * @param locale - BCP 47 locale for number formatting (default: "es-419" = LatAm Spanish)
 * @returns Formatted currency string (e.g. "$ 15.000" or "ARS 15.000")
 */
export function formatMoney(
  amount: number,
  currency: string | null | undefined,
  locale: string = "es-419",
): string {
  const effectiveCurrency = currency ?? "ARS"; // LatAm safest default (not USD)

  try {
    return new Intl.NumberFormat(locale, {
      style: "currency",
      currency: effectiveCurrency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    // Fallback: plain number if currency code is invalid
    return `${effectiveCurrency} ${amount.toLocaleString(locale)}`;
  }
}
