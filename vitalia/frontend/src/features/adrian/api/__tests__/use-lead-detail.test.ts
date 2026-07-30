// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * use-lead-detail.test.ts — RED-first tests for useLeadDetail and useLeadTimeline (T-FE-3).
 * TDD: tests written FIRST per tdd-mandatory.md.
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
  useTenantId: vi.fn().mockReturnValue("tenant-lead-test"),
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
import { useLeadDetail, useLeadTimeline } from "../lead";

const MOCK_LEAD_DETAIL = {
  lead: {
    // LeadDetailLeadDTO shape — mirrors BE LeadResponse (U2 fix: includes phone/email/assignedDoctorId).
    // isBlacklisted removed: not part of LeadResponse (it was a LeadCardDTO board field).
    id: "lead-001",
    tenantId: "tenant-lead-test",
    name: "María García López",
    email: "maria@example.com",
    phone: "+51 1 234 5678",
    source: "instagram",
    status: "active",
    createdAt: "2026-06-01T10:00:00Z",
    stage: "calificando",
    score: 64,
    temperature: "warm",
    operatedBy: "agent",
    channel: "whatsapp",
    estimatedValue: 8000,
    currency: "PEN",
    serviceInterest: "Ortodoncia",
    buyingSignals: ["urgencia", "presupuesto_ok"],
    stageEnteredAt: "2026-06-03T09:00:00Z",
    isFrozen: false,
    frozenReason: null,
    depositStatus: null,
    version: 1,
    assignedDoctorId: "doc-001",
  },
  scoreBreakdown: [
    { label: "Preguntó precio", delta: 25, icon: null },
    { label: "Respondió rápido", delta: 15, icon: null },
    { label: "Sin agendar 2d", delta: -2, icon: null },
  ],
  // Real BE AutonomyInfo shape (camelized): operatedBy/can/needsOk.
  // (Previously mocked the imagined canDo/needsApproval/currentMode → falso-verde
  //  that hid the Resumen crash; gated now by test_fe_be_contract_parity.py.)
  autonomy: {
    operatedBy: "agent",
    can: ["mover etapa", "agendar", "enviar info"],
    needsOk: ["cobrar", "descuentos"],
  },
};

const MOCK_TIMELINE = {
  events: [
    {
      id: "ev-001",
      kind: "stage_move",
      actor: "agent",
      descriptionEs: "Adrián movió a Calificando",
      occurredAt: "2026-06-03T09:00:00Z",
    },
    {
      id: "ev-002",
      kind: "message",
      actor: "lead",
      descriptionEs: "María preguntó por el precio",
      occurredAt: "2026-06-02T10:00:00Z",
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

describe("useLeadDetail", () => {
  beforeEach(() => {
    vi.mocked(fetchClient).mockReset();
  });

  it("fetches lead detail → lead + scoreBreakdown + autonomy (happy path)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_LEAD_DETAIL);
    const { result } = renderHook(() => useLeadDetail("lead-001"), {
      wrapper: wrapper(),
    });
    expect(result.current.isLoading).toBe(true);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.lead.id).toBe("lead-001");
    expect(result.current.data?.scoreBreakdown).toHaveLength(3);
    expect(result.current.data?.autonomy.operatedBy).toBe("agent");
    expect(result.current.data?.autonomy.can).toContain("mover etapa");
    expect(result.current.data?.autonomy.needsOk).toContain("cobrar");
  });

  it("isError=true on fetch failure", async () => {
    vi.mocked(fetchClient).mockRejectedValueOnce(new Error("Network error"));
    const { result } = renderHook(() => useLeadDetail("lead-001"), {
      wrapper: wrapper(),
    });
    await waitFor(() => expect(result.current.isError).toBe(true), {
      timeout: 5000,
    });
  });

  it("disabled when tenantId=null", () => {
    vi.mocked(useTenantId).mockReturnValueOnce(null);
    const { result } = renderHook(() => useLeadDetail("lead-001"), {
      wrapper: wrapper(),
    });
    expect(result.current.fetchStatus).toBe("idle");
    expect(vi.mocked(fetchClient)).not.toHaveBeenCalled();
  });

  it("disabled when leadId is empty string", () => {
    const { result } = renderHook(() => useLeadDetail(""), {
      wrapper: wrapper(),
    });
    expect(result.current.fetchStatus).toBe("idle");
    expect(vi.mocked(fetchClient)).not.toHaveBeenCalled();
  });
});

describe("useLeadTimeline", () => {
  beforeEach(() => {
    vi.mocked(fetchClient).mockReset();
  });

  it("fetches timeline events (happy path)", async () => {
    vi.mocked(fetchClient).mockResolvedValueOnce(MOCK_TIMELINE);
    const { result } = renderHook(() => useLeadTimeline("lead-001"), {
      wrapper: wrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.events).toHaveLength(2);
    expect(result.current.data?.events[0].kind).toBe("stage_move");
  });

  it("disabled when leadId is empty string", () => {
    const { result } = renderHook(() => useLeadTimeline(""), {
      wrapper: wrapper(),
    });
    expect(result.current.fetchStatus).toBe("idle");
  });
});
