/**
 * ChannelBreakdownRow tests — SC-MK-02 gherkin coverage
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

// Mock React Query — mockMutate defined after vi.mock to avoid hoisting issues
vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useMutation: vi.fn(),
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

// Mock ConnectionBadge to isolate
vi.mock("../components/ConnectionBadge", () => ({
  ConnectionBadge: ({ status }: { status: string }) => (
    <div data-testid="connection-badge" data-state={status}>
      {status}
    </div>
  ),
}));

// Mock ChannelDetailSidebar
vi.mock("../components/ChannelDetailSidebar", () => ({
  ChannelDetailSidebar: ({
    open,
    onClose,
  }: {
    open: boolean;
    onClose: () => void;
  }) =>
    open ? (
      <div data-testid="channel-detail-sidebar" role="dialog">
        <button onClick={onClose}>Cerrar</button>
      </div>
    ) : null,
}));

import { useQuery, useMutation } from "@tanstack/react-query";

const mockMutate = vi.fn();

const mockChannelDetailError: import("../types/channel").ChannelDetailResponse =
  {
    provider: "meta_ads",
    syncState: {
      provider: "meta_ads",
      lastSyncAt: "2026-05-20T10:00:00Z",
      lastSuccessAt: "2026-05-19T10:00:00Z",
      lastError: "API rate limit exceeded",
      status: "error",
      enabled: true,
      accountId: "act_123",
    },
    metrics: [
      {
        provider: "meta_ads",
        channelSlug: "meta-ads",
        campaignId: "camp-1",
        campaignName: "Campaña Atracción",
        metricDate: "2026-05-19",
        impressions: 5000,
        clicks: 150,
        conversions: 12,
        spendCents: 50000,
        currency: "PEN",
      },
    ],
  };

const mockChannelDetailIdle: import("../types/channel").ChannelDetailResponse =
  {
    provider: "google_ads",
    syncState: {
      provider: "google_ads",
      lastSyncAt: "2026-05-20T08:00:00Z",
      lastSuccessAt: "2026-05-20T08:00:00Z",
      lastError: null,
      status: "idle",
      enabled: true,
      accountId: "cust-456",
    },
    metrics: [],
  };

describe("ChannelBreakdownRow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useMutation).mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      isError: false,
      mutateAsync: vi.fn(),
      reset: vi.fn(),
      status: "idle",
      isSuccess: false,
      isIdle: true,
      data: undefined,
      error: null,
      variables: undefined,
      context: undefined,
      failureCount: 0,
      failureReason: null,
      isPaused: false,
      submittedAt: 0,
    } as ReturnType<typeof useMutation>);
    vi.mocked(useQuery).mockReturnValue({
      data: [mockChannelDetailError],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);
  });

  it("test_shows_warning_badge_when_sync_error — SC-MK-02: badge shows error state when sync fails", async () => {
    const { ChannelBreakdownRow } =
      await import("../components/ChannelBreakdownRow");
    render(<ChannelBreakdownRow provider="meta_ads" />);

    const badge = screen.getByTestId("connection-badge");
    expect(badge).toBeInTheDocument();
    expect(badge.getAttribute("data-state")).toBe("error");
  });

  it("test_shows_last_known_metrics_with_timestamp — SC-MK-02: shows timestamp of last known data when error", async () => {
    const { ChannelBreakdownRow } =
      await import("../components/ChannelBreakdownRow");
    render(<ChannelBreakdownRow provider="meta_ads" />);

    // Should show last success timestamp even when in error state
    const timestampEl = screen.getByTestId("last-success-timestamp");
    expect(timestampEl).toBeInTheDocument();
    // Shows some date text (formatted)
    expect(timestampEl.textContent).toBeTruthy();
  });

  it("test_retry_sync_button_invokes_useSyncChannel — SC-MK-02: retry button triggers sync mutation", async () => {
    const { ChannelBreakdownRow } =
      await import("../components/ChannelBreakdownRow");
    render(<ChannelBreakdownRow provider="meta_ads" />);

    const retryBtn = screen.getByTestId("retry-sync-btn");
    expect(retryBtn).toBeInTheDocument();
    fireEvent.click(retryBtn);

    expect(mockMutate).toHaveBeenCalledWith({ provider: "meta_ads" });
  });

  it("test_renders_provider_label — shows provider display name", async () => {
    const { ChannelBreakdownRow } =
      await import("../components/ChannelBreakdownRow");
    render(<ChannelBreakdownRow provider="meta_ads" />);

    expect(screen.getByText("Meta Ads")).toBeInTheDocument();
  });

  it("test_click_row_opens_sidebar — clicking row opens ChannelDetailSidebar", async () => {
    const { ChannelBreakdownRow } =
      await import("../components/ChannelBreakdownRow");
    render(<ChannelBreakdownRow provider="meta_ads" />);

    const row = screen.getByTestId("channel-row-meta_ads");
    fireEvent.click(row);

    expect(screen.getByTestId("channel-detail-sidebar")).toBeInTheDocument();
  });

  it("test_loading_state — shows skeleton when data loading", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: undefined,
      isLoading: true,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ChannelBreakdownRow } =
      await import("../components/ChannelBreakdownRow");
    render(<ChannelBreakdownRow provider="meta_ads" />);

    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("test_idle_state_no_retry_button — idle/success state hides retry button", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: [mockChannelDetailIdle],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ChannelBreakdownRow } =
      await import("../components/ChannelBreakdownRow");
    render(<ChannelBreakdownRow provider="google_ads" />);

    expect(screen.queryByTestId("retry-sync-btn")).not.toBeInTheDocument();
  });

  it("test_google_ads_provider_label — shows Google Ads label", async () => {
    vi.mocked(useQuery).mockReturnValue({
      data: [mockChannelDetailIdle],
      isLoading: false,
      isError: false,
    } as ReturnType<typeof useQuery>);

    const { ChannelBreakdownRow } =
      await import("../components/ChannelBreakdownRow");
    render(<ChannelBreakdownRow provider="google_ads" />);

    expect(screen.getByText("Google Ads")).toBeInTheDocument();
  });
});
