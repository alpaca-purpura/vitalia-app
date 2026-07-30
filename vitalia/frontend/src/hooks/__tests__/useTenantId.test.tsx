// cap: iam.luana-core-adoption
// story-origin: vitalia-fe-tenant-resolution-no-clerk-org (T-1)
/**
 * useTenantId.test.tsx — TDD RED → GREEN (T-1 2026-06-01)
 *
 * Verifies that useTenantId:
 * 1. Returns tenant_id from user.publicMetadata.tenant_id when present
 * 2. Returns null when user has no tenant_id in publicMetadata
 * 3. Returns null while still loading (isLoaded = false)
 * 4. Returns null when user is null (not signed in)
 * 5. NEVER reads from Clerk orgId / useOrganization
 * 6. Returns null when tenant_id is empty string
 * 7. Returns null when tenant_id is not a string (wrong type)
 *
 * Per MEMORY.md::no-clerk-organizations: tenant_id comes exclusively from
 * user.publicMetadata (written by luana-core-iam), NOT from Clerk org APIs.
 * useAuth().orgId is NOT a UUID — it is the Clerk org id (format: org_xxx).
 */

import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

// ---------------------------------------------------------------------------
// Mock @clerk/nextjs
// We mock ONLY what useTenantId uses: useUser.
// If useOrganization / useAuth were imported for orgId, this mock would NOT
// provide them — causing import-time errors that prove the hook is correct.
// ---------------------------------------------------------------------------
const mockUseUser = vi.fn();

vi.mock("@clerk/nextjs", () => ({
  useUser: () => mockUseUser(),
}));

import { useTenantId } from "../useTenantId";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeUser(publicMetadata: Record<string, unknown>) {
  return { publicMetadata };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------
describe("useTenantId", () => {
  beforeEach(() => {
    mockUseUser.mockReset();
  });

  it("returns tenant_id from user.publicMetadata.tenant_id when present", () => {
    const tenantId = "e69a691d-070e-5caf-a053-6e74642ec100";
    mockUseUser.mockReturnValue({
      user: makeUser({ tenant_id: tenantId }),
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantId());

    expect(result.current).toBe(tenantId);
  });

  it("returns null when user publicMetadata has no tenant_id field", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ clinicId: "clinic-uuid-123" }), // no tenant_id
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantId());

    expect(result.current).toBeNull();
  });

  it("returns null when tenant_id is an empty string", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ tenant_id: "" }),
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantId());

    expect(result.current).toBeNull();
  });

  it("returns null when tenant_id is not a string (e.g. number — wrong type)", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ tenant_id: 42 }), // wrong type — must be ignored
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantId());

    expect(result.current).toBeNull();
  });

  it("returns null while isLoaded is false (Clerk data still loading)", () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoaded: false,
    });

    const { result } = renderHook(() => useTenantId());

    expect(result.current).toBeNull();
  });

  it("returns null when user is null (not signed in)", () => {
    mockUseUser.mockReturnValue({
      user: null,
      isLoaded: true,
    });

    const { result } = renderHook(() => useTenantId());

    expect(result.current).toBeNull();
  });

  it("does NOT use Clerk orgId (would be org_xxx format, not UUID)", () => {
    // This test verifies the architectural constraint.
    // The mock only provides useUser — if useAuth were called for orgId,
    // it would throw because useAuth is NOT in the mock map.
    // We verify useTenantId does not depend on orgId.
    const orgStyleId = "org_3DzUI3lLjwX83Kth0j5enWrjIDY"; // Clerk org format, NOT UUID
    mockUseUser.mockReturnValue({
      // Even if someone were to add orgId to publicMetadata (wrong pattern),
      // useTenantId must read tenant_id specifically.
      user: makeUser({ tenant_id: "e69a691d-070e-5caf-a053-6e74642ec100" }),
      isLoaded: true,
    });

    // Must not throw (would throw if useAuth/useOrganization called without mock)
    expect(() => renderHook(() => useTenantId())).not.toThrow();

    // Returns our UUID, not the Clerk org id format
    const { result } = renderHook(() => useTenantId());
    expect(result.current).toBe("e69a691d-070e-5caf-a053-6e74642ec100");
    expect(result.current).not.toBe(orgStyleId);
    expect(result.current).not.toMatch(/^org_/);
  });

  it("useUser is called exactly once — no org hooks involved", () => {
    mockUseUser.mockReturnValue({
      user: makeUser({ tenant_id: "e69a691d-070e-5caf-a053-6e74642ec100" }),
      isLoaded: true,
    });

    renderHook(() => useTenantId());

    // Only useUser, no other Clerk hooks
    expect(mockUseUser).toHaveBeenCalledTimes(1);
  });
});
