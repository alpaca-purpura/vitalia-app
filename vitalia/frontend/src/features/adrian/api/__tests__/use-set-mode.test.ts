/**
 * use-set-mode.test.ts — Tests for useSetMode hook.
 *
 * Covers:
 * - SC-03: OCC 409 conflict → optimistic rollback + re-fetch triggered
 * - Happy path: optimistic update applied + resolved on success
 * - proposalRequired mapping for adrian-consulta mode
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import { useSetMode } from "../use-set-mode";
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

const CONVERSATION_ID = "conv-789";

function buildDetail(handlerMode: "ai" | "human" = "ai"): ConversationDetail {
  return {
    conversation: {
      id: CONVERSATION_ID,
      lead_id: "lead-xyz",
      tenant_id: "org-test-tenant",
      clinic_id: "clinic-abc",
      patient_id: null,
      channel: "whatsapp",
      status: "active",
      handler_mode: handlerMode,
      proposal_required: false,
      pause_until: null,
      help_needed: false,
      help_needed_reason: null,
      unread_media_count: 0,
      last_message_at: "2026-01-01T11:00:00Z",
      last_message_preview: null,
      messages_count: 0,
      stage_decision: null,
      linked_offer_id: null,
      updated_at: "2026-01-01T11:00:00Z",
    },
    lead: {
      id: "lead-xyz",
      tenant_id: "org-test-tenant",
      clinic_id: "clinic-abc",
      name: "Paciente Mock",
      phone: null,
      email: null,
      stage: "interesado",
      attribution: {
        origin: "walk_in",
        channel: null,
        attributed_at: "2026-01-01T09:00:00Z",
      },
      last_conversation_id: CONVERSATION_ID,
      created_at: "2026-01-01T09:00:00Z",
      updated_at: "2026-01-01T11:00:00Z",
    },
    messages: [],
    action_receipts: [],
    tools_state: null,
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

describe("useSetMode — SC-03 OCC conflict", () => {
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

  it("SC-03: rolls back optimistic update on 409 conflict and invalidates detail", async () => {
    const detail = buildDetail("ai");
    queryClient.setQueryData(
      ["crm", "conversation", CONVERSATION_ID],
      detail,
    );

    const conflictError = new ApiError({
      status: 409,
      statusText: "Conflict",
    } as unknown as Response);
    vi.mocked(fetchClient).mockRejectedValue(conflictError);

    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useSetMode(CONVERSATION_ID), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.mutate({
        newMode: "human",
        proposalRequired: false,
        expectedUpdatedAt: "2026-01-01T11:00:00Z",
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    // Rollback: handler_mode should be back to "ai"
    const cached = queryClient.getQueryData<ConversationDetail>([
      "crm", "conversation",
      CONVERSATION_ID,
    ]);
    expect(cached?.conversation.handler_mode).toBe("ai");

    // Re-fetch triggered
    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ["crm", "conversation", CONVERSATION_ID],
      }),
    );
  });

  it("applies optimistic update immediately on mutate", async () => {
    const detail = buildDetail("ai");
    queryClient.setQueryData(
      ["crm", "conversation", CONVERSATION_ID],
      detail,
    );

    let resolvePromise!: (value: unknown) => void;
    vi.mocked(fetchClient).mockReturnValue(
      new Promise((res) => (resolvePromise = res)),
    );

    const { result } = renderHook(() => useSetMode(CONVERSATION_ID), {
      wrapper: createWrapper(queryClient),
    });

    act(() => {
      result.current.mutate({
        newMode: "human",
        proposalRequired: false,
        expectedUpdatedAt: "2026-01-01T11:00:00Z",
      });
    });

    await waitFor(() => {
      const cached = queryClient.getQueryData<ConversationDetail>([
        "crm", "conversation",
        CONVERSATION_ID,
      ]);
      // Optimistic: switched to "human"
      expect(cached?.conversation.handler_mode).toBe("human");
    });

    resolvePromise({ conversation: buildDetail("human").conversation });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it("sets proposalRequired=true for adrian-consulta equivalent input", async () => {
    const detail = buildDetail("ai");
    queryClient.setQueryData(
      ["crm", "conversation", CONVERSATION_ID],
      detail,
    );

    vi.mocked(fetchClient).mockResolvedValue({
      conversation: buildDetail("ai").conversation,
    });

    const { result } = renderHook(() => useSetMode(CONVERSATION_ID), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.mutate({
        newMode: "ai",
        proposalRequired: true,
        expectedUpdatedAt: "2026-01-01T11:00:00Z",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(fetchClient).toHaveBeenCalledWith(
      expect.stringContaining("/mode"),
      expect.objectContaining({
        method: "PATCH",
        body: JSON.stringify({
          mode: "ai",
          proposal_required: true,
          expected_updated_at: "2026-01-01T11:00:00Z",
        }),
      }),
    );
  });
});
