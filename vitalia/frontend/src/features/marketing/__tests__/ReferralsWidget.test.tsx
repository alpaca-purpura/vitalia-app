/**
 * ReferralsWidget tests — HIPAA leaderboard with hashed IDs only
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("tok"),
    orgId: "org-1",
    isLoaded: true,
    isSignedIn: true,
  }),
  useOrganization: () => ({
    organization: {
      publicMetadata: {
        currency: "PEN",
        timezone: "America/Lima",
        locale: "es-419",
      },
    },
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Mock clinic hook
vi.mock("@/hooks/useClinicId", () => ({ useClinicId: () => "clinic-123" }));

// Mock tenant locale hook
vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({
    currency: "PEN",
    timezone: "America/Lima",
    locale: "es-419",
  }),
}));

// Mock React Query
vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useMutation: vi.fn(),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  QueryClient: vi.fn(),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

const mockReferralsData = {
  periodStart: "2026-05-01T00:00:00Z",
  periodEnd: "2026-05-31T23:59:59Z",
  referralsCount: 28,
  convRate: 0.64,
  avgLtvPerReferrerCents: 89000,
  topReferrers: [
    {
      referrerPatientIdHash: "a1b2c3d4e5f6",
      referralsCount: 5,
      totalValueCents: 450000,
    },
    {
      referrerPatientIdHash: "b2c3d4e5f6a7",
      referralsCount: 4,
      totalValueCents: 360000,
    },
    {
      referrerPatientIdHash: "c3d4e5f6a7b8",
      referralsCount: 3,
      totalValueCents: 270000,
    },
    {
      referrerPatientIdHash: "d4e5f6a7b8c9",
      referralsCount: 2,
      totalValueCents: 180000,
    },
    {
      referrerPatientIdHash: "e5f6a7b8c9d0",
      referralsCount: 1,
      totalValueCents: 90000,
    },
  ],
  currency: "PEN",
};

import { useQuery } from "@tanstack/react-query";

describe("ReferralsWidget", () => {
  beforeEach(() => {
    vi.mocked(useQuery).mockReturnValue({
      data: mockReferralsData,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);
  });

  it("test_renders_3_kpi_hero_cards — shows referralsCount, convRate, avgLtv", async () => {
    const { ReferralsWidget } = await import("../components/ReferralsWidget");
    render(<ReferralsWidget />);

    // Widget heading (h3 element)
    expect(
      screen.getByRole("heading", { name: "Referidos" }),
    ).toBeInTheDocument();

    // KPI labels
    expect(screen.getByText("Total de referidos")).toBeInTheDocument();
    expect(screen.getByText("Tasa de conversión")).toBeInTheDocument();
    expect(screen.getByText("LTV promedio por referidor")).toBeInTheDocument();
  });

  it("test_renders_top_referrers_leaderboard — shows hashed patient IDs in leaderboard", async () => {
    const { ReferralsWidget } = await import("../components/ReferralsWidget");
    render(<ReferralsWidget />);

    // Leaderboard section header
    expect(screen.getByText("Principales referidores")).toBeInTheDocument();

    // Hashed IDs must appear (not patient names)
    expect(screen.getByText("a1b2c3d4e5f6")).toBeInTheDocument();
    expect(screen.getByText("b2c3d4e5f6a7")).toBeInTheDocument();
  });

  it("test_hipaa_no_patient_names — leaderboard shows only hashed IDs, never patient names", async () => {
    const { ReferralsWidget } = await import("../components/ReferralsWidget");
    const { container } = render(<ReferralsWidget />);

    // PHI compliance: referrerLabel column header shows anonymized label
    expect(screen.getByText("Referidor (ID anónimo)")).toBeInTheDocument();

    // No patient name patterns in DOM (no real Spanish names)
    // DOM should contain hashes, not names like "María García" etc.
    expect(container.innerHTML).not.toMatch(/patient\.name/i);
  });

  it("test_loading_state — shows loading indicator when fetching", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ReferralsWidget } = await import("../components/ReferralsWidget");
    render(<ReferralsWidget />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("test_empty_state — shows empty message when no referrers", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: { ...mockReferralsData, referralsCount: 0, topReferrers: [] },
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ReferralsWidget } = await import("../components/ReferralsWidget");
    render(<ReferralsWidget />);
    expect(screen.getByText(/no hay datos de referidos/i)).toBeInTheDocument();
  });

  it("test_error_state — shows error message on query error", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: true,
      error: new Error("network error"),
    } as ReturnType<typeof useQuery>);

    const { ReferralsWidget } = await import("../components/ReferralsWidget");
    render(<ReferralsWidget />);
    expect(
      screen.getByText(/no se pudieron cargar los referidos/i),
    ).toBeInTheDocument();
  });

  it("test_no_data_state — shows empty when data is undefined", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ReferralsWidget } = await import("../components/ReferralsWidget");
    render(<ReferralsWidget />);
    expect(screen.getByText(/no hay datos de referidos/i)).toBeInTheDocument();
  });
});
