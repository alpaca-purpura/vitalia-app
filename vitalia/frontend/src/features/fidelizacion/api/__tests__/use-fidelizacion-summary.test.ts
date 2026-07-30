/**
 * use-fidelizacion-summary — TDD RED tests.
 *
 * Tests run BEFORE implementation (RED → GREEN per .claude/rules/tdd-mandatory.md).
 *
 * downstream-regression-na: brand-local FE feature; no cross-brand consumers
 */

import { renderHook, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

// Mock Clerk
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


// Mock vitaliaFetch
vi.mock("@/lib/fetch-client", () => ({
  vitaliaFetch: vi.fn(),
}));

import { vitaliaFetch } from "@/lib/fetch-client";
import { useFidelizacionSummary } from "../use-fidelizacion-summary";
import type { FidelizacionSummaryResponse } from "../../types/fidelizacion-summary";

const mockSummary: FidelizacionSummaryResponse = {
  patientsInFollowup: 42,
  nearAbandonment: 7,
  returnRate: 0.68,
  reEngagedThisPeriod: 12,
  npsAverage: 8.4,
  npsResponsesCount: 35,
  trendVsPreviousPeriod: {
    patientsInFollowup: 5,
    nearAbandonment: -2,
    returnRate: 0.05,
    reEngagedThisPeriod: 3,
    npsAverage: 0.2,
  },
};

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
}

describe("useFidelizacionSummary", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("returns loading state initially", () => {
    vi.mocked(vitaliaFetch).mockResolvedValue(mockSummary);

    const { result } = renderHook(() => useFidelizacionSummary("30d"), {
      wrapper: createWrapper(),
    });

    expect(result.current.isPending).toBe(true);
  });

  it("returns summary data on success", async () => {
    vi.mocked(vitaliaFetch).mockResolvedValue(mockSummary);

    const { result } = renderHook(() => useFidelizacionSummary("30d"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockSummary);
  });

  it("calls correct endpoint with period param", async () => {
    vi.mocked(vitaliaFetch).mockResolvedValue(mockSummary);

    const { result } = renderHook(() => useFidelizacionSummary("7d"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(vitaliaFetch).toHaveBeenCalledWith(
      expect.stringContaining("/api/v1/vitalia/fidelization/summary"),
      expect.objectContaining({ token: expect.any(String) }),
    );
  });

  it("returns error state on fetch failure", async () => {
    vi.mocked(vitaliaFetch).mockRejectedValue(new Error("API error"));

    const { result } = renderHook(() => useFidelizacionSummary("30d"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
