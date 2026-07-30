// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * use-frozen-leads.test.ts — RED-first tests for useFrozenLeads and useReactivateLead (T-FE-3).
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: vi.fn().mockReturnValue("tenant-frozen-test"),
}));
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(),
  ApiError: class extends Error {
    status: number;
    constructor(msg: string, status = 500) {
      super(msg);
      this.name = "ApiError";
      this.status = status;
    }
  },
}));

import { fetchClient } from "@/lib/api/fetchClient";
import { useTenantId } from "@/hooks/useTenantId";
import { useFrozenLeads, useReactivateLead } from "../frozen";

const MOCK_FROZEN = {
  recienCongelados: [
    {
      id: "lead-010",
      tenantId: "tenant-frozen-test",
      name: "Lucía R███",
      lastStage: "calificando",
      frozenReason: "inactividad_lead",
      frozenAt: "2026-05-28T10:00:00Z",
      channel: "whatsapp",
      score: 32,
      closureReason: null,
      reactivationCohortAt: null,
    },
  ],
  decidioNo: [
    {
      id: "lead-012",
      tenantId: "tenant-frozen-test",
      name: "Iván S███",
      lastStage: "plan_presentado",
      frozenReason: null,
      frozenAt: null,
      channel: null,
      score: null,
      closureReason: "precio",
      reactivationCohortAt: "2026-08-28T10:00:00Z",
    },
  ],
};

function wrapper() {
  const qc = new QueryClient({
    defaultOptions: {
      queries: { retry: false, retryDelay: 0, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: qc }, children);
}

describe("useFrozenLeads", () => {
  beforeEach(() => {
    vi.mocked(fetchClient).mockReset();
  });

  it("fetches frozen leads → recienCongelados + decidioNo (happy path)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_FROZEN);
    const { result } = renderHook(() => useFrozenLeads(), {
      wrapper: wrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.recienCongelados).toHaveLength(1);
    expect(result.current.data?.decidioNo).toHaveLength(1);
  });

  it("disabled when tenantId=null", () => {
    vi.mocked(useTenantId).mockReturnValueOnce(null);
    const { result } = renderHook(() => useFrozenLeads(), {
      wrapper: wrapper(),
    });
    expect(result.current.fetchStatus).toBe("idle");
  });
});

describe("useReactivateLead", () => {
  beforeEach(() => {
    vi.mocked(fetchClient).mockReset();
  });

  it("happy path: POST /crm/leads/:id/reactivate → returns reactivated lead", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce({
      id: "lead-010",
      stage: "calificando",
      isFrozen: false,
    });
    const { result } = renderHook(() => useReactivateLead(), {
      wrapper: wrapper(),
    });
    act(() => {
      result.current.mutate("lead-010");
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toMatchObject({ isFrozen: false });
  });
});
