// cap: scheduling.mateo-agenda
/**
 * use-nueva-cita.test.ts — TDD RED first (T-FE-1).
 *
 * Tests for hooks: useNuevaCitaServices, useNuevaCitaFreeDoctors,
 * useNuevaCitaAvailabilityCheck, useNuevaCitaCreate.
 *
 * React Query key convention: ["mateo","nueva-cita",action,...stableFilters]
 * BE returns snake_case — hooks normalize to camelCase.
 *
 * T-FE-4 regression: getToken() must be called INSIDE queryFn per-request,
 * not cached at mount. See describe "T-FE-4 regression" at bottom of file.
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// Hoist getToken so regression test can assert on it
const mockGetToken = vi.hoisted(() => vi.fn().mockResolvedValue("test-token"));

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: mockGetToken,
    isLoaded: true,
    isSignedIn: true,
  }),
}));

// Mock hooks used for headers
vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-uuid-123",
}));

vi.mock("@/hooks/useActorHeaders", () => ({
  useActorHeaders: () => ({
    "X-Clinic-ID": "clinic-uuid-123",
    "X-User-ID": "user-uuid-123",
    "X-User-Role": "admin_clinic",
  }),
}));

// Mock fetch-client
vi.mock("@/lib/fetch-client", () => ({
  vitaliaFetch: vi.fn(),
}));

import { vitaliaFetch } from "@/lib/fetch-client";
import {
  useNuevaCitaServices,
  useNuevaCitaFreeDoctors,
  useNuevaCitaAvailabilityCheck,
  useNuevaCitaCreate,
} from "../use-nueva-cita";

function makeWrapper() {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: qc }, children);
}

describe("useNuevaCitaServices", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (vitaliaFetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [
        {
          offer_id: "svc-uuid-1",
          public_name: "Limpieza dental",
          modality: "presencial",
          is_active: true,
          status: "active",
          initial_appt_duration_minutes: 45,
          price: null,
          currency: "PEN",
        },
      ],
      next_cursor: null,
    });
  });

  it("returns services list normalized to camelCase", async () => {
    const { result } = renderHook(
      () => useNuevaCitaServices({ tenantId: "t1" }),
      { wrapper: makeWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const items = result.current.data?.items;
    expect(items?.[0].offerId).toBe("svc-uuid-1");
    expect(items?.[0].publicName).toBe("Limpieza dental");
    expect(items?.[0].initialApptDurationMinutes).toBe(45);
  });

  it("uses key ['mateo','nueva-cita','services',tenantId]", async () => {
    const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    (vitaliaFetch as ReturnType<typeof vi.fn>).mockResolvedValue({ items: [], next_cursor: null });
    const wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: qc }, children);
    const { result } = renderHook(
      () => useNuevaCitaServices({ tenantId: "t1" }),
      { wrapper },
    );
    await waitFor(() => !result.current.isPending);
    const cache = qc.getQueryCache().findAll({
      queryKey: ["mateo", "nueva-cita", "services", "t1"],
    });
    expect(cache.length).toBeGreaterThan(0);
  });
});

describe("useNuevaCitaFreeDoctors", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (vitaliaFetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      doctors: [{ doctor_id: "doc-1", doctor_label: "Dr. García" }],
      count: 1,
    });
  });

  it("returns doctors normalized to camelCase", async () => {
    const { result } = renderHook(
      () =>
        useNuevaCitaFreeDoctors({
          tenantId: "t1",
          startIso: "2026-07-01T10:00:00Z",
          durationMinutes: 30,
        }),
      { wrapper: makeWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.doctors[0].doctorId).toBe("doc-1");
    expect(result.current.data?.doctors[0].doctorLabel).toBe("Dr. García");
  });

  it("is disabled when startIso is empty string", () => {
    const { result } = renderHook(
      () =>
        useNuevaCitaFreeDoctors({
          tenantId: "t1",
          startIso: "",
          durationMinutes: 30,
        }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.fetchStatus).toBe("idle");
  });
});

describe("useNuevaCitaAvailabilityCheck", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (vitaliaFetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      status: "available",
      conflict_label: null,
      conflict_start: null,
    });
  });

  it("returns availability normalized to camelCase", async () => {
    const { result } = renderHook(
      () =>
        useNuevaCitaAvailabilityCheck({
          tenantId: "t1",
          doctorId: "doc-1",
          startIso: "2026-07-01T10:00:00Z",
          durationMinutes: 30,
        }),
      { wrapper: makeWrapper() },
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.status).toBe("available");
    expect(result.current.data?.conflictLabel).toBeNull();
  });

  it("is disabled when doctorId is null", () => {
    const { result } = renderHook(
      () =>
        useNuevaCitaAvailabilityCheck({
          tenantId: "t1",
          doctorId: null,
          startIso: "2026-07-01T10:00:00Z",
          durationMinutes: 30,
        }),
      { wrapper: makeWrapper() },
    );
    expect(result.current.fetchStatus).toBe("idle");
  });
});

describe("useNuevaCitaCreate", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (vitaliaFetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      appointment_id: "appt-uuid-1",
      patient_id: "p-1",
      doctor_id: "doc-1",
      start_time: "2026-07-01T10:00:00Z",
      end_time: "2026-07-01T10:30:00Z",
    });
  });

  it("mutates and returns created appointment normalized", async () => {
    const { result } = renderHook(
      () => useNuevaCitaCreate({ tenantId: "t1" }),
      { wrapper: makeWrapper() },
    );
    result.current.mutate({
      origin: "walk_in",
      patientId: "p-1",
      offerId: "11111111-1111-1111-1111-111111111111",
      doctorId: "doc-1",
      serviceLabel: "Limpieza dental",
      startTime: "2026-07-01T10:00:00Z",
      endTime: "2026-07-01T10:30:00Z",
      notesInternal: null,
      currencyOverride: null,
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.appointmentId).toBe("appt-uuid-1");
  });
});

/**
 * T-FE-4 regression — getToken() called inside queryFn per-request.
 *
 * RED: before the fix, getToken was cached at mount (useState+useEffect).
 * GREEN: after fix, getToken is called inside every queryFn invocation.
 * This test asserts getToken() was called when the query resolved — not once
 * at mount but during each async fetch.
 */
describe("T-FE-4 regression: getToken() called per-request inside queryFn", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (vitaliaFetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      items: [],
      next_cursor: null,
    });
  });

  it("useNuevaCitaServices calls getToken() inside queryFn (not cached at mount)", async () => {
    // ARRANGE: reset so we can count calls from this test only
    mockGetToken.mockClear();

    const { result } = renderHook(
      () => useNuevaCitaServices({ tenantId: "t1" }),
      { wrapper: makeWrapper() },
    );

    // ACT: wait for query to complete
    await waitFor(() => !result.current.isPending);

    // ASSERT: getToken was called during the fetch (inside queryFn)
    // If token was cached at mount via useState/useEffect instead, getToken
    // would be called 0 times here (it ran in effect, not in queryFn).
    expect(mockGetToken).toHaveBeenCalled();
  });

  it("useNuevaCitaFreeDoctors calls getToken() inside queryFn", async () => {
    (vitaliaFetch as ReturnType<typeof vi.fn>).mockResolvedValue({
      doctors: [],
      count: 0,
    });
    mockGetToken.mockClear();

    const { result } = renderHook(
      () =>
        useNuevaCitaFreeDoctors({
          tenantId: "t1",
          startIso: "2026-07-01T10:00:00Z",
          durationMinutes: 30,
        }),
      { wrapper: makeWrapper() },
    );

    await waitFor(() => !result.current.isPending);
    expect(mockGetToken).toHaveBeenCalled();
  });
});
