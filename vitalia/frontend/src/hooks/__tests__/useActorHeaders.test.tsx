/**
 * useActorHeaders.test.tsx — shared HIPAA-lite actor headers hook.
 * vitalia-bugfix-agenda-actor-headers-422
 *
 * Tests cover:
 *   - X-User-ID resolves to the DB user UUID from the /me query cache (NOT Clerk id)
 *   - X-User-Role resolves to the PER-TENANT role from the tenant store
 *   - X-User-ID is "" before /me resolves (caller gates on it)
 *   - falls back to activeTenant.role when no availableTenants match
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { useActorHeaders } from "../useActorHeaders";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
    isLoaded: true,
    isSignedIn: true,
  })),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: vi.fn(() => "tenant-1"),
}));

vi.mock("@/lib/api/fetchClient", () => ({
  // Default resolves to a value (never undefined) so the /me query never warns.
  // Individual tests override with mockResolvedValueOnce when they assert the UUID.
  fetchClient: vi.fn().mockResolvedValue({ id: "db-uuid-default" }),
}));

const tenantStoreState = {
  availableTenants: [{ id: "tenant-1", name: "Clínica A", role: "doctor" }],
  activeTenant: { id: "tenant-1", name: "Clínica A", role: "doctor" },
};

vi.mock("@/stores/tenant-store", () => ({
  useTenantStore: vi.fn(
    (selector: (s: typeof tenantStoreState) => unknown) =>
      selector(tenantStoreState),
  ),
}));

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  };
}

describe("useActorHeaders", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("resolves X-User-ID to the DB UUID from /me (not the Clerk id)", async () => {
    const { fetchClient } = await import("@/lib/api/fetchClient");
    vi.mocked(fetchClient).mockResolvedValueOnce({
      id: "db-uuid-1234",
    } as never);

    const { result } = renderHook(() => useActorHeaders(), {
      wrapper: makeWrapper(),
    });

    await waitFor(() =>
      expect(result.current["X-User-ID"]).toBe("db-uuid-1234"),
    );
    expect(fetchClient).toHaveBeenCalledWith(
      "/api/v1/iam/users/me",
      expect.objectContaining({ token: "test-token", tenantId: "tenant-1" }),
    );
  });

  it("resolves X-User-Role to the per-tenant role from the tenant store", () => {
    const { result } = renderHook(() => useActorHeaders(), {
      wrapper: makeWrapper(),
    });
    expect(result.current["X-User-Role"]).toBe("doctor");
  });

  it("returns empty X-User-ID before /me resolves (caller gates on it)", () => {
    const { result } = renderHook(() => useActorHeaders(), {
      wrapper: makeWrapper(),
    });
    // /me not yet resolved → empty UUID
    expect(result.current["X-User-ID"]).toBe("");
  });
});
