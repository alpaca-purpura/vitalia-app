// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * use-create-lead.test.ts — RED-first tests for useCreateLead (T-FE-3).
 * TDD: tests FIRST per tdd-mandatory.md.
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
  useTenantId: vi.fn().mockReturnValue("tenant-create-test"),
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
import { useCreateLead } from "../create-lead";

const MOCK_CREATED_LEAD = {
  id: "lead-new-abc123",
  tenantId: "tenant-create-test",
  name: "Luis T███",
  stage: "interesado",
  score: 10,
  temperature: "cold",
  operatedBy: "agent",
  channel: "whatsapp",
  estimatedValue: null,
  currency: "PEN",
  buyingSignals: [],
  isFrozen: false,
  frozenReason: null,
  depositStatus: null,
  version: 1,
  stageEnteredAt: "2026-06-03T10:00:00Z",
};

function wrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    createElement(QueryClientProvider, { client: qc }, children);
}

describe("useCreateLead", () => {
  beforeEach(() => {
    vi.mocked(fetchClient).mockReset();
  });

  it("happy path: POST /crm/leads → returns created lead (SC-nuevo)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_CREATED_LEAD);
    const { result } = renderHook(() => useCreateLead(), { wrapper: wrapper() });
    act(() => {
      result.current.mutate({
        name: "Luis Torres",
        channel: "whatsapp",
        phone: "+51999111222",
        email: null,
        stage: "interesado",
        serviceInterest: "Ortodoncia",
        tags: [],
        notes: "",
      });
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.id).toBe("lead-new-abc123");
    expect(result.current.data?.stage).toBe("interesado");
  });

  it("validation error → mutation rejects (422)", async () => {
    const err = new Error("API error 422") as Error & { status: number };
    err.name = "ApiError";
    err.status = 422;
    vi.mocked(fetchClient).mockRejectedValueOnce(err);
    const { result } = renderHook(() => useCreateLead(), { wrapper: wrapper() });
    act(() => {
      result.current.mutate({
        name: "",
        channel: "whatsapp",
        phone: null,
        email: null,
        stage: "interesado",
        serviceInterest: null,
        tags: [],
        notes: "",
      });
    });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error & { status: number }).status).toBe(422);
  });
});
