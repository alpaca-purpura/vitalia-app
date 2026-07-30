/**
 * MessageBubble.test.tsx
 *
 * SC-01 coverage: test_renders_action_receipt_inline — agent_ai message shows undo chip.
 * SC-04 coverage: test_xss_escaped_as_literal — XSS payload renders as text, not HTML.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MessageBubble } from "../MessageBubble";
import type { Message } from "../../../types/inbox.types";

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
// MessageBubble formats per-bubble timestamps via useTenantLocale (UI-AUDIT #3).
vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({
    currency: "PEN",
    timezone: "America/Lima",
    locale: "es-PE",
  }),
}));


vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic_test",
}));

vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(async () => ({})),
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
    ) {
      super(message);
    }
  },
}));

function makeMessage(overrides: Partial<Message> = {}): Message {
  return {
    id: "msg-1",
    conversation_id: "conv-1",
    sender_type: "agent_ai",
    sender_user_id: null,
    body_text: "Hola, te atiendo con gusto.",
    media_kind: null,
    media_url: null,
    media_duration_s: null,
    transcription_text: null,
    transcription_confidence: null,
    retracted_at: null,
    retract_succeeded: null,
    handler_mode: "ai",
    sent_at: "2026-01-01T00:00:00Z",
    action_receipt_expires_at: null,
    ...overrides,
  };
}

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("MessageBubble", () => {
  /**
   * SC-01: test_renders_action_receipt_inline
   * Given: agent_ai message with action_receipt_expires_at 5 minutes in future
   * When: MessageBubble is rendered
   * Then: ActionReceiptUndoChip with countdown appears inline below the bubble
   */
  it("test_renders_action_receipt_inline — shows undo chip for AI message within window", () => {
    const expiresAt = new Date(Date.now() + 300_000).toISOString();
    const msg = makeMessage({ action_receipt_expires_at: expiresAt });

    render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );

    // Undo chip visible with "Revertir" (the "✨ auto" marker moved to the
    // per-turn header rendered by InboxThread — no longer on the bubble, #2).
    expect(screen.getByText("Revertir")).toBeInTheDocument();
    // Timer role exists
    expect(screen.getByRole("timer")).toBeInTheDocument();
  });

  it("does NOT show undo chip when action_receipt_expires_at is null", () => {
    const msg = makeMessage({ action_receipt_expires_at: null });
    render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );
    expect(screen.queryByText("Revertir")).toBeNull();
  });

  it("does NOT show undo chip when message is already retracted", () => {
    const expiresAt = new Date(Date.now() + 300_000).toISOString();
    const msg = makeMessage({
      action_receipt_expires_at: expiresAt,
      retracted_at: "2026-01-01T00:00:10Z",
    });
    render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );
    expect(screen.queryByText("Revertir")).toBeNull();
  });

  /**
   * SC-04: test_xss_escaped_as_literal
   * Given: a message with XSS payload in body_text
   * When: MessageBubble is rendered
   * Then: payload is visible as escaped literal text, NOT executed as HTML
   */
  it("test_xss_escaped_as_literal — XSS payload renders as text, not HTML", () => {
    const xssPayload = "<script>alert('xss')</script>";
    const msg = makeMessage({
      sender_type: "patient",
      body_text: xssPayload,
    });
    const { container } = render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );

    // The payload must appear as visible text (React escapes it)
    expect(screen.getByText(xssPayload)).toBeInTheDocument();
    // No <script> tag should exist in the DOM
    expect(container.querySelector("script")).toBeNull();
  });

  // UI-AUDIT #4 — WhatsApp business inbox orientation: the patient (incoming) is on
  // the LEFT; Adrián / human (outgoing) is on the RIGHT.
  it("renders patient message left-aligned (incoming · data-sender=patient)", () => {
    const msg = makeMessage({ sender_type: "patient", body_text: "Hola" });
    const { container } = render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );
    const bubble = container.querySelector("[data-sender='patient']");
    expect(bubble).toBeInTheDocument();
    // Should have mr-auto class for left alignment
    expect(bubble?.className).toContain("mr-auto");
  });

  it("renders agent_ai message right-aligned (outgoing · data-sender=agent_ai)", () => {
    const msg = makeMessage({ sender_type: "agent_ai", body_text: "Hola" });
    const { container } = render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );
    const bubble = container.querySelector("[data-sender='agent_ai']");
    expect(bubble?.className).toContain("ml-auto");
  });

  // UI-AUDIT #3 — every message bubble shows its own HH:mm timestamp.
  it("shows a per-bubble timestamp", () => {
    const msg = makeMessage({
      sender_type: "patient",
      body_text: "Hola",
      sent_at: "2026-01-01T15:30:00Z",
    });
    render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );
    expect(screen.getByTestId("message-bubble-time")).toBeInTheDocument();
  });

  it("renders system message as centered pill", () => {
    const msg = makeMessage({
      sender_type: "system",
      body_text: "La conversación fue reasignada",
    });
    render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );
    expect(screen.getByRole("status")).toBeInTheDocument();
    expect(
      screen.getByText("La conversación fue reasignada"),
    ).toBeInTheDocument();
  });

  it("renders retracted message with strikethrough style", () => {
    const msg = makeMessage({
      retracted_at: "2026-01-01T00:00:10Z",
      body_text: "Mensaje original",
    });
    render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );
    expect(screen.getByText("[Mensaje revertido]")).toBeInTheDocument();
  });

  it("renders VoiceMessagePlayer for audio media_kind", () => {
    const msg = makeMessage({
      sender_type: "patient",
      body_text: null,
      media_kind: "audio",
      media_url: "https://cdn.example.com/audio.webm",
      media_duration_s: 15,
    });
    render(
      <MessageBubble
        message={msg}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );
    // Audio player region should be present
    expect(
      screen.getByRole("region", { name: /nota de voz/i }),
    ).toBeInTheDocument();
  });
});
