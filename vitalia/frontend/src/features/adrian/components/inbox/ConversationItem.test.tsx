// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * ConversationItem.test.tsx — Vitest unit tests for rich ConversationItem.
 * T-4 vitalia-fase2-adrian-inbox (MIGRATE + MERGE — updated to rich component interface)
 *
 * MERGE note: parity tests used ConversationListItem props.
 * Rich version uses Conversation (crm-shared) + patientName prop.
 * Regression_guard: same user-observable behaviors (channel icons, badges, selection).
 *
 * downstream-regression-na: brand-local component test
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ConversationItem } from "./ConversationItem";
import type { Conversation } from "@/features/crm-shared";

// Mock Clerk — ConversationItem → useTenantLocale → useUser
// Canonical pattern per mateo/AgendaHeader.test.tsx + __tests__/ContactSidebar.test.tsx
vi.mock("@clerk/nextjs", () => ({
  useUser: () => ({ user: null, isLoaded: true }),
}));
vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({
    currency: "PEN",
    timezone: "America/Lima",
    locale: "es-PE",
  }),
}));

// ── Fixtures ─────────────────────────────────────────────────────────────────

const BASE_CONVERSATION: Conversation = {
  id: "conv-001",
  lead_id: "lead-001",
  tenant_id: "tenant-001",
  clinic_id: "clinic-001",
  patient_id: "pat-hash-001",
  channel: "whatsapp",
  status: "active",
  handler_mode: "ai",
  proposal_required: false,
  pause_until: null,
  help_needed: false,
  help_needed_reason: null,
  unread_media_count: 0,
  last_message_at: new Date(Date.now() - 5 * 60_000).toISOString(),
  last_message_preview: "Hola, ¿cuánto cuesta?",
  messages_count: 3,
  stage_decision: null,
  linked_offer_id: null,
  updated_at: new Date().toISOString(),
};

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("ConversationItem", () => {
  it("renders without crashing", () => {
    render(
      <ConversationItem
        conversation={BASE_CONVERSATION}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="P.H."
      />,
    );
    expect(document.body).toBeDefined();
  });

  it("renders last message preview", () => {
    render(
      <ConversationItem
        conversation={BASE_CONVERSATION}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="P.H."
      />,
    );
    expect(screen.getByText(/Hola/)).toBeDefined();
  });

  it("calls onSelect with conversation id when clicked", () => {
    const onSelect = vi.fn();
    render(
      <ConversationItem
        conversation={BASE_CONVERSATION}
        isSelected={false}
        onSelect={onSelect}
        patientName="P.H."
      />,
    );
    const item = screen.getByRole("option");
    fireEvent.click(item);
    expect(onSelect).toHaveBeenCalledWith("conv-001");
  });

  it("shows aria-selected=true when selected", () => {
    render(
      <ConversationItem
        conversation={BASE_CONVERSATION}
        isSelected={true}
        onSelect={vi.fn()}
        patientName="P.H."
      />,
    );
    const item = screen.getByRole("option");
    expect(item.getAttribute("aria-selected")).toBe("true");
  });

  it("shows help_needed indicator 🔴 when help needed", () => {
    render(
      <ConversationItem
        conversation={{ ...BASE_CONVERSATION, help_needed: true }}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="P.H."
      />,
    );
    // help_needed badge should be visible
    expect(screen.getByTestId("help-needed-badge")).toBeDefined();
  });

  it("shows media count badge when unread_media_count > 0", () => {
    render(
      <ConversationItem
        conversation={{ ...BASE_CONVERSATION, unread_media_count: 2 }}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="P.H."
      />,
    );
    expect(screen.getByText(/📎|2/)).toBeDefined();
  });

  it("shows patient name", () => {
    render(
      <ConversationItem
        conversation={BASE_CONVERSATION}
        isSelected={false}
        onSelect={vi.fn()}
        patientName="María G."
      />,
    );
    expect(screen.getByText("María G.")).toBeDefined();
  });
});
