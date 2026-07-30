/**
 * ComposerArea.test.tsx — Composer area assembly tests.
 *
 * Tests that ComposerArea renders sub-components correctly and
 * wires up the send flow.
 *
 * T-FE-1 adds: effectiveMode tests (instruction mode / direct mode)
 * covering SC-8 RN-14.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ComposerArea } from "../ComposerArea";
import type { Conversation } from "@/features/crm-shared";
import { INBOX_COPY } from "../../../lib/copy";

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: async () => "mock-token",
    orgId: "org_test",
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic_test",
}));

vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(async () => ({
    id: "msg-1",
    conversation_id: "conv-1",
    sender_type: "agent_human",
    sender_user_id: null,
    body_text: "Test",
    media_kind: null,
    media_url: null,
    media_duration_s: null,
    transcription_text: null,
    transcription_confidence: null,
    retracted_at: null,
    retract_succeeded: null,
    handler_mode: "human",
    sent_at: new Date().toISOString(),
    action_receipt_expires_at: null,
  })),
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
    ) {
      super(message);
    }
  },
}));

function makeConversation(overrides: Partial<Conversation> = {}): Conversation {
  return {
    id: "conv-1",
    tenant_id: "tenant-1",
    clinic_id: "clinic-1",
    lead_id: "lead-1",
    patient_id: null,
    channel: "whatsapp",
    status: "active",
    handler_mode: "ai",
    proposal_required: false,
    pause_until: null,
    help_needed: false,
    help_needed_reason: null,
    unread_media_count: 0,
    last_message_at: "2026-01-01T00:00:00Z",
    last_message_preview: null,
    messages_count: 0,
    stage_decision: null,
    linked_offer_id: null,
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("ComposerArea", () => {
  it("renders MessageInput textarea", () => {
    render(<ComposerArea conversation={makeConversation()} />, { wrapper });
    // Textarea should be present
    expect(screen.getByRole("textbox")).toBeInTheDocument();
  });

  it("renders attach button with correct aria-label in direct mode (handler_mode human)", () => {
    // Attach button is only shown in direct mode (paused = human)
    render(
      <ComposerArea conversation={makeConversation({ handler_mode: "human" })} />,
      { wrapper },
    );
    expect(
      screen.getByRole("button", { name: INBOX_COPY.composer.attachAriaLabel }),
    ).toBeInTheDocument();
  });

  it("T-FE-1 (RN-14): instruction mode renders 'Dar instrucción' send label when handler_mode=ai", () => {
    // handler_mode=ai (decide) → effectiveMode=instruction → "Dar instrucción" label
    render(
      <ComposerArea conversation={makeConversation({ handler_mode: "ai" })} />,
      { wrapper },
    );
    expect(
      screen.getByRole("button", { name: INBOX_COPY.composer.sendButtonInstruction }),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: INBOX_COPY.composer.sendButtonHuman }),
    ).toBeNull();
  });

  it("direct mode renders 'Enviar' send label when handler_mode=human (Adrián paused)", () => {
    render(
      <ComposerArea conversation={makeConversation({ handler_mode: "human" })} />,
      { wrapper },
    );
    expect(
      screen.getByRole("button", { name: INBOX_COPY.composer.sendButtonHuman }),
    ).toBeInTheDocument();
  });

  it("shows ProposalCardBanner when pendingProposalText is provided", () => {
    render(
      <ComposerArea
        conversation={makeConversation({ handler_mode: "human" })}
        pendingProposalText="Hola, te puedo ayudar con tu consulta."
      />,
      { wrapper },
    );
    expect(
      screen.getByRole("region", {
        name: INBOX_COPY.proposalCardBanner.heading,
      }),
    ).toBeInTheDocument();
    expect(
      screen.getByText("Hola, te puedo ayudar con tu consulta."),
    ).toBeInTheDocument();
  });

  it("send button is disabled when text is empty (direct mode)", () => {
    render(
      <ComposerArea conversation={makeConversation({ handler_mode: "human" })} />,
      { wrapper },
    );
    const sendBtn = screen.getByRole("button", {
      name: INBOX_COPY.composer.sendButtonHuman,
    });
    expect(sendBtn).toBeDisabled();
  });

  it("send button becomes enabled when user types text (direct mode)", () => {
    render(
      <ComposerArea conversation={makeConversation({ handler_mode: "human" })} />,
      { wrapper },
    );
    const textarea = screen.getByRole("textbox");
    fireEvent.change(textarea, { target: { value: "Hola" } });
    const sendBtn = screen.getByRole("button", {
      name: INBOX_COPY.composer.sendButtonHuman,
    });
    expect(sendBtn).not.toBeDisabled();
  });

  it("clears textarea after editing proposal (direct mode)", () => {
    render(
      <ComposerArea
        conversation={makeConversation({ handler_mode: "human" })}
        pendingProposalText="Propuesta de Adrián"
      />,
      { wrapper },
    );
    // Click edit CTA — should copy proposal text to textarea
    fireEvent.click(
      screen.getByRole("button", {
        name: INBOX_COPY.proposalCardBanner.editCta,
      }),
    );
    const textarea = screen.getByRole("textbox") as HTMLTextAreaElement;
    expect(textarea.value).toBe("Propuesta de Adrián");
  });

  // ── T-FE-1: effectiveMode / instruction mode tests (SC-8 RN-14) ──────────

  it("shows instruction mode label when handler_mode is 'ai' (decide)", () => {
    render(
      <ComposerArea conversation={makeConversation({ handler_mode: "ai" })} />,
      { wrapper },
    );
    expect(
      screen.getByRole("note", { name: INBOX_COPY.instruction.modeLabel }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(INBOX_COPY.instruction.modeHint, { exact: false }),
    ).toBeInTheDocument();
  });

  it("does NOT show instruction label when handler_mode is 'human' (paused)", () => {
    render(
      <ComposerArea conversation={makeConversation({ handler_mode: "human" })} />,
      { wrapper },
    );
    expect(
      screen.queryByRole("note", { name: INBOX_COPY.instruction.modeLabel }),
    ).toBeNull();
  });

  it("shows instruction mode send button label in decide mode", () => {
    render(
      <ComposerArea conversation={makeConversation({ handler_mode: "ai" })} />,
      { wrapper },
    );
    expect(
      screen.getByRole("button", {
        name: INBOX_COPY.composer.sendButtonInstruction,
      }),
    ).toBeInTheDocument();
  });

  it("shows instruction chip when activeInstruction is set + handler_mode is ai", () => {
    render(
      <ComposerArea
        conversation={makeConversation({ handler_mode: "ai" })}
        activeInstruction="Ofrécele 10% de descuento por ser referido"
      />,
      { wrapper },
    );
    expect(
      screen.getByText("Ofrécele 10% de descuento por ser referido"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: INBOX_COPY.instruction.chipClearAriaLabel }),
    ).toBeInTheDocument();
  });

  it("does NOT show instruction chip when handler_mode is 'human'", () => {
    render(
      <ComposerArea
        conversation={makeConversation({ handler_mode: "human" })}
        activeInstruction="Ofrécele 10% de descuento"
      />,
      { wrapper },
    );
    expect(
      screen.queryByRole("button", { name: INBOX_COPY.instruction.chipClearAriaLabel }),
    ).toBeNull();
  });

  it("shows direct mode send button in human mode (Adrián paused)", () => {
    render(
      <ComposerArea conversation={makeConversation({ handler_mode: "human" })} />,
      { wrapper },
    );
    expect(
      screen.getByRole("button", {
        name: INBOX_COPY.composer.sendButtonHuman,
      }),
    ).toBeInTheDocument();
  });
});
