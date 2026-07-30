/**
 * InboxConvList.test.tsx — Unit tests for InboxConvList + ConversationItem.
 *
 * Key test: test_render_with_help_needed_badge (SC-01/SC-02 gherkin coverage).
 * Tests list rendering, empty state integration, loading skeleton, and item badges.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { InboxConvList } from "../InboxConvList";
import { ConversationItem } from "../ConversationItem";
import type { Conversation } from "@/features/crm-shared";

// Mock Clerk — ConversationItem calls useTenantLocale() → useUser()
// T-2 fix (2026-06-01): useTenantLocale now uses useUser (not useOrganization).
// user: null / isLoaded: true triggers default locale (ARS / America/Argentina/Buenos_Aires / es-419)
vi.mock("@clerk/nextjs", () => ({
  useUser: () => ({ user: null, isLoaded: true }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Minimal conversation factory
function makeConversation(overrides: Partial<Conversation> = {}): Conversation {
  return {
    id: "conv-1",
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
    last_message_at: "2026-05-01T10:00:00Z",
    last_message_preview: "Hola, quiero información",
    messages_count: 3,
    stage_decision: null,
    linked_offer_id: null,
    updated_at: "2026-05-01T10:00:00Z",
    ...overrides,
  };
}

describe("InboxConvList", () => {
  it("renders list of conversations", () => {
    const conversations = [
      makeConversation({ id: "conv-1", last_message_preview: "Mensaje uno" }),
      makeConversation({ id: "conv-2", last_message_preview: "Mensaje dos" }),
    ];
    render(
      <InboxConvList
        conversations={conversations}
        selectedId={null}
        onSelect={vi.fn()}
      />,
    );
    // Both items rendered (role="option" inside role="listbox")
    expect(screen.getAllByRole("option")).toHaveLength(2);
  });

  it("shows loading skeleton when isLoading", () => {
    render(
      <InboxConvList
        conversations={[]}
        selectedId={null}
        onSelect={vi.fn()}
        isLoading
      />,
    );
    // Loading state shows skeleton items
    const skeletons = screen.getAllByTestId("conversation-item-skeleton");
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it("shows empty state when no conversations and not loading", () => {
    render(
      <InboxConvList
        conversations={[]}
        selectedId={null}
        onSelect={vi.fn()}
        emptyVariant="noConversations"
      />,
    );
    // Empty state component rendered
    expect(screen.getByTestId("list-empty-state")).toBeDefined();
  });

  it("marks selected conversation with aria-selected", () => {
    const conversations = [makeConversation({ id: "conv-1" })];
    render(
      <InboxConvList
        conversations={conversations}
        selectedId="conv-1"
        onSelect={vi.fn()}
      />,
    );
    const item = screen.getByRole("option", { selected: true });
    expect(item).toBeDefined();
  });
});

// SC-01 + SC-02 gherkin coverage
describe("ConversationItem", () => {
  // test_render_with_help_needed_badge — SC-02 coverage
  it("test_render_with_help_needed_badge: shows 🔴 help-needed indicator", () => {
    const conv = makeConversation({ help_needed: true });
    render(
      <ConversationItem
        conversation={conv}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="Ana López"
      />,
    );
    const badge = screen.getByTestId("help-needed-badge");
    expect(badge).toBeDefined();
  });

  it("shows 📎 unread-media indicator when unread_media_count > 0", () => {
    const conv = makeConversation({ unread_media_count: 2 });
    render(
      <ConversationItem
        conversation={conv}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="Carlos Ruiz"
      />,
    );
    const badge = screen.getByTestId("unread-media-badge");
    expect(badge).toBeDefined();
  });

  it("renders stage chip when stage_decision is set", () => {
    const conv = makeConversation({ stage_decision: "considerando" });
    render(
      <ConversationItem
        conversation={conv}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="María García"
      />,
    );
    expect(screen.getByTestId("stage-chip")).toBeDefined();
  });

  it("does not show badges when not needed", () => {
    const conv = makeConversation({
      help_needed: false,
      unread_media_count: 0,
      stage_decision: null,
    });
    render(
      <ConversationItem
        conversation={conv}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="Pedro Saenz"
      />,
    );
    expect(screen.queryByTestId("help-needed-badge")).toBeNull();
    expect(screen.queryByTestId("unread-media-badge")).toBeNull();
    expect(screen.queryByTestId("stage-chip")).toBeNull();
  });

  it("calls onSelect with conversation id when clicked", () => {
    const onSelect = vi.fn();
    const conv = makeConversation({ id: "conv-42" });
    render(
      <ConversationItem
        conversation={conv}
        isSelected={false}
        onSelect={onSelect}
        patientName="Laura Vega"
      />,
    );
    const item = screen.getByRole("option");
    item.click();
    expect(onSelect).toHaveBeenCalledWith("conv-42");
  });

  it("applies aria-selected when isSelected=true", () => {
    const conv = makeConversation({ id: "conv-1" });
    render(
      <ConversationItem
        conversation={conv}
        isSelected
        onSelect={vi.fn()}
        patientName="Ana Torres"
      />,
    );
    const item = screen.getByRole("option", { selected: true });
    expect(item).toBeDefined();
  });

  it("shows last_message_preview truncated", () => {
    const conv = makeConversation({
      last_message_preview: "Este es un mensaje bastante largo de prueba",
    });
    render(
      <ConversationItem
        conversation={conv}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="Juan Perez"
      />,
    );
    expect(
      screen.getByText("Este es un mensaje bastante largo de prueba"),
    ).toBeDefined();
  });
});
