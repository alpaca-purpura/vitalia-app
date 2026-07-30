// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * use-lead-stage-mutation.test.ts — RED-first tests for useLeadStageMutation (T-FE-2).
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("mock-token"), isLoaded: true, isSignedIn: true }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: vi.fn().mockReturnValue("tenant-stage-test") }));
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(),
  ApiError: class extends Error {
    status: number;
    body: unknown;
    constructor(response: { status: number } | string, body?: unknown) {
      super(typeof response === "string" ? response : `API error ${(response as { status: number }).status}`);
      this.name = "ApiError";
      this.status = typeof response === "object" ? (response as { status: number }).status : 500;
      this.body = body;
    }
  },
}));

import { fetchClient } from "@/lib/api/fetchClient";
import { useLeadStageMutation } from "../lead-stage-mutation";

interface ApiErrorLike { status: number; }

const MOCK_SUCCESS = {
  lead: { id: "lead-001", stage: "calificando", version: 2 },
  transition: { id: "trans-001", fromStage: "interesado", toStage: "calificando",
    triggeredBy: "manual_override", occurredAt: "2026-06-03T10:00:00Z" },
};

function wrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: qc }, children);
}

// Helper to create errors with status
function makeApiError(status: number): Error & ApiErrorLike {
  const err = new Error(`API error ${status}`) as Error & ApiErrorLike;
  err.name = "ApiError";
  err.status = status;
  return err;
}

describe("useLeadStageMutation", () => {
  beforeEach(() => { vi.mocked(fetchClient).mockReset(); });

  it("happy path: PATCH /stage → 200 returns transition (SC-1b)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_SUCCESS);
    const { result } = renderHook(() => useLeadStageMutation(), { wrapper: wrapper() });
    act(() => {
      result.current.mutate({
        leadId: "lead-001", toStage: "calificando",
        reason: "coordiné por teléfono", version: 1, triggeredBy: "manual_override",
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.transition.toStage).toBe("calificando");
  });

  it("409 conflict → mutation rejects with status 409 (SC-5)", async () => {
    vi.mocked(fetchClient).mockRejectedValueOnce(makeApiError(409));
    const { result } = renderHook(() => useLeadStageMutation(), { wrapper: wrapper() });
    act(() => {
      result.current.mutate({ leadId: "lead-001", toStage: "calificando", version: 1 });
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as unknown as ApiErrorLike).status).toBe(409);
  });

  it("422 invalid skip → mutation rejects with status 422 (SC-2)", async () => {
    vi.mocked(fetchClient).mockRejectedValueOnce(makeApiError(422));
    const { result } = renderHook(() => useLeadStageMutation(), { wrapper: wrapper() });
    act(() => {
      result.current.mutate({ leadId: "lead-001", toStage: "reservado", version: 1 });
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as unknown as ApiErrorLike).status).toBe(422);
  });

  // ★ EMBUDO-INBOX-SYNC-FIX (2026-06-11): moving a lead stage in Embudo must
  // refresh the Inbox conversation thread, which renders lead.stage from the
  // crm-shared key ['crm','conversation',id]. Regression guard: onSuccess must
  // cross-invalidate the Inbox namespaces, not only the board/detail.
  it("onSuccess cross-invalidates Inbox + Embudo namespaces (embudo↔inbox sync)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_SUCCESS);
    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(qc, "invalidateQueries");
    const localWrapper = ({ children }: { children: React.ReactNode }) =>
      createElement(QueryClientProvider, { client: qc }, children);

    const { result } = renderHook(() => useLeadStageMutation(), {
      wrapper: localWrapper,
    });
    act(() => {
      result.current.mutate({
        leadId: "lead-001",
        toStage: "calificando",
        reason: "coordiné por teléfono",
        version: 1,
        triggeredBy: "manual_override",
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const invalidatedKeys = invalidateSpy.mock.calls.map((c) => c[0]?.queryKey);
    // The renderered Inbox thread key namespace + the inbox list namespace
    expect(invalidatedKeys).toContainEqual(["crm", "conversation"]);
    expect(invalidatedKeys).toContainEqual(["adrian", "inbox"]);
  });
});
