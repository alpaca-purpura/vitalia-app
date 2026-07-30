/**
 * AdoptionStage tests — standard KPI + Lucas
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

// Mock child components
vi.mock("../components/LucasStageRecommendationsCard", () => ({
  LucasStageRecommendationsCard: ({ stage }: { stage?: string }) => (
    <div data-testid="lucas-recommendations" data-stage={stage}>
      Lucas Recommendations
    </div>
  ),
}));

import { useQuery } from "@tanstack/react-query";

const mockStageDetail = {
  stage: "adoption",
  label: "Adopción",
  periodStart: "2026-05-01T00:00:00Z",
  periodEnd: "2026-05-31T23:59:59Z",
  count: 62,
  kpis: [
    {
      key: "adherence_rate",
      label: "Adherencia",
      value: 87,
      unit: "pct",
      currency: null,
    },
    {
      key: "followup_rate",
      label: "Seguimiento completado",
      value: 73,
      unit: "pct",
      currency: null,
    },
  ],
  trendData: [],
};

describe("AdoptionStage", () => {
  beforeEach(() => {
    vi.mocked(useQuery).mockReturnValue({
      data: mockStageDetail,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);
  });

  it("test_renders_lucas_for_adoption — shows LucasStageRecommendationsCard with adoption stage", async () => {
    const { AdoptionStage } = await import("../components/AdoptionStage");
    render(<AdoptionStage />);

    const lucasCard = screen.getByTestId("lucas-recommendations");
    expect(lucasCard).toBeInTheDocument();
    expect(lucasCard.getAttribute("data-stage")).toBe("adoption");
  });

  it("test_renders_stage_kpis — shows KPI labels from stage detail", async () => {
    const { AdoptionStage } = await import("../components/AdoptionStage");
    render(<AdoptionStage />);

    expect(screen.getByText("Adherencia")).toBeInTheDocument();
  });

  it("test_no_attribution_widget — adoption stage does NOT render attribution matrix", async () => {
    const { AdoptionStage } = await import("../components/AdoptionStage");
    render(<AdoptionStage />);

    expect(
      screen.queryByTestId("attribution-matrix-widget"),
    ).not.toBeInTheDocument();
  });

  it("test_loading_state — shows skeleton when loading", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { AdoptionStage } = await import("../components/AdoptionStage");
    render(<AdoptionStage />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("test_aria_tabpanel — stage renders as tabpanel with correct id", async () => {
    const { AdoptionStage } = await import("../components/AdoptionStage");
    render(<AdoptionStage />);

    const panel = screen.getByRole("tabpanel");
    expect(panel).toBeInTheDocument();
    expect(panel.id).toBe("stage-panel-adoption");
  });
});
