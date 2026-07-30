/**
 * MarketingLayout tests — SC-MK-03 bowtie sticky top + orchestration
 * @coverage gherkin SC-MK-03 (test_bowtie_sticky_top)
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// Mock nuqs — handle both withDefault().withOptions() and direct withOptions() patterns
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
    useQueryState: (_key: string, _parser: unknown) => ["attraction", vi.fn()],
    parseAsStringEnum: (_values: string[]) => makeParser(),
    parseAsString: makeParser(),
    parseAsBoolean: makeParser(),
  };
});

// Mock data hooks (T-mk-fe-1 outputs)
vi.mock("@/features/marketing/api/use-bowtie-summary", () => ({
  useBowtieSummary: () => ({
    data: {
      periodStart: "2026-05-01T00:00:00Z",
      periodEnd: "2026-05-31T23:59:59Z",
      stages: [
        {
          slug: "attraction",
          label: "Atracción",
          count: 182,
          primaryKpiValue: 24,
          primaryKpiLabel: "cpL",
        },
        {
          slug: "qualification",
          label: "Calificación",
          count: 87,
          primaryKpiValue: 48,
          primaryKpiLabel: "conv%",
        },
        {
          slug: "reservation",
          label: "Reserva",
          count: 36,
          primaryKpiValue: 41,
          primaryKpiLabel: "conv%",
        },
        {
          slug: "adoption",
          label: "Adopción",
          count: 62,
          primaryKpiValue: 87,
          primaryKpiLabel: "adherencia%",
        },
        {
          slug: "expansion",
          label: "Expansión",
          count: 28,
          primaryKpiValue: 72,
          primaryKpiLabel: "NPS",
        },
      ],
      overallConversionPct: 15.4,
      overallRoiX: 3.2,
      overallLtvCents: 89000,
      currency: "PEN",
      lastSyncAt: "2026-05-20T18:00:00Z",
    },
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("@/hooks/useClinicId", () => ({ useClinicId: () => "clinic-123" }));
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("tok"),
    orgId: "org-1",
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Mock child components to isolate layout test
vi.mock("../components/MarketingBowtieSVG", () => ({
  MarketingBowtieSVG: ({ className }: { className?: string }) => (
    <div data-testid="bowtie-svg" className={className}>
      Bowtie SVG
    </div>
  ),
}));

vi.mock("../components/MarketingStageTabs", () => ({
  MarketingStageTabs: () => <div data-testid="stage-tabs">Stage Tabs</div>,
}));

vi.mock("../components/StageDispatcher", () => ({
  StageDispatcher: () => (
    <div data-testid="stage-dispatcher">Stage Content</div>
  ),
}));

vi.mock("../components/MarketingActivityFooter", () => ({
  MarketingActivityFooter: () => (
    <div data-testid="activity-footer">Activity Footer</div>
  ),
}));

// Import component under test (RED — will fail until created)
import { MarketingLayout } from "../components/MarketingLayout";

describe("MarketingLayout", () => {
  it("test_bowtie_sticky_top — bowtie container has position sticky and top-0 (SC-MK-03)", () => {
    render(<MarketingLayout />);
    const bowtieContainer = screen.getByTestId("bowtie-sticky-container");
    expect(bowtieContainer).toBeInTheDocument();
    // sticky positioning
    expect(bowtieContainer.className).toMatch(/sticky/);
    expect(bowtieContainer.className).toMatch(/top-0/);
  });

  it("renders MarketingBowtieSVG at top", () => {
    render(<MarketingLayout />);
    expect(screen.getByTestId("bowtie-svg")).toBeInTheDocument();
  });

  it("renders MarketingStageTabs below bowtie", () => {
    render(<MarketingLayout />);
    expect(screen.getByTestId("stage-tabs")).toBeInTheDocument();
  });

  it("renders StageDispatcher as main content", () => {
    render(<MarketingLayout />);
    expect(screen.getByTestId("stage-dispatcher")).toBeInTheDocument();
  });

  it("renders MarketingActivityFooter at bottom", () => {
    render(<MarketingLayout />);
    expect(screen.getByTestId("activity-footer")).toBeInTheDocument();
  });

  it("has correct DOM order: bowtie sticky container appears before stage-tabs in document", () => {
    const { container } = render(<MarketingLayout />);
    const bowtie = container.querySelector(
      "[data-testid='bowtie-sticky-container']",
    );
    const tabs = container.querySelector("[data-testid='stage-tabs']");
    expect(bowtie).toBeInTheDocument();
    expect(tabs).toBeInTheDocument();
    // bowtie must come before tabs in document order
    const position = bowtie!.compareDocumentPosition(tabs!);
    // Node.DOCUMENT_POSITION_FOLLOWING = 4 (tabs comes after bowtie)
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
