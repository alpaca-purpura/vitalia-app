/**
 * AttractionStage tests — renders Lucas card + KPIs + channel breakdown placeholder
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

// Mock ChannelBreakdownRow (T-mk-fe-5) to isolate AttractionStage test
vi.mock("../components/ChannelBreakdownRow", () => ({
  ChannelBreakdownRow: ({ provider }: { provider?: string }) => (
    <div data-testid={`channel-row-${provider}`} data-provider={provider}>
      Channel Row: {provider}
    </div>
  ),
}));

import { useQuery } from "@tanstack/react-query";

const mockStageDetail = {
  stage: "attraction",
  label: "Atracción",
  periodStart: "2026-05-01T00:00:00Z",
  periodEnd: "2026-05-31T23:59:59Z",
  count: 182,
  kpis: [
    { key: "cpl", label: "CPL", value: 24, unit: "currency", currency: "PEN" },
    {
      key: "conv_rate",
      label: "Tasa de conversión",
      value: 48,
      unit: "pct",
      currency: null,
    },
  ],
  trendData: [],
};

describe("AttractionStage", () => {
  beforeEach(() => {
    vi.mocked(useQuery).mockReturnValue({
      data: mockStageDetail,
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);
  });

  it("test_renders_channel_breakdown_placeholder — shows channel breakdown placeholder for T-mk-fe-5", async () => {
    const { AttractionStage } = await import("../components/AttractionStage");
    render(<AttractionStage />);

    // Channel breakdown placeholder (T-mk-fe-5 will fill with real ChannelBreakdown)
    expect(
      screen.getByTestId("channel-breakdown-placeholder"),
    ).toBeInTheDocument();
  });

  it("test_renders_lucas_recommendations — shows LucasStageRecommendationsCard for attraction", async () => {
    const { AttractionStage } = await import("../components/AttractionStage");
    render(<AttractionStage />);

    const lucasCard = screen.getByTestId("lucas-recommendations");
    expect(lucasCard).toBeInTheDocument();
    expect(lucasCard.getAttribute("data-stage")).toBe("attraction");
  });

  it("test_renders_stage_kpis — shows KPI labels from stage detail", async () => {
    const { AttractionStage } = await import("../components/AttractionStage");
    render(<AttractionStage />);

    expect(screen.getByText("CPL")).toBeInTheDocument();
  });

  it("test_loading_state — shows skeleton when loading", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { AttractionStage } = await import("../components/AttractionStage");
    render(<AttractionStage />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("test_aria_tabpanel — stage renders as tabpanel with correct id", async () => {
    const { AttractionStage } = await import("../components/AttractionStage");
    render(<AttractionStage />);

    const panel = screen.getByRole("tabpanel");
    expect(panel).toBeInTheDocument();
    expect(panel.id).toBe("stage-panel-attraction");
  });
});
