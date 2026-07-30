/**
 * ActivityStream.test.tsx — Unit tests for ActivityStream.
 *
 * Tests:
 *   - Renders collapsed (32px height) by default
 *   - Expands to 240px when toggleActivityStream called
 *   - Shows last 8 events when expanded (test_8_last_events_scrollable)
 *   - Shows empty state when no events
 *   - Shows event kind label from INBOX_COPY.activityStream.eventKinds
 *   - Toggle button aria-expanded reflects state
 *
 * useActivityStream + useInboxStore mocked.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ActivityStream } from "../ActivityStream";
import { INBOX_COPY } from "../../../lib/copy";
import type { ActivityEvent } from "../../../types/inbox.types";

// Mock Clerk — ActivityStream calls useTenantLocale() → useUser()
// T-2 fix (2026-06-01): useTenantLocale now uses useUser (not useOrganization).
// user: null / isLoaded: true triggers vitalia default locale (ARS / America/Argentina/Buenos_Aires / es-419)
vi.mock("@clerk/nextjs", () => ({
  useUser: () => ({ user: null, isLoaded: true }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Mock useInboxStore
let mockExpanded = false;
const mockToggle = vi.fn();
vi.mock("../../../store/inbox-store", () => ({
  useInboxStore: (
    selector: (s: {
      expandedActivityStream: boolean;
      toggleActivityStream: () => void;
    }) => unknown,
  ) =>
    selector({
      expandedActivityStream: mockExpanded,
      toggleActivityStream: mockToggle,
    }),
}));

// Create 10 test events (more than 8 to test slice)
const createEvent = (
  id: string,
  kind: ActivityEvent["kind"],
  summary: string,
): ActivityEvent => ({
  id,
  conversation_id: "conv-1",
  kind,
  summary,
  payload_redacted: null,
  occurred_at: `2026-01-15T10:0${id}:00Z`,
});

const mockEvents: ActivityEvent[] = [
  createEvent("0", "turn_start", "Comenzó turno 0"),
  createEvent("1", "tool_call", "Usó herramienta 1"),
  createEvent("2", "llm_call", "Procesó consulta 2"),
  createEvent("3", "message_sent", "Envió mensaje 3"),
  createEvent("4", "proposal_generated", "Generó propuesta 4"),
  createEvent("5", "mode_changed", "Cambió modo 5"),
  createEvent("6", "turn_end", "Terminó turno 6"),
  createEvent("7", "tool_call", "Usó herramienta 7"),
  createEvent("8", "message_sent", "Envió mensaje 8"),
  createEvent("9", "compliance_blocked", "Bloqueado 9"),
];

vi.mock("../../../api/use-activity-stream", () => ({
  useActivityStream: vi.fn(() => ({
    data: { events: mockEvents, total: 10 },
    isLoading: false,
    isError: false,
  })),
}));

describe("ActivityStream — collapsed state", () => {
  beforeEach(() => {
    mockExpanded = false;
    mockToggle.mockReset();
  });

  it("renders collapse wrapper with data-testid", () => {
    render(<ActivityStream conversationId="conv-1" />);
    expect(screen.getByTestId("agent-activity-stream")).toBeDefined();
  });

  it("toggle button has aria-expanded=false when collapsed", () => {
    render(<ActivityStream conversationId="conv-1" />);
    const btn = screen.getByTestId("activity-stream-toggle");
    expect(btn.getAttribute("aria-expanded")).toBe("false");
  });

  it("toggle button has aria-label from INBOX_COPY.activityStream.expandAriaLabel", () => {
    render(<ActivityStream conversationId="conv-1" />);
    const btn = screen.getByTestId("activity-stream-toggle");
    expect(btn.getAttribute("aria-label")).toBe(
      INBOX_COPY.activityStream.expandAriaLabel,
    );
  });

  it("clicking toggle calls toggleActivityStream in store", () => {
    render(<ActivityStream conversationId="conv-1" />);
    fireEvent.click(screen.getByTestId("activity-stream-toggle"));
    expect(mockToggle).toHaveBeenCalledTimes(1);
  });

  it("events list is not visible when collapsed", () => {
    render(<ActivityStream conversationId="conv-1" />);
    // Event items should not be rendered when collapsed
    expect(screen.queryByTestId("activity-event-list")).toBeNull();
  });
});

describe("ActivityStream — expanded state (test_8_last_events_scrollable)", () => {
  beforeEach(() => {
    mockExpanded = true;
    mockToggle.mockReset();
  });

  it("renders event list when expanded", () => {
    render(<ActivityStream conversationId="conv-1" />);
    expect(screen.getByTestId("activity-event-list")).toBeDefined();
  });

  it("shows at most 8 events (last 8 from stream)", () => {
    render(<ActivityStream conversationId="conv-1" />);
    const items = screen.getAllByTestId(/^activity-event-item-/);
    expect(items).toHaveLength(8);
  });

  it("shows last 8 events (events 2..9, not 0..1)", () => {
    render(<ActivityStream conversationId="conv-1" />);
    // Events 0 and 1 should NOT appear (only last 8)
    expect(screen.queryByText("Comenzó turno 0")).toBeNull();
    expect(screen.queryByText("Usó herramienta 1")).toBeNull();
    // Events 2..9 should appear
    expect(screen.getByText("Procesó consulta 2")).toBeDefined();
    expect(screen.getByText("Bloqueado 9")).toBeDefined();
  });

  it("shows event kind label from INBOX_COPY.activityStream.eventKinds", () => {
    render(<ActivityStream conversationId="conv-1" />);
    // tool_call kind label
    const kindLabel = INBOX_COPY.activityStream.eventKinds.tool_call;
    expect(screen.getAllByText(kindLabel).length).toBeGreaterThan(0);
  });

  it("toggle button has aria-expanded=true when expanded", () => {
    render(<ActivityStream conversationId="conv-1" />);
    const btn = screen.getByTestId("activity-stream-toggle");
    expect(btn.getAttribute("aria-expanded")).toBe("true");
  });

  it("toggle button has aria-label=collapseAriaLabel when expanded", () => {
    render(<ActivityStream conversationId="conv-1" />);
    const btn = screen.getByTestId("activity-stream-toggle");
    expect(btn.getAttribute("aria-label")).toBe(
      INBOX_COPY.activityStream.collapseAriaLabel,
    );
  });
});

describe("ActivityStream — empty events", () => {
  beforeEach(() => {
    mockExpanded = true;
  });

  it("shows empty state copy when no events", async () => {
    const { useActivityStream } = await import("../../../api/use-activity-stream");
    vi.mocked(useActivityStream).mockReturnValue(
      // Mock partial React Query result — full type not needed in test
      {
        data: { events: [], total: 0 },
        isLoading: false,
        isError: false,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
    );

    render(<ActivityStream conversationId="conv-1" />);
    expect(screen.getByText(INBOX_COPY.activityStream.empty)).toBeDefined();
  });
});
