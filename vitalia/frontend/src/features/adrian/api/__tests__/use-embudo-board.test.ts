// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * use-embudo-board.test.ts — RED-first tests for useEmbudoBoard hook (T-FE-2).
 * TDD: tests FIRST, implementation follows.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
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
  useTenantId: vi.fn().mockReturnValue("tenant-embudo-test"),
}));
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(msg: string, status = 500) { super(msg); this.status = status; }
  },
}));

import { fetchClient } from "@/lib/api/fetchClient";
import { useTenantId } from "@/hooks/useTenantId";
import { useEmbudoBoard } from "../embudo-board";

const MOCK_BOARD = {
  columns: [
    {
      stage: "interesado", label: "Interesado", count: 3,
      sumValue: 23000, currency: "PEN", overSlaCount: 1,
      leads: [{ id: "lead-001", name: "María G.", stage: "interesado", score: 48,
        temperature: "warm", operatedBy: "agent", channel: "whatsapp",
        estimatedValue: 7000, currency: "PEN", buyingSignals: ["pregunto_precio"],
        stageEnteredAt: "2026-05-27T10:00:00Z", version: 1,
        tenantId: "tenant-embudo-test" }],
    },
  ],
  kpis: { totalActive: 11, adrianCount: 9, humanCount: 2, hotCount: 3,
    warmCount: 5, coldCount: 3, avgScore: 58, depositRate: 0.18, frozenCount: 2 },
};

function wrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false, retryDelay: 0, gcTime: 0 }, mutations: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: qc }, children);
}

describe("useEmbudoBoard", () => {
  beforeEach(() => { vi.mocked(fetchClient).mockReset(); });

  it("fetches board data → columns + kpis (happy path)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_BOARD);
    const { result } = renderHook(() => useEmbudoBoard({}), { wrapper: wrapper() });
    expect(result.current.isLoading).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.columns).toHaveLength(1);
    expect(result.current.data?.kpis.totalActive).toBe(11);
  });

  it("isError=true on fetch failure", async () => {
    vi.mocked(fetchClient).mockRejectedValueOnce(new Error("Network error"));
    const { result } = renderHook(() => useEmbudoBoard({}), { wrapper: wrapper() });
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });

  it("disabled (idle) when tenantId=null", () => {
    vi.mocked(useTenantId).mockReturnValueOnce(null);
    const { result } = renderHook(() => useEmbudoBoard({}), { wrapper: wrapper() });
    expect(result.current.fetchStatus).toBe("idle");
    expect(vi.mocked(fetchClient)).not.toHaveBeenCalled();
  });
});
