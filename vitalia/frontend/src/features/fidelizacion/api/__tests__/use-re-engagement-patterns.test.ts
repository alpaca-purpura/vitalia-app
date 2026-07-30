/**
 * use-re-engagement-patterns — TDD RED tests.
 *
 * downstream-regression-na: brand-local FE feature; no cross-brand consumers
 */

import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    userId: "mock-user-id",
    isLoaded: true,
    isSignedIn: true,
    orgId: "mock-tenant-id",
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("@/lib/fetch-client", () => ({
  vitaliaFetch: vi.fn(),
}));

import { vitaliaFetch } from "@/lib/fetch-client";
import { useReEngagementPatterns } from "../use-re-engagement-patterns";
import type { PatternRow } from "../../types/re-engagement";

const mockRow: PatternRow = {
  reEngagementEventId: "evt-1",
  patientId: "pat-1",
  patientName: "María García",
  pattern: "multi_session",
  urgency: "alert",
  patternData: {
    kind: "multi_session",
    offerLabel: "Tratamiento ortodóncico",
    sessionsCompleted: 3,
    sessionsExpected: 6,
    gapDays: 45,
    lastSessionDate: "2026-04-01T00:00:00Z",
    doctorName: "Dra. López",
  },
  acciones: [
    { id: "send_reminder", enabled: true, disabledReason: null },
    { id: "pause_patient", enabled: true, disabledReason: null },
  ],
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
}

describe("useReEngagementPatterns", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns rows on success", async () => {
    vi.mocked(vitaliaFetch).mockResolvedValue({ rows: [mockRow] });

    const { result } = renderHook(
      () =>
        useReEngagementPatterns({
          pattern: "multi_session",
          period: "30d",
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.rows).toHaveLength(1);
    expect(result.current.data?.rows[0].pattern).toBe("multi_session");
  });

  it("passes filter params to API", async () => {
    vi.mocked(vitaliaFetch).mockResolvedValue({ rows: [] });

    const { result } = renderHook(
      () =>
        useReEngagementPatterns({
          pattern: "follow_up",
          period: "7d",
          urgency: ["critical"],
        }),
      { wrapper: createWrapper() },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vitaliaFetch).toHaveBeenCalledWith(
      expect.stringContaining(
        "/api/v1/vitalia/fidelization/re-engagement/patterns",
      ),
      expect.objectContaining({ token: expect.any(String) }),
    );
  });
});
