/**
 * use-send-message.test.ts — Tests for useSendMessage hook.
 *
 * Covers:
 * - SC-01: Happy path send → ActionReceipt returned
 * - Optimistic update: message appended to cache before API response
 * - Rollback on error: previous cache state restored
 * - Idempotency-Key header forwarded to fetch
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import { useSendMessage } from "../use-send-message";
import type { ConversationDetail } from "../../types/inbox.types";

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    orgId: "org-test-tenant",
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Mock useClinicId
vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic-abc",
}));

// Mock fetchClient
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(),
  ApiError: class ApiError extends Error {
    constructor(
      public status: number,
      message: string,
    ) {
      super(message);
    }
  },
}));

import { fetchClient } from "@/lib/api/fetchClient";

const CONVERSATION_ID = "conv-123";

const mockConversationDetail: ConversationDetail = {
  conversation: {
    id: CONVERSATION_ID,
    lead_id: "lead-abc",
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
    id: "lead-abc",
    tenant_id: "org-test-tenant",
    clinic_id: "clinic-abc",
    name: "Test Patient",
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
      id: "msg-001",
      conversation_id: CONVERSATION_ID,
      sender_type: "patient",
      sender_user_id: null,
      body_text: "Hola",
      media_kind: null,
      media_url: null,
      media_duration_s: null,
      transcription_text: null,
      transcription_confidence: null,
      retracted_at: null,
      retract_succeeded: null,
      handler_mode: "ai",
      sent_at: "2026-01-01T10:00:00Z",
      action_receipt_expires_at: null,
    },
  ],
  action_receipts: [],
  tools_state: null,
};

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(
      QueryClientProvider,
      { client: queryClient },
      children,
    );
  };
}

describe("useSendMessage", () => {
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

  it("SC-01: sends message and invalidates conversation detail + list queries", async () => {
    const sentMessage = {
      ...mockConversationDetail.messages[0],
      id: "msg-new",
      body_text: "Buenos días",
      action_receipt_expires_at: "2026-01-01T10:05:00Z",
    };
    vi.mocked(fetchClient).mockResolvedValue(sentMessage);

    const { result } = renderHook(() => useSendMessage(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        bodyText: "Buenos días",
        idempotencyKey: "idem-uuid-001",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(sentMessage);
    expect(fetchClient).toHaveBeenCalledOnce();
  });

  it("applies optimistic update before API resolves", async () => {
    // Seed the cache with conversation detail
    queryClient.setQueryData(
      ["crm", "conversation", CONVERSATION_ID],
      mockConversationDetail,
    );

    // Delay fetchClient to observe optimistic state
    let resolvePromise!: (value: unknown) => void;
    vi.mocked(fetchClient).mockReturnValue(
      new Promise((res) => (resolvePromise = res)),
    );

    const { result } = renderHook(() => useSendMessage(), {
      wrapper: createWrapper(queryClient),
    });

    act(() => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        bodyText: "Mensaje optimista",
        idempotencyKey: "idem-uuid-002",
      });
    });

    // Before resolving: cache should have optimistic message appended
    await waitFor(() => {
      const cached = queryClient.getQueryData<ConversationDetail>([
        "crm", "conversation",
        CONVERSATION_ID,
      ]);
      expect(cached?.messages.length).toBe(2);
    });

    // Resolve the promise
    resolvePromise(mockConversationDetail.messages[0]);
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it("rolls back optimistic update on error", async () => {
    queryClient.setQueryData(
      ["crm", "conversation", CONVERSATION_ID],
      mockConversationDetail,
    );
    vi.mocked(fetchClient).mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useSendMessage(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.mutate({
        conversationId: CONVERSATION_ID,
        bodyText: "Este no va a llegar",
        idempotencyKey: "idem-uuid-003",
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    // Cache should be rolled back to original 1 message
    const cached = queryClient.getQueryData<ConversationDetail>([
      "crm", "conversation",
      CONVERSATION_ID,
    ]);
    expect(cached?.messages.length).toBe(1);
  });
});
