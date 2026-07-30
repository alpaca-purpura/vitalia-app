/**
 * ExpansionStage tests — SC-MK-03 referrals widget inline
 * @coverage gherkin SC-MK-03 (test_renders_referrals_widget)
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

vi.mock("../components/ReferralsWidget", () => ({
  ReferralsWidget: () => (
    <div data-testid="referrals-widget">Referrals Widget</div>
  ),
}));

import { useQuery } from "@tanstack/react-query";

const mockStageDetail = {
  stage: "expansion",
  label: "Expansión",
  periodStart: "2026-05-01T00:00:00Z",
  periodEnd: "2026-05-31T23:59:59Z",
  count: 28,
  kpis: [
    { key: "nps", label: "NPS", value: 72, unit: "score", currency: null },
    {
      key: "referral_rate",
      label: "Tasa de referidos",
      value: 18,
      unit: "pct",
      currency: null,
    },
  ],
  trendData: [],
};

describe("ExpansionStage", () => {
  beforeEach(() => {
    vi.mocked(useQuery).mockReturnValue({
      data: mockStageDetail,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);
  });

  it("test_renders_referrals_widget — SC-MK-03: expansion stage renders ReferralsWidget", async () => {
    const { ExpansionStage } = await import("../components/ExpansionStage");
    render(<ExpansionStage />);

    // SC-MK-03: Referrals widget must appear inline in the expansion stage
    expect(screen.getByTestId("referrals-widget")).toBeInTheDocument();
  });

  it("test_renders_lucas_recommendations — shows LucasStageRecommendationsCard for expansion", async () => {
    const { ExpansionStage } = await import("../components/ExpansionStage");
    render(<ExpansionStage />);

    const lucasCard = screen.getByTestId("lucas-recommendations");
    expect(lucasCard).toBeInTheDocument();
    expect(lucasCard.getAttribute("data-stage")).toBe("expansion");
  });

  it("test_renders_nps_placeholder — shows NPS placeholder section", async () => {
    const { ExpansionStage } = await import("../components/ExpansionStage");
    render(<ExpansionStage />);

    // NPS placeholder section should exist
    expect(screen.getByTestId("nps-placeholder")).toBeInTheDocument();
  });

  it("test_renders_stage_kpis — shows KPI hero cards from stage detail", async () => {
    const { ExpansionStage } = await import("../components/ExpansionStage");
    render(<ExpansionStage />);

    // NPS KPI label appears (may appear multiple times: KPI card + NPS placeholder heading)
    const npsElements = screen.getAllByText("NPS");
    expect(npsElements.length).toBeGreaterThan(0);
  });

  it("test_loading_state — shows skeleton when loading", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ExpansionStage } = await import("../components/ExpansionStage");
    render(<ExpansionStage />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("test_aria_tabpanel — stage renders as tabpanel with correct id", async () => {
    const { ExpansionStage } = await import("../components/ExpansionStage");
    render(<ExpansionStage />);

    const panel = screen.getByRole("tabpanel");
    expect(panel).toBeInTheDocument();
    expect(panel.id).toBe("stage-panel-expansion");
  });
});
