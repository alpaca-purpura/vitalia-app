/**
 * ChannelConnectionWizard tests — 3-step OAuth wizard (selector → OAuth → confirm)
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
const mockSyncMutate = vi.fn();
vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useMutation: vi.fn().mockReturnValue({
    mutate: mockSyncMutate,
    isPending: false,
    isError: false,
    isSuccess: false,
  }),
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

// Mock window.location for jsdom navigation testing
Object.defineProperty(window, "location", {
  value: { href: "" },
  writable: true,
});

describe("ChannelConnectionWizard", () => {
  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    window.location.href = "";
  });

  it("test_not_rendered_when_closed — wizard not in DOM when open=false", async () => {
    const { ChannelConnectionWizard } =
      await import("../components/ChannelConnectionWizard");
    const { queryByRole } = render(
      <ChannelConnectionWizard
        open={false}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />,
    );

    expect(queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("test_step1_renders_provider_selector — step 1 shows provider options", async () => {
    const { ChannelConnectionWizard } =
      await import("../components/ChannelConnectionWizard");
    render(
      <ChannelConnectionWizard
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />,
    );

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByTestId("wizard-step-1")).toBeInTheDocument();
    expect(screen.getByTestId("provider-option-meta_ads")).toBeInTheDocument();
    expect(
      screen.getByTestId("provider-option-google_ads"),
    ).toBeInTheDocument();
  });

  it("test_cancel_button_calls_onClose — cancel button invokes onClose", async () => {
    const { ChannelConnectionWizard } =
      await import("../components/ChannelConnectionWizard");
    render(
      <ChannelConnectionWizard
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />,
    );

    const cancelBtn = screen.getByTestId("wizard-cancel-btn");
    fireEvent.click(cancelBtn);

    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("test_provider_selection_enables_authorize — selecting provider enables authorize button", async () => {
    const { ChannelConnectionWizard } =
      await import("../components/ChannelConnectionWizard");
    render(
      <ChannelConnectionWizard
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />,
    );

    // Initially authorize button is disabled (no provider selected)
    const authorizeBtn = screen.getByTestId("wizard-authorize-btn");
    expect(authorizeBtn).toBeDisabled();

    // Select meta_ads
    const metaOption = screen.getByTestId("provider-option-meta_ads");
    fireEvent.click(metaOption);

    // Now authorize should be enabled
    expect(authorizeBtn).not.toBeDisabled();
  });

  it("test_oauth_uses_full_page_navigation — OAuth redirect uses window.location.href (NOT window.open)", async () => {
    // Spy on window.open to ensure it's NEVER called
    const windowOpenSpy = vi.spyOn(window, "open");
    const locationSpy = vi.spyOn(window.location, "href", "set");

    const { ChannelConnectionWizard } =
      await import("../components/ChannelConnectionWizard");
    render(
      <ChannelConnectionWizard
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
        // Inject mock auth URL for test
        _testAuthorizationUrl="https://meta.com/oauth/authorize?state=abc123"
      />,
    );

    // Select provider and authorize
    fireEvent.click(screen.getByTestId("provider-option-meta_ads"));
    fireEvent.click(screen.getByTestId("wizard-authorize-btn"));

    // Should NOT use window.open (popup)
    expect(windowOpenSpy).not.toHaveBeenCalled();
    // Should use full page navigation
    expect(locationSpy).toHaveBeenCalledWith(
      "https://meta.com/oauth/authorize?state=abc123",
    );
  });

  it("test_wizard_title_spanish_neutro — wizard title uses Spanish neutro tuteo", async () => {
    const { ChannelConnectionWizard } =
      await import("../components/ChannelConnectionWizard");
    render(
      <ChannelConnectionWizard
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />,
    );

    const dialog = screen.getByRole("dialog");
    // Title text uses tuteo imperatives
    expect(dialog.textContent).toContain("Conectar canal");
    expect(dialog.textContent).toContain("Selecciona el canal");
  });

  it("test_step_indicator_shows_step_1_active — step indicator marks step 1 as active initially", async () => {
    const { ChannelConnectionWizard } =
      await import("../components/ChannelConnectionWizard");
    render(
      <ChannelConnectionWizard
        open={true}
        onClose={mockOnClose}
        onSuccess={mockOnSuccess}
      />,
    );

    expect(screen.getByTestId("step-indicator-1")).toHaveAttribute(
      "aria-current",
      "step",
    );
  });
});
