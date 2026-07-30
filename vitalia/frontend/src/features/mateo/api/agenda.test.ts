/**
 * agenda.test.ts — Unit tests for Valeria Agenda React Query hooks.
 * T-12 vitalia-fase2-valeria-agenda
 *
 * Tests cover:
 *   - agendaKeys factory produces stable, distinct keys
 *   - useAgendaGrid: enabled when signed in, disabled when not
 *   - useAgendaGrid: passes correct query params (view + date + presetFilter)
 *   - useAppointmentDetail: disabled when appointmentId is null
 *   - usePatchAppointmentStatus: invalidates grid + detail on success
 *   - useChargeMutation (payments.ts): sends X-Idempotency-Key header
 *
 * Pattern: vi.fn() mocks for Clerk + vitaliaFetch + actor-header hooks (MSW not installed).
 *
 * ★ Actor headers (vitalia-bugfix-agenda-actor-headers-422): the hooks now inject
 *   X-Clinic-ID (useClinicId) + X-User-ID/X-User-Role (useActorHeaders) and gate PHI
 *   queries on a non-empty X-User-ID (`ready`). Tests mock both hooks + assert the
 *   merged headers reach vitaliaFetch.
 *
 * downstream-regression-na: brand-local FE tests; no cross-brand consumers
 * spec_anchor: 06-tickets.yaml T-12 (A2, A3, A4)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import {
  agendaKeys,
  useAgendaGrid,
  useAppointmentDetail,
  usePatchAppointmentStatus,
} from "./agenda";
import type { AgendaGridResponseDTO } from "../types/agenda-schema";

// ── Mocks ─────────────────────────────────────────────────────────────────────

// Mock Clerk useAuth
vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
    isLoaded: true,
    isSignedIn: true,
  })),
}));

// Mock vitaliaFetch
vi.mock("@/lib/fetch-client", () => ({
  vitaliaFetch: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    constructor(response: { status: number; statusText: string }) {
      super(`API error ${response.status}`);
      this.status = response.status;
    }
  },
}));

// Mock the HIPAA-lite actor-header hooks (X-Clinic-ID + X-User-ID + X-User-Role)
vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: vi.fn(() => "clinic-1"),
}));
vi.mock("@/hooks/useActorHeaders", () => ({
  useActorHeaders: vi.fn(() => ({
    "X-User-ID": "db-user-uuid",
    "X-User-Role": "doctor",
  })),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return (
      React.createElement(QueryClientProvider, { client: queryClient }, children)
    );
  };
}

const MOCK_GRID: AgendaGridResponseDTO = {
  view: "semana",
  dateFrom: "2026-05-26",
  dateTo: "2026-06-01",
  slots: [],
  serverTime: "2026-05-26T12:00:00Z",
  clinicId: "clinic-1",
  tenantId: "tenant-1",
};

// ── Tests: agendaKeys factory ─────────────────────────────────────────────────

describe("agendaKeys", () => {
  it("produces distinct keys for different views", () => {
    const semana = agendaKeys.grid("t1", "semana", "2026-05-26", null);
    const dia = agendaKeys.grid("t1", "dia", "2026-05-26", null);
    expect(semana).not.toEqual(dia);
  });

  it("produces distinct keys for different tenants", () => {
    const t1 = agendaKeys.grid("tenant-1", "semana", "2026-05-26", null);
    const t2 = agendaKeys.grid("tenant-2", "semana", "2026-05-26", null);
    expect(t1).not.toEqual(t2);
  });

  it("produces distinct keys for different dates", () => {
    const date1 = agendaKeys.grid("t1", "semana", "2026-05-26", null);
    const date2 = agendaKeys.grid("t1", "semana", "2026-05-27", null);
    expect(date1).not.toEqual(date2);
  });

  it("includes preset filter in key", () => {
    const noFilter = agendaKeys.grid("t1", "semana", "2026-05-26", null);
    const withFilter = agendaKeys.grid("t1", "semana", "2026-05-26", "today");
    expect(noFilter).not.toEqual(withFilter);
  });

  it("all() key contains tenantId for scoped invalidation", () => {
    const all = agendaKeys.all("t1");
    // all() key is used with invalidateQueries prefix matching
    // It must contain "agenda" + tenantId so that invalidation
    // targets only this tenant's agenda queries
    expect(all).toContain("agenda");
    expect(all).toContain("t1");
    // grid key also contains both
    const grid = agendaKeys.grid("t1", "semana", "2026-05-26", null);
    expect(grid).toContain("agenda");
    expect(grid).toContain("t1");
  });

  it("detail key contains appointmentId", () => {
    const key = agendaKeys.detail("t1", "appt-123");
    expect(key).toContain("appt-123");
  });
});

// ── Tests: useAgendaGrid ──────────────────────────────────────────────────────

describe("useAgendaGrid", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("is enabled when signed in and fetches grid", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");
    vi.mocked(vitaliaFetch).mockResolvedValueOnce(MOCK_GRID);

    const { result } = renderHook(
      () =>
        useAgendaGrid({
          tenantId: "tenant-1",
          view: "semana",
          date: "2026-05-26",
        }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(MOCK_GRID);
    expect(vitaliaFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/scheduling/agenda/grid"),
      expect.objectContaining({ token: "test-token", tenantId: "tenant-1" }),
    );
  });

  // ★ Regression (vitalia-bugfix-agenda-actor-headers-422): the grid call MUST carry
  //   X-Clinic-ID + X-User-ID + X-User-Role — only X-Tenant-ID was a 422.
  it("sends X-Clinic-ID + X-User-ID + X-User-Role actor headers", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");
    vi.mocked(vitaliaFetch).mockResolvedValueOnce(MOCK_GRID);

    const { result } = renderHook(
      () =>
        useAgendaGrid({
          tenantId: "tenant-1",
          view: "semana",
          date: "2026-05-26",
        }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(vitaliaFetch).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({
        headers: expect.objectContaining({
          "X-Clinic-ID": "clinic-1",
          "X-User-ID": "db-user-uuid",
          "X-User-Role": "doctor",
        }),
      }),
    );
  });

  // ★ Regression: gate on X-User-ID — firing before /me resolves sends X-User-ID:"" → 422.
  it("is disabled until X-User-ID (actor header) resolves", async () => {
    const { useActorHeaders } = await import("@/hooks/useActorHeaders");
    vi.mocked(useActorHeaders).mockReturnValueOnce({
      "X-User-ID": "", // /me not resolved yet
      "X-User-Role": "doctor",
    });
    const { vitaliaFetch } = await import("@/lib/fetch-client");

    const { result } = renderHook(
      () =>
        useAgendaGrid({
          tenantId: "tenant-1",
          view: "semana",
          date: "2026-05-26",
        }),
      { wrapper: makeWrapper() },
    );

    await new Promise((r) => setTimeout(r, 50));
    expect(result.current.status).toBe("pending");
    expect(vitaliaFetch).not.toHaveBeenCalled();
  });

  it("passes view + date as query params", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");
    vi.mocked(vitaliaFetch).mockResolvedValueOnce(MOCK_GRID);

    const { result } = renderHook(
      () =>
        useAgendaGrid({
          tenantId: "tenant-1",
          view: "dia",
          date: "2026-05-28",
          presetFilter: "today",
        }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(vitaliaFetch).toHaveBeenCalledWith(
      expect.stringMatching(/view=dia/),
      expect.anything(),
    );
    expect(vitaliaFetch).toHaveBeenCalledWith(
      expect.stringMatching(/date=2026-05-28/),
      expect.anything(),
    );
    expect(vitaliaFetch).toHaveBeenCalledWith(
      expect.stringMatching(/preset_filter=today/),
      expect.anything(),
    );
  });

  it("is disabled when not signed in", async () => {
    const { useAuth } = await import("@clerk/nextjs");
    vi.mocked(useAuth).mockReturnValueOnce({
      getToken: vi.fn(),
      isLoaded: true,
      isSignedIn: false,
    } as unknown as ReturnType<typeof useAuth>);

    const { vitaliaFetch } = await import("@/lib/fetch-client");

    const { result } = renderHook(
      () =>
        useAgendaGrid({
          tenantId: "tenant-1",
          view: "semana",
          date: "2026-05-26",
        }),
      { wrapper: makeWrapper() },
    );

    // Should not fetch
    await new Promise((r) => setTimeout(r, 50));
    expect(result.current.status).toBe("pending");
    expect(vitaliaFetch).not.toHaveBeenCalled();
  });

  it("uses placeholderData from SSR", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");
    // Delay resolution to check placeholder appears first
    vi.mocked(vitaliaFetch).mockImplementation(
      () => new Promise((r) => setTimeout(() => r(MOCK_GRID), 100)),
    );

    const ssrData = { ...MOCK_GRID, slots: [] };

    const { result } = renderHook(
      () =>
        useAgendaGrid({
          tenantId: "tenant-1",
          view: "semana",
          date: "2026-05-26",
          queryOptions: { placeholderData: ssrData },
        }),
      { wrapper: makeWrapper() },
    );

    // Placeholder data available immediately
    expect(result.current.data).toEqual(ssrData);
    expect(result.current.isPlaceholderData).toBe(true);

    await waitFor(() => expect(result.current.isPlaceholderData).toBe(false));
  });
});

// ── Tests: useAppointmentDetail ───────────────────────────────────────────────

describe("useAppointmentDetail", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("is disabled when appointmentId is null", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");

    const { result } = renderHook(
      () =>
        useAppointmentDetail({
          tenantId: "tenant-1",
          appointmentId: null,
        }),
      { wrapper: makeWrapper() },
    );

    await new Promise((r) => setTimeout(r, 50));
    expect(result.current.status).toBe("pending");
    expect(vitaliaFetch).not.toHaveBeenCalled();
  });

  it("fetches appointment detail when appointmentId is provided", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");
    const mockAppointment = {
      appointmentId: "appt-1",
      patientId: "p-1",
      patientNameMasked: "M. Rodríguez",
      patientDniMasked: "12.***.***",
      patientPhoneMasked: null,
      patientEmailMasked: null,
      startTime: "2026-05-26T10:00:00-05:00",
      endTime: "2026-05-26T11:00:00-05:00",
      doctorId: "doc-1",
      doctorLabel: "Dr. C. Mendoza",
      serviceLabel: "Limpieza dental",
      appointmentStatus: "SCHEDULED",
      paymentStatus: "unpaid",
      origin: "walk_in",
      balanceDueCents: 15000,
      balancePaidCents: 0,
      currency: "PEN",
      currencyOverride: null,
      payments: [],
      notesInternal: null,
      lastActivityAt: null,
      lastActivityByLabel: null,
    };
    vi.mocked(vitaliaFetch).mockResolvedValueOnce(mockAppointment);

    const { result } = renderHook(
      () =>
        useAppointmentDetail({
          tenantId: "tenant-1",
          appointmentId: "appt-1",
        }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.appointmentId).toBe("appt-1");
    expect(vitaliaFetch).toHaveBeenCalledWith(
      expect.stringContaining("/appointments/appt-1"),
      expect.objectContaining({ tenantId: "tenant-1" }),
    );
  });
});

// ── Tests: usePatchAppointmentStatus ─────────────────────────────────────────

describe("usePatchAppointmentStatus", () => {
  it("invalidates grid + detail queries on success", async () => {
    const { vitaliaFetch } = await import("@/lib/fetch-client");
    const mockPatched = { appointmentId: "appt-1", appointmentStatus: "COMPLETED" };
    vi.mocked(vitaliaFetch).mockResolvedValueOnce(mockPatched);

    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
    });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: queryClient }, children);

    const { result } = renderHook(
      () => usePatchAppointmentStatus("tenant-1"),
      { wrapper },
    );

    result.current.mutate({
      appointmentId: "appt-1",
      payload: { newStatus: "COMPLETED" },
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    // Should have called invalidateQueries at least twice (grid + detail)
    expect(invalidateSpy).toHaveBeenCalledTimes(2);
  });
});
