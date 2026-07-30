/**
 * use-retract-message.test.ts — Tests for useRetractMessage hook.
 *
 * Covers:
 * - Happy path: retraction succeeds → message marked retracted_at
 * - Optimistic: message immediately marked + action receipt removed
 * - Rollback on error: previous state restored
 * - 409 conflict: re-fetch triggered
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import { useRetractMessage } from "../use-retract-message";
import { conversationDetailKeyForInvalidation } from "../_keys";
import { ApiError } from "@/lib/api/fetchClient";
import type { ConversationDetail } from "../../types/inbox.types";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    orgId: "org-test-tenant",
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-abc",
}));

vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number;
    statusText: string;
    body: unknown;
    constructor(response: Response, body?: unknown) {
      super(`API error ${response.status}`);
      this.status = response.status;
      this.statusText = response.statusText;
      this.body = body;
    }
  },
}));

import { fetchClient } from "@/lib/api/fetchClient";

const CONVERSATION_ID = "conv-456";
const MESSAGE_ID = "msg-retractable";

function buildDetail(
  partial?: Partial<ConversationDetail>,
): ConversationDetail {
  return {
    conversation: {
      id: CONVERSATION_ID,
      lead_id: "lead-def",
      tenant_id: "org-test-tenant",
      clinic_id: "clinic-abc",
      patient_id: null,
      channel: "whatsapp",
      status: "active",
      handler_mode: "ai",
      proposal_required: false,
      pause_until: null,
      help_needed: false,
      help_needed_reason: null,
      unread_media_count: 0,
      last_message_at: "2026-01-01T10:00:00Z",
      last_message_preview: "Hola",
      messages_count: 1,
      stage_decision: null,
      linked_offer_id: null,
      updated_at: "2026-01-01T10:00:00Z",
    },
    lead: {
      id: "lead-def",
      tenant_id: "org-test-tenant",
      clinic_id: "clinic-abc",
      name: "Paciente Test",
      phone: null,
      email: null,
      stage: "interesado",
      attribution: {
        origin: "sales_agent",
        channel: "whatsapp",
        attributed_at: "2026-01-01T09:00:00Z",
      },
      last_conversation_id: CONVERSATION_ID,
      created_at: "2026-01-01T09:00:00Z",
      updated_at: "2026-01-01T10:00:00Z",
    },
    messages: [
      {
        id: MESSAGE_ID,
        conversation_id: CONVERSATION_ID,
        sender_type: "agent_ai",
        sender_user_id: null,
        body_text: "Mensaje original",
        media_kind: null,
        media_url: null,
        media_duration_s: null,
        transcription_text: null,
        transcription_confidence: null,
        retracted_at: null,
        retract_succeeded: null,
        handler_mode: "ai",
        sent_at: "2026-01-01T10:00:00Z",
        action_receipt_expires_at: "2026-01-01T10:05:00Z",
      },
    ],
    action_receipts: [
      {
        id: "receipt-1",
        message_id: MESSAGE_ID,
        conversation_id: "conv-test-1",
        expires_at: "2026-01-01T10:05:00Z",
        used: false,
        created_at: "2026-01-01T10:00:00Z",
      },
    ],
    tools_state: null,
    ...partial,
  };
}

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(
      QueryClientProvider,
      { client: queryClient },
      children,
    );
  };
}

describe("useRetractMessage", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  it("optimistically marks message as retracted and removes action receipt", async () => {
    queryClient.setQueryData(
      conversationDetailKeyForInvalidation(CONVERSATION_ID),
      buildDetail(),
    );
    let resolvePromise!: (value: unknown) => void;
    vi.mocked(fetchClient).mockReturnValue(
      new Promise((res) => (resolvePromise = res)),
    );

    const { result } = renderHook(() => useRetractMessage(), {
      wrapper: createWrapper(queryClient),
    });

    act(() => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        messageId: MESSAGE_ID,
        expectedUpdatedAt: "2026-01-01T10:00:00Z",
      });
    });

    await waitFor(() => {
      const cached = queryClient.getQueryData<ConversationDetail>(
        conversationDetailKeyForInvalidation(CONVERSATION_ID),
      );
      // Optimistic: retracted_at is set
      expect(cached?.messages[0].retracted_at).toBeTruthy();
      // Action receipt removed
      expect(cached?.action_receipts.length).toBe(0);
    });

    resolvePromise({ message: buildDetail().messages[0] });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it("rolls back optimistic update on network error", async () => {
    const detail = buildDetail();
    queryClient.setQueryData(
      conversationDetailKeyForInvalidation(CONVERSATION_ID),
      detail,
    );
    vi.mocked(fetchClient).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useRetractMessage(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        messageId: MESSAGE_ID,
        expectedUpdatedAt: "2026-01-01T10:00:00Z",
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    const cached = queryClient.getQueryData<ConversationDetail>(
      conversationDetailKeyForInvalidation(CONVERSATION_ID),
    );
    expect(cached?.messages[0].retracted_at).toBeNull();
    expect(cached?.action_receipts.length).toBe(1);
  });

  it("invalidates detail query on 409 conflict", async () => {
    queryClient.setQueryData(
      conversationDetailKeyForInvalidation(CONVERSATION_ID),
      buildDetail(),
    );
    const conflictError = new ApiError({
      status: 409,
      statusText: "Conflict",
    } as unknown as Response);
    vi.mocked(fetchClient).mockRejectedValue(conflictError);

    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useRetractMessage(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        messageId: MESSAGE_ID,
        expectedUpdatedAt: "2026-01-01T10:00:00Z",
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    // Should have invalidated to re-fetch fresh state
    expect(invalidateSpy).toHaveBeenCalled();
  });
});
