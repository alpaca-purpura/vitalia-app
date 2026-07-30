/**
 * ReservationStage tests — SC-MK-03 attribution matrix inline
 * @coverage gherkin SC-MK-03 (test_renders_attribution_matrix_inline)
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// Mock nuqs
vi.mock("nuqs", () => {
  const makeParser = () => ({
    withDefault: (_d: unknown) => ({
      withOptions: (_opts: unknown) => ({
        defaultValue: _d,
        parseServerSide: (v: unknown) => v,
      }),
      defaultValue: _d,
      parseServerSide: (v: unknown) => v,
    }),
    withOptions: (_opts: unknown) => ({
      withDefault: (_d: unknown) => ({
        defaultValue: _d,
        parseServerSide: (v: unknown) => v,
      }),
      defaultValue: undefined,
      parseServerSide: (v: unknown) => v,
    }),
    defaultValue: undefined,
    parseServerSide: (v: unknown) => v,
  });
  return {
    useQueryState: (_key: string, _parser: unknown) => [null, vi.fn()],
    parseAsStringEnum: (_values: string[]) => makeParser(),
    parseAsString: makeParser(),
    parseAsBoolean: makeParser(),
  };
});

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("tok"),
    orgId: "org-1",
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Mock clinic hook
vi.mock("@/hooks/useClinicId", () => ({ useClinicId: () => "clinic-123" }));

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

// Mock child components to isolate stage test
vi.mock("../components/LucasStageRecommendationsCard", () => ({
  LucasStageRecommendationsCard: ({ stage }: { stage?: string }) => (
    <div data-testid="lucas-recommendations" data-stage={stage}>
      Lucas Recommendations
    </div>
  ),
}));

vi.mock("../components/AttributionMatrixWidget", () => ({
  AttributionMatrixWidget: () => (
    <div data-testid="attribution-matrix-widget">Attribution Matrix</div>
  ),
}));

import { useQuery } from "@tanstack/react-query";

const mockStageDetail = {
  stage: "reservation",
  label: "Reserva",
  periodStart: "2026-05-01T00:00:00Z",
  periodEnd: "2026-05-31T23:59:59Z",
  count: 36,
  kpis: [
    {
      key: "conv_rate",
      label: "Tasa de conversión",
      value: 41,
      unit: "pct",
      currency: null,
    },
    {
      key: "no_show_rate",
      label: "Ausentismo",
      value: 12,
      unit: "pct",
      currency: null,
    },
  ],
  trendData: [],
};

describe("ReservationStage", () => {
  beforeEach(() => {
    vi.mocked(useQuery).mockReturnValue({
      data: mockStageDetail,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);
  });

  it("test_renders_attribution_matrix_inline — SC-MK-03: reservation stage renders AttributionMatrixWidget", async () => {
    const { ReservationStage } = await import("../components/ReservationStage");
    render(<ReservationStage />);

    // SC-MK-03: Attribution matrix must appear inline in the reservation stage
    expect(screen.getByTestId("attribution-matrix-widget")).toBeInTheDocument();
  });

  it("test_renders_lucas_recommendations — shows LucasStageRecommendationsCard for reservation", async () => {
    const { ReservationStage } = await import("../components/ReservationStage");
    render(<ReservationStage />);

    const lucasCard = screen.getByTestId("lucas-recommendations");
    expect(lucasCard).toBeInTheDocument();
    expect(lucasCard.getAttribute("data-stage")).toBe("reservation");
  });

  it("test_renders_stage_kpis — shows KPI hero cards from stage detail", async () => {
    const { ReservationStage } = await import("../components/ReservationStage");
    render(<ReservationStage />);

    // KPI labels from mock data
    expect(screen.getByText("Tasa de conversión")).toBeInTheDocument();
  });

  it("test_loading_state — shows skeleton when loading", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ReservationStage } = await import("../components/ReservationStage");
    render(<ReservationStage />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("test_aria_tabpanel — stage renders as tabpanel with correct id", async () => {
    const { ReservationStage } = await import("../components/ReservationStage");
    render(<ReservationStage />);

    const panel = screen.getByRole("tabpanel");
    expect(panel).toBeInTheDocument();
    expect(panel.id).toBe("stage-panel-reservation");
  });
});
