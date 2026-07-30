// cap: scheduling.mateo-agenda
/**
 * use-service-day.contract.test.ts — FE↔BE contract test for useServiceDayStrips.
 * T-D3 vitalia-fase2-mateo-nueva-cita delta.
 *
 * Contract: asserts that the hook requests
 *   GET /api/v1/scheduling/availability/service-day?serviceId={id}&date=YYYY-MM-DD
 * and that the normalization of BE snake_case → FE camelCase is correct.
 *
 * BE DTO (T-D1):
 *   { service_id, date, doctors: [{ doctor_id, doctor_label, blocks: [{kind,start,end}] }] }
 * FE normalized shape:
 *   { serviceId, dateLocal, doctors: [{ doctorId, doctorLabel, blocks: [{kind,startTime,endTime}] }] }
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * spec_anchor: 03-arch-delta-availability.md § 4 + § 7 seam_coverage
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import * as React from "react";

// ── Mock fetch-client ──────────────────────────────────────────────────────

const mockVitaliaFetch = vi.fn();
vi.mock("@/lib/fetch-client", () => ({
  vitaliaFetch: (...args: unknown[]) => mockVitaliaFetch(...args),
}));

// ── Mock Clerk useAuth ─────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

// ── Mock useClinicId + useActorHeaders ─────────────────────────────────────

vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-001",
}));
vi.mock("@/hooks/useActorHeaders", () => ({
  useActorHeaders: () => ({ "X-Actor-Role": "admin" }),
}));

// ── Import hook after mocks ────────────────────────────────────────────────

const { useServiceDayStrips } = await import("../use-availability");

// ── Test wrapper ───────────────────────────────────────────────────────────

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return React.createElement(QueryClientProvider, { client: qc }, children);
}

// ── BE snake_case mock payload ─────────────────────────────────────────────

const BE_PAYLOAD = {
  service_id: "svc-limpieza-001",
  date: "2026-06-22",
  doctors: [
    {
      doctor_id: "00000000-0000-0000-0000-000000000001",
      doctor_label: "Dr. Carlos Ortiz",
      blocks: [
        {
          kind: "working_hours",
          start: "2026-06-22T08:00:00Z",
          end: "2026-06-22T17:00:00Z",
        },
        {
          kind: "busy",
          start: "2026-06-22T10:00:00Z",
          end: "2026-06-22T10:30:00Z",
        },
      ],
    },
    {
      doctor_id: "00000000-0000-0000-0000-000000000002",
      doctor_label: "Dra. Lucía Vega",
      blocks: [],
    },
  ],
};

describe("useServiceDayStrips — FE↔BE contract", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockVitaliaFetch.mockResolvedValue(BE_PAYLOAD);
  });

  it("requests the correct endpoint URL with serviceId + date params", async () => {
    const { result } = renderHook(
      () =>
        useServiceDayStrips({
          tenantId: "t-1",
          serviceId: "svc-limpieza-001",
          dateLocal: "2026-06-22",
        }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(mockVitaliaFetch).toHaveBeenCalledOnce();
    const [url, opts] = mockVitaliaFetch.mock.calls[0] as [string, Record<string, unknown>];

    // Contract: URL path + params
    expect(url).toContain("/api/v1/scheduling/availability/service-day");
    expect(url).toContain("serviceId=svc-limpieza-001");
    expect(url).toContain("date=2026-06-22");

    // Contract: auth headers present
    expect(opts.token).toBe("test-token");
    expect(opts.tenantId).toBe("t-1");
    expect((opts.headers as Record<string, string>)["X-Clinic-ID"]).toBe("clinic-001");
  });

  it("normalizes BE snake_case response to FE camelCase shape", async () => {
    const { result } = renderHook(
      () =>
        useServiceDayStrips({
          tenantId: "t-1",
          serviceId: "svc-limpieza-001",
          dateLocal: "2026-06-22",
        }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const data = result.current.data!;

    // Top-level normalization
    expect(data.serviceId).toBe("svc-limpieza-001"); // service_id → serviceId
    expect(data.dateLocal).toBe("2026-06-22");        // date → dateLocal

    // First doctor
    const d1 = data.doctors[0]!;
    expect(d1.doctorId).toBe("00000000-0000-0000-0000-000000000001"); // doctor_id → doctorId
    expect(d1.doctorLabel).toBe("Dr. Carlos Ortiz");                  // doctor_label → doctorLabel

    // Blocks normalization: start → startTime, end → endTime
    expect(d1.blocks).toHaveLength(2);
    expect(d1.blocks[0]!.startTime).toBe("2026-06-22T08:00:00Z"); // start → startTime
    expect(d1.blocks[0]!.endTime).toBe("2026-06-22T17:00:00Z");   // end → endTime
    expect(d1.blocks[0]!.kind).toBe("working_hours");
    expect(d1.blocks[1]!.kind).toBe("busy");

    // Second doctor with empty blocks (sin horario)
    const d2 = data.doctors[1]!;
    expect(d2.blocks).toHaveLength(0);
  });

  it("is disabled when serviceId is null (fail-closed)", async () => {
    const { result } = renderHook(
      () =>
        useServiceDayStrips({
          tenantId: "t-1",
          serviceId: null,
          dateLocal: "2026-06-22",
        }),
      { wrapper },
    );

    // Should remain pending/idle, never call fetch
    await new Promise((r) => setTimeout(r, 50));
    expect(mockVitaliaFetch).not.toHaveBeenCalled();
    expect(result.current.isPending).toBe(true); // disabled query = pending
  });

  it("is disabled when dateLocal is empty (fail-closed)", async () => {
    const { result } = renderHook(
      () =>
        useServiceDayStrips({
          tenantId: "t-1",
          serviceId: "svc-001",
          dateLocal: "",
        }),
      { wrapper },
    );

    await new Promise((r) => setTimeout(r, 50));
    expect(mockVitaliaFetch).not.toHaveBeenCalled();
    expect(result.current.isPending).toBe(true);
  });

  it("returns doctors:[] on empty response (empty_state)", async () => {
    mockVitaliaFetch.mockResolvedValue({
      service_id: "svc-001",
      date: "2026-06-22",
      doctors: [],
    });

    const { result } = renderHook(
      () =>
        useServiceDayStrips({
          tenantId: "t-1",
          serviceId: "svc-001",
          dateLocal: "2026-06-22",
        }),
      { wrapper },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.doctors).toHaveLength(0);
  });
});
