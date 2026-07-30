// cap: iam.luana-core-adoption
// story-origin: vitalia-fe-tenant-resolution-no-clerk-org (T-2)
/**
 * useTenantLocale.test.tsx — TDD RED → GREEN (T-2 2026-06-01)
 *
 * Verifies that useTenantLocale:
 * 1. Returns currency/timezone/locale from user.publicMetadata when present
 * 2. Falls back to VITALIA_DEFAULT_LOCALE when fields absent
 * 3. Falls back to VITALIA_DEFAULT_LOCALE when user is null
 * 4. Falls back to VITALIA_DEFAULT_LOCALE while loading (isLoaded = false)
 * 5. NEVER calls useOrganization — reads only from user.publicMetadata
 * 6. Applies correct field-level fallbacks (missing one field gets default for that field only)
 *
 * Per MEMORY.md::no-clerk-organizations: Luana does NOT use Clerk Organizations.
 * Locale prefs come from user.publicMetadata (our claim, written by luana-core-iam),
 * NOT from Clerk organization.publicMetadata.
 *
 * T-2 fix: replace useOrganization() → useUser() reading from user.publicMetadata.
 */

import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mock @clerk/nextjs
// We mock ONLY useUser — not useOrganization.
// If useOrganization were still imported, the mock would NOT provide it
// (vitest strict mock), causing an error that proves the hook is wrong.
// ---------------------------------------------------------------------------
const mockUseUser = vi.fn();

vi.mock("@clerk/nextjs", () => ({
  // Only useUser should be used by useTenantLocale after T-2 fix.
  // useOrganization deliberately NOT provided — proves it is not called.
  useUser: () => mockUseUser(),
}));

import { useTenantLocale } from "../useTenantLocale";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeUser(publicMetadata: Record<string, unknown>) {
  return { publicMetadata };
}

const VITALIA_DEFAULT = {
  currency: "ARS",
  timezone: "America/Argentina/Buenos_Aires",
  locale: "es-419",
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("useTenantLocale", () => {
  beforeEach(() => {
    mockUseUser.mockReset();
  });

  it("returns currency from user.publicMetadata when present (3-char ISO 4217)", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "MXN", timezone: "America/Mexico_City", locale: "es-MX" }),
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current.currency).toBe("MXN");
  });

  it("returns timezone from user.publicMetadata when present", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "COP", timezone: "America/Bogota", locale: "es-CO" }),
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current.timezone).toBe("America/Bogota");
  });

  it("returns locale from user.publicMetadata when present", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "PEN", timezone: "America/Lima", locale: "es-PE" }),
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current.locale).toBe("es-PE");
  });

  it("returns full locale object from publicMetadata when all fields present", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "USD", timezone: "America/Guayaquil", locale: "es-EC" }),
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current).toEqual({
      currency: "USD",
      timezone: "America/Guayaquil",
      locale: "es-EC",
    });
  });

  it("falls back to VITALIA_DEFAULT_LOCALE when user is null (not signed in)", () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current).toEqual(VITALIA_DEFAULT);
  });

  it("falls back to VITALIA_DEFAULT_LOCALE while isLoaded is false (Clerk loading)", () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoaded: false,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current).toEqual(VITALIA_DEFAULT);
  });

  it("falls back to default currency when currency field is absent from publicMetadata", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ timezone: "America/Lima", locale: "es-PE" }), // no currency
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current.currency).toBe(VITALIA_DEFAULT.currency);
  });

  it("falls back to default currency when currency is not a 3-char string", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "US", timezone: "America/New_York", locale: "en-US" }), // 2-char, invalid
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    // Must reject non-3-char currency codes
    expect(result.current.currency).toBe(VITALIA_DEFAULT.currency);
  });

  it("falls back to default timezone when timezone field is absent", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "COP", locale: "es-CO" }), // no timezone
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current.timezone).toBe(VITALIA_DEFAULT.timezone);
  });

  it("falls back to default timezone when timezone is empty string", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "COP", timezone: "", locale: "es-CO" }),
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current.timezone).toBe(VITALIA_DEFAULT.timezone);
  });

  it("falls back to default locale when locale field is absent", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "ARS", timezone: "America/Argentina/Buenos_Aires" }), // no locale
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current.locale).toBe(VITALIA_DEFAULT.locale);
  });

  it("falls back entirely to VITALIA_DEFAULT_LOCALE when publicMetadata is empty", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({}), // no locale fields at all
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantLocale());

    expect(result.current).toEqual(VITALIA_DEFAULT);
  });

  it("does NOT use Clerk Organization — no useOrganization called (mock enforcement)", () => {
    // useOrganization is NOT in the vi.mock() map above.
    // If the hook still tries to import/call useOrganization, vitest will
    // either throw (strict mode) or return undefined (lax), causing the hook
    // to crash or misbehave. This test confirms it does NOT crash.
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "ARS", timezone: "America/Argentina/Buenos_Aires", locale: "es-419" }),
      isLoaded: true,
    });

    // Must not throw (would throw if useOrganization called without mock)
    expect(() => renderHook(() => useTenantLocale())).not.toThrow();

    const { result } = renderHook(() => useTenantLocale());
    expect(result.current.currency).toBe("ARS");
  });

  it("useUser is called — confirms dependency on useUser (not useOrganization)", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ currency: "MXN", timezone: "America/Mexico_City", locale: "es-MX" }),
      isLoaded: true,
    });

    renderHook(() => useTenantLocale());

    expect(mockUseUser).toHaveBeenCalledTimes(1);
  });
});
