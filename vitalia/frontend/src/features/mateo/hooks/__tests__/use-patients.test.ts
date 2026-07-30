// cap: scheduling.mateo-agenda
/**
 * use-patients.test.ts — TDD RED-first (T-FE-2)
 *
 * Hook tests:
 *  - useSearchPatients: searchFn calls correct endpoint with dual headers
 *  - useCreatePatientInline: POST maps channel "telefono"→"phone" (contract mismatch fix)
 *  - useCreatePatientInline: returns isDuplicate flag from BE
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Hoist mock fn declarations so vi.mock factories can reference them
const { mockFetch, mockGetToken } = vi.hoisted(() => ({
  mockFetch: vi.fn(),
  mockGetToken: vi.fn().mockResolvedValue("test-token"),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: mockGetToken,
    isLoaded: true,
    isSignedIn: true,
  }),
}));

vi.mock("@/lib/fetch-client", () => ({
  vitaliaFetch: mockFetch,
}));

vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-1",
}));

vi.mock("@/hooks/useActorHeaders", () => ({
  useActorHeaders: () => ({ "X-User-ID": "user-1", "X-User-Role": "doctor" }),
}));

import { useSearchPatients, useCreatePatientInline } from "../use-patients";

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return React.createElement(QueryClientProvider, { client: qc }, children);
}

describe("useSearchPatients", () => {
  beforeEach(() => vi.clearAllMocks());

  it("searchFn calls GET /api/v1/crm/patients with q and clinic header", async () => {
    mockFetch.mockResolvedValueOnce({
      items: [
        {
          patient_id: "pid-1",
          name_masked: "J*** G***",
          phone_masked: "+54 ***",
          channel_first: "walk_in",
          created_at: "2026-01-01T00:00:00Z",
        },
      ],
      next_cursor: null,
      total_approx: 1,
    });

    const { result } = renderHook(
      () => useSearchPatients({ tenantId: "t-1" }),
      { wrapper },
    );

    const res = await act(async () =>
      result.current.searchFn({ q: "Juan", cursor: null, limit: 20 }),
    );

    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/crm/patients"),
      expect.objectContaining({
        headers: expect.objectContaining({ "X-Clinic-ID": "clinic-1" }),
      }),
    );
    expect(res.items[0]).toMatchObject({
      id: "pid-1",
      name: "J*** G***",
    });
    expect(res.nextCursor).toBeNull();
  });

  it("passes cursor as query param when provided", async () => {
    mockFetch.mockResolvedValueOnce({ items: [], next_cursor: null, total_approx: 0 });

    const { result } = renderHook(
      () => useSearchPatients({ tenantId: "t-1" }),
      { wrapper },
    );

    await act(async () =>
      result.current.searchFn({ q: "", cursor: "cursor-abc", limit: 20 }),
    );

    const calledUrl: string = mockFetch.mock.calls[0][0] as string;
    expect(calledUrl).toContain("cursor=cursor-abc");
  });
});

describe("useCreatePatientInline", () => {
  beforeEach(() => vi.clearAllMocks());

  it("maps UI 'telefono' → BE 'phone' channel", async () => {
    mockFetch.mockResolvedValueOnce({
      patient_id: "new-pid",
      name_masked: "A*** R***",
      phone_masked: "+54 ***",
      is_duplicate: false,
      created_at: "2026-01-01T00:00:00Z",
    });

    const { result } = renderHook(
      () => useCreatePatientInline({ tenantId: "t-1" }),
      { wrapper },
    );

    await act(async () => {
      await result.current.mutateAsync({
        name: "Ana Rodríguez",
        phone: "+5491112345678",
        email: null,
        uiChannel: "telefono",
        note: null,
      });
    });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body.channel).toBe("phone"); // NOT "telefono"
    expect(body.name).toBe("Ana Rodríguez");
  });

  it("maps UI 'walk_in' → BE 'walk_in' channel unchanged", async () => {
    mockFetch.mockResolvedValueOnce({
      patient_id: "new-pid-2",
      name_masked: "B*** L***",
      phone_masked: null,
      is_duplicate: false,
      created_at: "2026-01-01T00:00:00Z",
    });

    const { result } = renderHook(
      () => useCreatePatientInline({ tenantId: "t-1" }),
      { wrapper },
    );

    await act(async () => {
      await result.current.mutateAsync({
        name: "Beatriz López",
        phone: null,
        email: null,
        uiChannel: "walk_in",
        note: null,
      });
    });

    const body = JSON.parse(mockFetch.mock.calls[0][1].body as string) as Record<string, unknown>;
    expect(body.channel).toBe("walk_in");
  });

  it("returns isDuplicate=true when BE signals duplicate phone (RN-9)", async () => {
    mockFetch.mockResolvedValueOnce({
      patient_id: "existing-pid",
      name_masked: "C*** M***",
      phone_masked: "+54 ***",
      is_duplicate: true,
      created_at: "2026-01-01T00:00:00Z",
    });

    const { result } = renderHook(
      () => useCreatePatientInline({ tenantId: "t-1" }),
      { wrapper },
    );

    let response: { isDuplicate: boolean; patientId: string } | undefined;
    await act(async () => {
      response = await result.current.mutateAsync({
        name: "Carlos Méndez",
        phone: "+5491122334455",
        email: null,
        uiChannel: "walk_in",
        note: null,
      });
    });

    expect(response?.isDuplicate).toBe(true);
    expect(response?.patientId).toBe("existing-pid");
  });
});
