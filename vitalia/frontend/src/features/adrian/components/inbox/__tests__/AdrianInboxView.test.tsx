// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * AdrianInboxView.test.tsx — T-5 tests.
 *
 * SC-1: renders 3-pane layout without errors (data-testid checks).
 * RN-11: no max-width constraint on the section.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock all child components (they have their own tests)
vi.mock("../ConversationListPanel", () => ({
  ConversationListPanel: () => <div data-testid="mock-conv-list-panel" />,
}));
vi.mock("../InboxThread", () => ({
  InboxThread: ({ conversationId }: { conversationId: string }) => (
    <div data-testid="mock-inbox-thread" data-conv-id={conversationId} />
  ),
}));
vi.mock("../ContactSidebar", () => ({
  ContactSidebar: () => <div data-testid="mock-contact-sidebar" />,
}));

// Mock next/navigation
vi.mock("next/navigation", () => ({
  useSearchParams: vi.fn(() => ({
    get: vi.fn().mockReturnValue(null),
    toString: vi.fn().mockReturnValue(""),
  })),
  useRouter: vi.fn(() => ({ replace: vi.fn() })),
}));

// Mock useInboxStore
const mockSetActiveConvId = vi.fn();
vi.mock("../../../store/inbox-store", () => ({
  useInboxStore: vi.fn(
    (selector: (s: Record<string, unknown>) => unknown) =>
      selector({
        activeConvId: null,
        setActiveConvId: mockSetActiveConvId,
        contactSidebarOpen: true,
      }),
  ),
}));

// Mock crm-shared conversation detail (AdrianInboxView reads it for the contact
// sidebar). Unmocked it pulls in Clerk useAuth → "useAuth within ClerkProvider".
vi.mock("@/features/crm-shared", () => ({
  useConversationDetail: () => ({
    data: undefined,
    isLoading: false,
    isError: false,
  }),
}));

// Mock useValeriaReaccion
vi.mock("../../../hooks/useValeriaReaccion", () => ({
  useValeriaReaccion: vi.fn(() => ({
    contextMessage: null,
    suggestedActions: [],
    isLoading: false,
    isError: false,
  })),
}));

// Mock ResizablePanelGroup components (avoid canvas/DOM complexities)
vi.mock("@/components/ui/resizable", () => ({
  ResizablePanelGroup: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
    <div data-testid="resizable-group" {...props}>{children}</div>
  ),
  ResizablePanel: ({ children, ...props }: React.HTMLAttributes<HTMLDivElement>) => (
    <div data-testid="resizable-panel" {...props}>{children}</div>
  ),
  ResizableHandle: (props: React.HTMLAttributes<HTMLDivElement>) => (
    <div data-testid="resizable-handle" {...props} />
  ),
}));

import { AdrianInboxView } from "../AdrianInboxView";
import type { InitialInboxState } from "@/features/adrian/api/inbox-server";

const emptyInitialData: InitialInboxState = {
  conversations: [],
  detail: null,
  tenantId: "tenant-test",
};

describe("AdrianInboxView — SC-1 3-pane render", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("test_renders: renders without throwing", () => {
    render(
      <AdrianInboxView
        initialData={emptyInitialData}
        initialConvId={null}
        initialFilter={null}
        tenantId="tenant-test"
      />,
    );
    expect(screen.getByTestId("adrian-inbox-view")).toBeDefined();
  });

  it("test_testid: has data-testid=adrian-inbox-view", () => {
    render(
      <AdrianInboxView
        initialData={emptyInitialData}
        initialConvId={null}
        initialFilter={null}
        tenantId="tenant-test"
      />,
    );
    const view = screen.getByTestId("adrian-inbox-view");
    expect(view).toBeDefined();
  });

  it("test_aria_label: section has aria-label containing Inbox de Adrián", () => {
    render(
      <AdrianInboxView
        initialData={emptyInitialData}
        initialConvId={null}
        initialFilter={null}
        tenantId="tenant-test"
      />,
    );
    const view = screen.getByTestId("adrian-inbox-view");
    expect(view.getAttribute("aria-label")).toContain("Inbox de Adrián");
  });

  it("test_no_max_width: section fills full width (no max-width class)", () => {
    render(
      <AdrianInboxView
        initialData={emptyInitialData}
        initialConvId={null}
        initialFilter={null}
        tenantId="tenant-test"
      />,
    );
    const view = screen.getByTestId("adrian-inbox-view");
    // Should have w-full, no max-w-* class
    expect(view.className).toContain("w-full");
    expect(view.className).not.toMatch(/max-w-\[?\d/);
  });

  it("test_empty_thread: shows empty thread placeholder when no conv selected", () => {
    render(
      <AdrianInboxView
        initialData={emptyInitialData}
        initialConvId={null}
        initialFilter={null}
        tenantId="tenant-test"
      />,
    );
    // Empty state text should appear (since no conv is selected)
    expect(screen.getByTestId("inbox-thread-empty")).toBeDefined();
  });
});
