/**
 * ChannelDetailSidebar tests — KPIs + campaigns + Lucas recs + external links
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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
  useMutation: vi.fn().mockReturnValue({ mutate: vi.fn(), isPending: false }),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  QueryClient: vi.fn(),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

// Mock useTenantLocale
vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({ currency: "PEN", timezone: "America/Lima" }),
}));

// Mock LucasStageRecommendationsCard
vi.mock("../components/LucasStageRecommendationsCard", () => ({
  LucasStageRecommendationsCard: ({ stage }: { stage?: string }) => (
    <div data-testid="lucas-recommendations" data-stage={stage}>
      Lucas Recs
    </div>
  ),
}));

import { useQuery } from "@tanstack/react-query";

const mockDetail: import("../types/channel").ChannelDetailResponse = {
  provider: "meta_ads",
  syncState: {
    provider: "meta_ads",
    lastSyncAt: "2026-05-20T10:00:00Z",
    lastSuccessAt: "2026-05-20T09:00:00Z",
    lastError: null,
    status: "idle",
    enabled: true,
    accountId: "act_123",
  },
  metrics: [
    {
      provider: "meta_ads",
      channelSlug: "meta-ads",
      campaignId: "camp-1",
      campaignName: "Campaña Retargeting",
      metricDate: "2026-05-20",
      impressions: 10000,
      clicks: 300,
      conversions: 25,
      spendCents: 75000,
      currency: "PEN",
    },
    {
      provider: "meta_ads",
      channelSlug: "meta-ads",
      campaignId: "camp-2",
      campaignName: "Campaña Atracción",
      metricDate: "2026-05-20",
      impressions: 5000,
      clicks: 100,
      conversions: 8,
      spendCents: 30000,
      currency: "PEN",
    },
    {
      provider: "meta_ads",
      channelSlug: "meta-ads",
      campaignId: "camp-3",
      campaignName: "Campaña Reactivación",
      metricDate: "2026-05-20",
      impressions: 2000,
      clicks: 50,
      conversions: 4,
      spendCents: 15000,
      currency: "PEN",
    },
  ],
};

describe("ChannelDetailSidebar", () => {
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useQuery).mockReturnValue({
      data: [mockDetail],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);
  });

  it("test_not_rendered_when_closed — sidebar not in DOM when open=false", async () => {
    const { ChannelDetailSidebar } =
      await import("../components/ChannelDetailSidebar");
    const { queryByRole } = render(
      <ChannelDetailSidebar
        open={false}
        provider="meta_ads"
        onClose={mockOnClose}
      />,
    );

    expect(queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("test_renders_when_open — sidebar renders as dialog when open=true", async () => {
    const { ChannelDetailSidebar } =
      await import("../components/ChannelDetailSidebar");
    render(
      <ChannelDetailSidebar
        open={true}
        provider="meta_ads"
        onClose={mockOnClose}
      />,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
  });

  it("test_close_button_calls_onClose — close button invokes onClose callback", async () => {
    const { ChannelDetailSidebar } =
      await import("../components/ChannelDetailSidebar");
    render(
      <ChannelDetailSidebar
        open={true}
        provider="meta_ads"
        onClose={mockOnClose}
      />,
    );

    const closeBtn = screen.getByTestId("sidebar-close-btn");
    fireEvent.click(closeBtn);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("test_shows_top_3_campaigns — renders up to 3 campaign rows from metrics", async () => {
    const { ChannelDetailSidebar } =
      await import("../components/ChannelDetailSidebar");
    render(
      <ChannelDetailSidebar
        open={true}
        provider="meta_ads"
        onClose={mockOnClose}
      />,
    );

    expect(screen.getByText("Campaña Retargeting")).toBeInTheDocument();
    expect(screen.getByText("Campaña Atracción")).toBeInTheDocument();
    expect(screen.getByText("Campaña Reactivación")).toBeInTheDocument();
  });

  it("test_shows_provider_title — shows correct provider display name", async () => {
    const { ChannelDetailSidebar } =
      await import("../components/ChannelDetailSidebar");
    render(
      <ChannelDetailSidebar
        open={true}
        provider="meta_ads"
        onClose={mockOnClose}
      />,
    );

    expect(screen.getByTestId("sidebar-provider-title")).toHaveTextContent(
      "Meta Ads",
    );
  });

  it("test_external_link_has_target_blank — external link has proper security attributes", async () => {
    const { ChannelDetailSidebar } =
      await import("../components/ChannelDetailSidebar");
    render(
      <ChannelDetailSidebar
        open={true}
        provider="meta_ads"
        onClose={mockOnClose}
      />,
    );

    const externalLink = screen.getByTestId("external-manager-link");
    expect(externalLink.getAttribute("target")).toBe("_blank");
    expect(externalLink.getAttribute("rel")).toBe("noopener noreferrer");
  });

  it("test_shows_lucas_recommendations — renders Lucas recommendations section", async () => {
    const { ChannelDetailSidebar } =
      await import("../components/ChannelDetailSidebar");
    render(
      <ChannelDetailSidebar
        open={true}
        provider="meta_ads"
        onClose={mockOnClose}
      />,
    );

    expect(screen.getByTestId("lucas-recommendations")).toBeInTheDocument();
  });

  it("test_loading_state — shows skeleton when data loading", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ChannelDetailSidebar } =
      await import("../components/ChannelDetailSidebar");
    render(
      <ChannelDetailSidebar
        open={true}
        provider="meta_ads"
        onClose={mockOnClose}
      />,
    );

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("test_no_campaigns_empty_state — shows empty state when no metrics", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: [{ ...mockDetail, metrics: [] }],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ChannelDetailSidebar } =
      await import("../components/ChannelDetailSidebar");
    render(
      <ChannelDetailSidebar
        open={true}
        provider="meta_ads"
        onClose={mockOnClose}
      />,
    );

    expect(screen.getByTestId("no-campaigns-message")).toBeInTheDocument();
  });
});
