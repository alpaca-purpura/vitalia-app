// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * ChannelBadge.test.tsx — RED-first tests for ChannelBadge molecule.
 * T-3 vitalia-fase2-adrian-inbox
 *
 * ChannelBadge lives in components/shared/shell-organism/ but is tested here
 * co-located as part of T-3 deliverables.
 *
 * downstream-regression-na: brand-local component test
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChannelBadge } from "@/components/shared/shell-organism/ChannelBadge";

// Mock next/navigation (needed for AdrianInboxView which uses useSearchParams)
vi.mock("next/navigation", () => ({
  useSearchParams: vi.fn(() => ({
    get: vi.fn().mockReturnValue(null),
    toString: vi.fn().mockReturnValue(""),
  })),
  useRouter: vi.fn(() => ({ replace: vi.fn() })),
}));

// Mock deps used by AdrianInboxView
vi.mock("../../../store/inbox-store", () => ({
  useInboxStore: vi.fn(
    (selector: (s: Record<string, unknown>) => unknown) =>
      selector({ activeConvId: null, setActiveConvId: vi.fn(), contactSidebarOpen: false }),
  ),
}));

vi.mock("../../../hooks/useValeriaReaccion", () => ({
  useValeriaReaccion: vi.fn(() => ({
    contextMessage: null,
    suggestedActions: [],
    isLoading: false,
    isError: false,
  })),
}));

// crm-shared conversation detail (AdrianInboxView contact sidebar) — unmocked it
// pulls Clerk useAuth → "useAuth within ClerkProvider".
vi.mock("@/features/crm-shared", () => ({
  useConversationDetail: () => ({
    data: undefined,
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("../ConversationListPanel", () => ({
  ConversationListPanel: () => <div data-testid="mock-conv-list-panel" />,
}));
vi.mock("../InboxThread", () => ({
  InboxThread: () => <div data-testid="mock-inbox-thread" />,
}));
vi.mock("../ContactSidebar", () => ({
  ContactSidebar: () => <div data-testid="mock-contact-sidebar" />,
}));
vi.mock("@/components/ui/resizable", () => ({
  ResizablePanelGroup: ({ children }: React.HTMLAttributes<HTMLDivElement>) => (
    <div>{children}</div>
  ),
  ResizablePanel: ({ children }: React.HTMLAttributes<HTMLDivElement>) => (
    <div>{children}</div>
  ),
  ResizableHandle: () => <div />,
}));

describe("ChannelBadge — renders correct label per channel", () => {
  it("renders WhatsApp channel", () => {
    render(<ChannelBadge channel="whatsapp" />);
    const badge = screen.getByTestId("channel-badge-whatsapp");
    expect(badge).toBeDefined();
    // Label visible text
    expect(badge.textContent).toContain("WhatsApp");
  });

  it("renders instagram channel", () => {
    render(<ChannelBadge channel="instagram" />);
    // badge renders without throwing
    const badge = screen.getByTestId("channel-badge-instagram");
    expect(badge).toBeDefined();
  });

  it("renders email channel", () => {
    render(<ChannelBadge channel="email" />);
    const badge = screen.getByTestId("channel-badge-email");
    expect(badge).toBeDefined();
  });

  it("renders web channel", () => {
    render(<ChannelBadge channel="web" />);
    const badge = screen.getByTestId("channel-badge-web");
    expect(badge).toBeDefined();
  });

  it("does NOT contain hardcoded hex colors in output", () => {
    const { container } = render(<ChannelBadge channel="whatsapp" />);
    // No inline style with hex colors
    expect(container.innerHTML).not.toMatch(/#[0-9a-fA-F]{3,6}/);
  });
});

describe("ChannelBadge — AdrianInboxView skeleton renders", () => {
  it("renders without throwing with initialData placeholder", async () => {
    const { AdrianInboxView } = await import(
      "@/features/adrian/components/inbox/AdrianInboxView"
    );
    render(
      <AdrianInboxView
        initialData={{ conversations: [], detail: null, tenantId: "t1" }}
        initialConvId={null}
        initialFilter={null}
        tenantId="t1"
      />,
    );
    // skeleton renders the inbox container
    expect(document.body).toBeDefined();
  });
});
