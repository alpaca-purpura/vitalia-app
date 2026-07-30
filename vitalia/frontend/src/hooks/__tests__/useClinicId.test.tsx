// cap: compliance.hipaa-lite-defensive-stack
// story-origin: vitalia-fase2-lisa-doctores (T-FIX-1-FE)
/**
 * useClinicId.test.tsx — TDD RED → GREEN (T-FIX-1-FE 2026-06-01)
 *
 * Verifies that useClinicId:
 * 1. Returns clinicId from user.publicMetadata.clinicId when present
 * 2. Returns null when user has no clinicId in publicMetadata
 * 3. Returns null while still loading (isLoaded = false)
 * 4. Returns null when user is null (not signed in)
 * 5. NEVER calls useOrganization (Clerk Organizations are not used in Luana)
 *
 * Per MEMORY.md::no-clerk-organizations: clinic_id comes exclusively from
 * user.publicMetadata (written by luana-core-iam), NOT from Clerk org APIs.
 */

import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mock @clerk/nextjs
// We mock ONLY what useClinicId uses after T-FIX-1-FE fix: useUser.
// If useOrganization were imported, this mock would error (it is NOT in the mock),
// which would cause an import-time failure — proving the fix is correct.
// ---------------------------------------------------------------------------
const mockUseUser = vi.fn();

vi.mock("@clerk/nextjs", () => ({
  useUser: () => mockUseUser(),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


import { useClinicId } from "../useClinicId";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeUser(publicMetadata: Record<string, unknown>) {
  return { publicMetadata };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("useClinicId", () => {
  beforeEach(() => {
    mockUseUser.mockReset();
  });

  it("returns clinicId from user.publicMetadata.clinicId when present", () => {
    const clinicId = "clinic-uuid-abc-123";
    mockUseUser.mockReturnValue({
      user: makeUser({ clinicId }),
      isLoaded: true,
    });

    const { result } = renderHook(() => useClinicId());

    expect(result.current).toBe(clinicId);
  });

  it("returns null when user publicMetadata has no clinicId field", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ tenantId: "tenant-123" }), // no clinicId
      isLoaded: true,
    });

    const { result } = renderHook(() => useClinicId());

    expect(result.current).toBeNull();
  });

  it("returns null when clinicId is an empty string", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ clinicId: "" }),
      isLoaded: true,
    });

    const { result } = renderHook(() => useClinicId());

    expect(result.current).toBeNull();
  });

  it("returns null when clinicId is not a string (e.g. number)", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ clinicId: 42 }), // wrong type — should be ignored
      isLoaded: true,
    });

    const { result } = renderHook(() => useClinicId());

    expect(result.current).toBeNull();
  });

  it("returns null while isLoaded is false (data still loading)", () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoaded: false,
    });

    const { result } = renderHook(() => useClinicId());

    expect(result.current).toBeNull();
  });

  it("returns null when user is null (not signed in)", () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoaded: true,
    });

    const { result } = renderHook(() => useClinicId());

    expect(result.current).toBeNull();
  });

  it("does NOT call useOrganization (Clerk Organizations not used in Luana)", () => {
    // This test verifies the architectural constraint from MEMORY.md::no-clerk-organizations.
    // The mock above only provides useUser — if useOrganization were imported and called,
    // it would throw because it is not in the mock map.
    // We additionally verify this by asserting the mock has no org-related calls.
    mockUseUser.mockReturnValue({
      user: makeUser({ clinicId: "clinic-test" }),
      isLoaded: true,
    });

    // This must not throw (would throw if useOrganization() is called and not mocked)
    expect(() => renderHook(() => useClinicId())).not.toThrow();

    // useUser was called exactly once — no org hook involved
    expect(mockUseUser).toHaveBeenCalledTimes(1);
  });
});
