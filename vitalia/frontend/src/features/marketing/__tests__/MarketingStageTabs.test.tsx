/**
 * MarketingStageTabs tests — SC-MK-03 tab URL state + active highlight
 * @coverage gherkin SC-MK-03 (test_tab_click_updates_url_replace + test_active_tab_highlight_cian)
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

// Mock nuqs — control what setTab does
const mockSetTab = vi.fn();
vi.mock("nuqs", () => ({
  useQueryState: (_key: string, _parser: unknown) => ["attraction", mockSetTab],
  parseAsStringEnum: (_values: string[]) => ({
    withDefault: (_d: unknown) => ({
      withOptions: (_opts: unknown) => ({}),
    }),
  }),
  parseAsString: { withOptions: (_opts: unknown) => ({}) },
  parseAsBoolean: {
    withDefault: (_d: unknown) => ({ withOptions: (_opts: unknown) => ({}) }),
  },
}));

// Mock the hooks (T-mk-fe-1 outputs)
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


// Import the component (will fail until created — RED test)
import { MarketingStageTabs } from "../components/MarketingStageTabs";

const mockStages = [
  {
    slug: "attraction" as const,
    label: "Atracción",
    count: 182,
    primaryKpiValue: 24,
    primaryKpiLabel: "cpL",
  },
  {
    slug: "qualification" as const,
    label: "Calificación",
    count: 87,
    primaryKpiValue: 48,
    primaryKpiLabel: "conv%",
  },
  {
    slug: "reservation" as const,
    label: "Reserva",
    count: 36,
    primaryKpiValue: 41,
    primaryKpiLabel: "conv%",
  },
  {
    slug: "adoption" as const,
    label: "Adopción",
    count: 62,
    primaryKpiValue: 87,
    primaryKpiLabel: "adherencia%",
  },
  {
    slug: "expansion" as const,
    label: "Expansión",
    count: 28,
    primaryKpiValue: 72,
    primaryKpiLabel: "NPS",
  },
];

describe("MarketingStageTabs", () => {
  beforeEach(() => {
    mockSetTab.mockClear();
  });

  it("test_tab_click_updates_url_replace — clicking a tab calls setTab with slug (SC-MK-03)", () => {
    render(
      <MarketingStageTabs
        stages={mockStages}
        activeTab="attraction"
        onTabChange={mockSetTab}
      />,
    );
    const qualTab = screen.getByRole("tab", { name: /calificación/i });
    fireEvent.click(qualTab);
    expect(mockSetTab).toHaveBeenCalledWith("qualification");
  });

  it("test_active_tab_highlight_cian — active tab has cian background class (SC-MK-03)", () => {
    render(
      <MarketingStageTabs
        stages={mockStages}
        activeTab="attraction"
        onTabChange={mockSetTab}
      />,
    );
    const attractionTab = screen.getByRole("tab", { name: /atracción/i });
    // active tab must have cian gradient/border styling
    expect(attractionTab).toHaveAttribute("aria-selected", "true");
    // The active class must contain bg-gradient-to-r (cian gradient) or data-active attribute
    const classOrData =
      attractionTab.className.includes("gradient") ||
      attractionTab.className.includes("cian") ||
      attractionTab.dataset["active"] === "true";
    expect(classOrData).toBe(true);
  });

  it("renders all 5 stage tabs", () => {
    render(
      <MarketingStageTabs
        stages={mockStages}
        activeTab="attraction"
        onTabChange={mockSetTab}
      />,
    );
    expect(screen.getAllByRole("tab")).toHaveLength(5);
  });

  it("renders count badge per tab", () => {
    render(
      <MarketingStageTabs
        stages={mockStages}
        activeTab="attraction"
        onTabChange={mockSetTab}
      />,
    );
    expect(screen.getByText("182")).toBeInTheDocument();
    expect(screen.getByText("87")).toBeInTheDocument();
    expect(screen.getByText("36")).toBeInTheDocument();
  });

  it("inactive tabs are aria-selected=false", () => {
    render(
      <MarketingStageTabs
        stages={mockStages}
        activeTab="attraction"
        onTabChange={mockSetTab}
      />,
    );
    const qualTab = screen.getByRole("tab", { name: /calificación/i });
    expect(qualTab).toHaveAttribute("aria-selected", "false");
  });
});
