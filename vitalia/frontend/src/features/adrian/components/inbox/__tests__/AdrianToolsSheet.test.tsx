/**
 * AdrianToolsSheet.test.tsx — Unit tests for AdrianToolsSheet.
 *
 * Tests:
 *   - Renders panel closed when open=false
 *   - Renders open when open=true (accessible role="dialog")
 *   - Shows read-only badge on tools (aria-disabled)
 *   - Shows HIPAA guard note for each tool (hipaaGuardNote)
 *   - Shows goToOfferStudio link when tools present
 *   - Shows noTools message when invocations empty
 *   - Calls onClose when close button clicked
 *
 * useToolsState mocked via vi.mock.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AdrianToolsSheet } from "../AdrianToolsSheet";
import { INBOX_COPY } from "../../../lib/copy";
import type { ToolsState } from "../../../types/inbox.types";

// Mock Clerk — AdrianToolsSheet calls useTenantLocale() → useUser()
// T-2 fix (2026-06-01): useTenantLocale now uses useUser (not useOrganization).
// user: null / isLoaded: true triggers vitalia default locale (ARS / America/Argentina/Buenos_Aires / es-419)
vi.mock("@clerk/nextjs", () => ({
  useUser: () => ({ user: null, isLoaded: true }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


const mockOnClose = vi.fn();

const mockToolsState: ToolsState = {
  conversation_id: "conv-1",
  linked_offer_id: null,
  invocations: [
    {
      tool_name: "schedule_appointment",
      display_name: "Agendar cita",
      invoked_at: "2026-01-15T10:00:00Z",
      started_at: "2026-01-15T10:00:00Z",
      completed_at: "2026-01-15T10:00:01Z",
      status: "success",
      result_summary: "Cita agendada para el 20 de enero",
      enabled: true,
      disabled_reason: null,
      last_used_at: "2026-01-15T10:00:00Z",
    },
    {
      tool_name: "send_offer_link",
      display_name: "Enviar enlace de oferta",
      invoked_at: "2026-01-15T10:01:00Z",
      started_at: "2026-01-15T10:01:00Z",
      completed_at: null,
      status: "error",
      result_summary: null,
      enabled: true,
      disabled_reason: null,
      last_used_at: null,
    },
  ],
};

vi.mock("../../../api/use-tools-state", () => ({
  useToolsState: vi.fn(() => ({
    data: mockToolsState,
    isLoading: false,
    isError: false,
  })),
}));

describe("AdrianToolsSheet — closed state", () => {
  beforeEach(() => mockOnClose.mockReset());

  it("renders nothing when open=false", () => {
    const { container } = render(
      <AdrianToolsSheet
        open={false}
        onClose={mockOnClose}
        conversationId="conv-1"
      />,
    );
    expect(
      container.querySelector("[data-testid='adrian-tools-sheet']"),
    ).toBeNull();
  });
});

describe("AdrianToolsSheet — open state with tools", () => {
  beforeEach(() => mockOnClose.mockReset());

  it("renders panel with correct aria-label when open=true", () => {
    render(
      <AdrianToolsSheet
        open={true}
        onClose={mockOnClose}
        conversationId="conv-1"
      />,
    );
    const panel = screen.getByTestId("adrian-tools-sheet");
    expect(panel).toBeDefined();
    expect(panel.getAttribute("aria-label")).toBe(
      INBOX_COPY.toolsSheet.ariaLabel,
    );
  });

  it("shows sheet title", () => {
    render(
      <AdrianToolsSheet
        open={true}
        onClose={mockOnClose}
        conversationId="conv-1"
      />,
    );
    expect(screen.getByText(INBOX_COPY.toolsSheet.title)).toBeDefined();
  });

  it("close button calls onClose", () => {
    render(
      <AdrianToolsSheet
        open={true}
        onClose={mockOnClose}
        conversationId="conv-1"
      />,
    );
    fireEvent.click(screen.getByTestId("tools-sheet-close"));
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("shows tool names as read-only (test_read_only_with_disabled_explanation)", () => {
    render(
      <AdrianToolsSheet
        open={true}
        onClose={mockOnClose}
        conversationId="conv-1"
      />,
    );
    // Tools are displayed read-only — no interactive controls like buttons for invoking
    expect(screen.getByText("schedule_appointment")).toBeDefined();
    expect(screen.getByText("send_offer_link")).toBeDefined();
    // Tool rows should NOT have a button that invokes the tool
    const invokeButtons = screen.queryAllByRole("button", {
      name: /invocar|usar herramienta/i,
    });
    expect(invokeButtons).toHaveLength(0);
  });

  it("shows HIPAA guard note explaining why tools are disabled", () => {
    render(
      <AdrianToolsSheet
        open={true}
        onClose={mockOnClose}
        conversationId="conv-1"
      />,
    );
    expect(screen.getByTestId("hipaa-guard-note")).toBeDefined();
    expect(
      screen.getByText(INBOX_COPY.toolsSheet.hipaaGuardNote),
    ).toBeDefined();
  });

  it("shows goToOfferStudio link", () => {
    render(
      <AdrianToolsSheet
        open={true}
        onClose={mockOnClose}
        conversationId="conv-1"
      />,
    );
    const link = screen.getByTestId("offer-studio-link");
    expect(link).toBeDefined();
    expect(link.textContent).toContain(INBOX_COPY.toolsSheet.goToOfferStudio);
  });

  it("shows status label for each tool invocation", () => {
    render(
      <AdrianToolsSheet
        open={true}
        onClose={mockOnClose}
        conversationId="conv-1"
      />,
    );
    // success status
    expect(screen.getByText(INBOX_COPY.toolsSheet.statusEnabled)).toBeDefined();
    // error status row should have statusDisabled label or error marker
    expect(
      screen.getByText(INBOX_COPY.toolsSheet.statusDisabled),
    ).toBeDefined();
  });
});

describe("AdrianToolsSheet — empty invocations", () => {
  it("shows noTools copy when invocations is empty", async () => {
    const { useToolsState } = await import("../../../api/use-tools-state");
    vi.mocked(useToolsState).mockReturnValue(
      // Mock partial React Query result — full type not needed in test
      {
        data: {
          conversation_id: "conv-2",
          invocations: [],
          updated_at: "2026-01-15T10:00:00Z",
        },
        isLoading: false,
        isError: false,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } as any,
    );

    render(
      <AdrianToolsSheet
        open={true}
        onClose={mockOnClose}
        conversationId="conv-2"
      />,
    );
    expect(screen.getByText(INBOX_COPY.toolsSheet.noTools)).toBeDefined();
  });
});
