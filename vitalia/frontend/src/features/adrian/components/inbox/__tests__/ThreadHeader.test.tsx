/**
 * ThreadHeader.test.tsx — Unit tests for ThreadHeader.
 *
 * Tests:
 *   - Renders header with data-testid=thread-header
 *   - Contains SegmentedControl3Modes
 *   - Contains VoiceStyleChip
 *   - Contains PauseAdrianButton
 *   - Contains ToolsSheetTrigger
 *   - Contains ContactSidebarToggle
 *   - Patient name displayed
 *
 * Mocked dependencies: useInboxStore, useModeToggle, useConversationDetail.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { ThreadHeader } from "../ThreadHeader";
import type { ConversationDetail } from "../../../types/inbox.types";
// Mock useInboxStore
const mockToggleContactSidebar = vi.fn();
const mockToggleActivityStream = vi.fn();
vi.mock("../../../store/inbox-store", () => ({
  useInboxStore: (
    selector: (s: {
      contactSidebarOpen: boolean;
      toggleContactSidebar: () => void;
      expandedActivityStream: boolean;
      toggleActivityStream: () => void;
    }) => unknown,
  ) =>
    selector({
      contactSidebarOpen: false,
      toggleContactSidebar: mockToggleContactSidebar,
      expandedActivityStream: false,
      toggleActivityStream: mockToggleActivityStream,
    }),
}));

// Mock useModeToggle
const mockToggle = vi.fn();
vi.mock("../../../hooks/use-mode-toggle", async (importOriginal) => {
  const original =
    await importOriginal<typeof import("../../../hooks/use-mode-toggle")>();
  return {
    ...original,
    useModeToggle: () => ({
      toggle: mockToggle,
      isPending: false,
      isConflict: false,
    }),
  };
});

// Mock usePauseAdrian (used by PauseAdrianButton)
vi.mock("../../../api/use-pause-adrian", () => ({
  usePauseAdrian: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

vi.mock("../../../api/use-nudge", () => ({
  useNudge: () => ({
    mutate: vi.fn(),
    isPending: false,
  }),
}));

/** Build a minimal ConversationDetail fixture */
function makeDetail(
  overrides: Partial<ConversationDetail["conversation"]> = {},
): ConversationDetail {
  return {
    conversation: {
      id: "conv-test-1",
      lead_id: "lead-1",
      tenant_id: "tenant-1",
      clinic_id: "clinic-1",
      patient_id: null,
      channel: "whatsapp",
      status: "active",
      handler_mode: "ai",
      proposal_required: false,
      pause_until: null,
      help_needed: false,
      help_needed_reason: null,
      unread_media_count: 0,
      last_message_at: new Date().toISOString(),
      last_message_preview: "Hola",
      messages_count: 1,
      stage_decision: null,
      linked_offer_id: null,
      updated_at: new Date().toISOString(),
      ...overrides,
    },
    lead: {
      id: "lead-1",
      tenant_id: "tenant-1",
      clinic_id: "clinic-1",
      name: "María García",
      phone: null,
      email: null,
      stage: "interesado",
      attribution: {
        origin: "sales_agent",
        channel: "whatsapp",
        attributed_at: new Date().toISOString(),
      },
      last_conversation_id: "conv-test-1",
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    messages: [],
    action_receipts: [],
    tools_state: null,
  };
}

describe("ThreadHeader", () => {
  beforeEach(() => {
    mockToggle.mockReset();
    mockToggleContactSidebar.mockReset();
    mockToggleActivityStream.mockReset();
  });

  it("renders with data-testid=thread-header", () => {
    render(<ThreadHeader detail={makeDetail()} />);
    expect(screen.getByTestId("thread-header")).toBeDefined();
  });

  it("displays patient name from detail.lead.name", () => {
    render(<ThreadHeader detail={makeDetail()} />);
    expect(screen.getByTestId("thread-header-patient-name").textContent).toBe(
      "María García",
    );
  });

  it("displays channel badge from detail.conversation.channel", () => {
    render(<ThreadHeader detail={makeDetail()} />);
    expect(
      screen.getByTestId("thread-header-channel").textContent?.toLowerCase(),
    ).toContain("whatsapp");
  });

  it("renders SegmentedControl3Modes component", () => {
    render(<ThreadHeader detail={makeDetail()} />);
    expect(screen.getByTestId("segmented-control-3-modes")).toBeDefined();
  });

  it("does NOT render VoiceStyleChip (removed · Chris UI #3)", () => {
    render(<ThreadHeader detail={makeDetail()} />);
    expect(screen.queryByTestId("voice-style-chip")).toBeNull();
  });

  it("does NOT render PauseAdrianButton (moved to composer dock · Chris UI #3)", () => {
    render(<ThreadHeader detail={makeDetail()} />);
    expect(screen.queryByTestId("pause-adrian-button")).toBeNull();
  });

  it("does NOT render ToolsSheetTrigger (removed · Chris UI #2 — bottom activity stream is enough)", () => {
    render(<ThreadHeader detail={makeDetail()} />);
    expect(screen.queryByTestId("tools-sheet-trigger")).toBeNull();
  });

  it("renders ContactSidebarToggle component", () => {
    render(<ThreadHeader detail={makeDetail()} />);
    expect(screen.getByTestId("contact-sidebar-toggle")).toBeDefined();
  });

  it("SegmentedControl3Modes shows adrian-decide when handler_mode=ai + proposal_required=false", () => {
    const detail = makeDetail({ handler_mode: "ai", proposal_required: false });
    render(<ThreadHeader detail={detail} />);
    const adrianDecide = screen.getByTestId("segment-adrian-decide");
    expect(adrianDecide.getAttribute("aria-checked")).toBe("true");
  });

  it("legacy handler_mode=human falls back to adrian-decide (manual is now Pausar)", () => {
    const detail = makeDetail({
      handler_mode: "human",
      proposal_required: false,
    });
    render(<ThreadHeader detail={detail} />);
    expect(screen.queryByTestId("segment-yo-escribo")).toBeNull();
    const adrianDecide = screen.getByTestId("segment-adrian-decide");
    expect(adrianDecide.getAttribute("aria-checked")).toBe("true");
  });

  it("SegmentedControl3Modes shows adrian-consulta when handler_mode=ai + proposal_required=true", () => {
    const detail = makeDetail({ handler_mode: "ai", proposal_required: true });
    render(<ThreadHeader detail={detail} />);
    const adrianConsulta = screen.getByTestId("segment-adrian-consulta");
    expect(adrianConsulta.getAttribute("aria-checked")).toBe("true");
  });
});
