// cap: iam.luana-core-adoption
// story-origin: vitalia-fe-tenant-resolution-no-clerk-org (T-2)
"use client";

/**
 * useTenantLocale — returns tenant-level locale preferences (currency + timezone).
 *
 * Per .claude/rules/master-data.md:
 *   - NEVER hardcode 'USD' — use this hook's currency as fallback
 *   - NEVER toLocaleDateString() — use formatTenantDate*() with this timezone
 *
 * T-2 fix (2026-06-01): replaced useOrganization() + organization.publicMetadata
 * with useUser() reading from user.publicMetadata. The Clerk Organization
 * org_3DzUI3... was deleted → organization was always null → always fell back
 * to VITALIA_DEFAULT_LOCALE (hiding real tenant locale). Now reads correctly
 * from user.publicMetadata (our data, written by luana-core-iam).
 *
 * Per MEMORY.md::no-clerk-organizations: Luana does NOT use Clerk Organizations.
 * Locale prefs come from user.publicMetadata (our claim), NOT from Clerk
 * organization.publicMetadata.
 *
 * Reads from Clerk user public metadata (our data, written by luana-core-iam):
 *   - user.publicMetadata.currency (ISO 4217 code)
 *   - user.publicMetadata.timezone (IANA timezone name)
 *   - user.publicMetadata.locale (BCP 47 locale)
 *
 * Fallback: ARS / America/Argentina/Buenos_Aires (vitalia primary market).
 *
 * TODO: the canonical source of locale for the tenant (endpoint
 * GET /api/v1/tenant/locale or similar) should be used when available.
 * This hook is a best-effort read from publicMetadata as a convenient
 * client-side cache. Follow-up story to wire the actual tenant locale endpoint.
 */

import { useUser } from "@clerk/nextjs";

export interface TenantLocale {
  /** ISO 4217 currency code (e.g. "ARS", "MXN", "USD", "COP") */
  currency: string;
  /** IANA timezone name (e.g. "America/Argentina/Buenos_Aires") */
  timezone: string;
  /** BCP 47 locale for number/date formatting */
  locale: string;
}

const VITALIA_DEFAULT_LOCALE: TenantLocale = {
  currency: "ARS",
  timezone: "America/Argentina/Buenos_Aires",
  locale: "es-419",
};

/**
 * Returns tenant locale preferences from user.publicMetadata.
 * Falls back to Vitalia defaults (ARS / Buenos Aires / es-419).
 *
 * Does NOT use Clerk Organizations — reads exclusively from
 * user.publicMetadata (our data, written by luana-core-iam).
 */
export function useTenantLocale(): TenantLocale {
  const { user, isLoaded } = useUser();

  if (!isLoaded || !user) {
    return VITALIA_DEFAULT_LOCALE;
  }

  const meta = user.publicMetadata as Record<string, unknown>;

  const currency =
    typeof meta.currency === "string" && meta.currency.length === 3
      ? meta.currency
      : VITALIA_DEFAULT_LOCALE.currency;

  const timezone =
    typeof meta.timezone === "string" && meta.timezone.length > 0
      ? meta.timezone
      : VITALIA_DEFAULT_LOCALE.timezone;

  const locale =
    typeof meta.locale === "string" && meta.locale.length > 0
      ? meta.locale
      : VITALIA_DEFAULT_LOCALE.locale;

  return { currency, timezone, locale };
}
