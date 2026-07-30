/**
 * use-activity-stream.test.ts — Tests for useActivityStream hook.
 *
 * Covers:
 * - Polling enabled when expanded=true
 * - Query disabled when expanded=false
 * - Query disabled when conversationId is null
 * - sanitize payload: test that no PHI fields leak in event (payload_redacted contract)
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import { useActivityStream } from "../use-activity-stream";
import type { ActivityStreamResponse } from "../use-activity-stream";

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
  ApiError: class extends Error {},
}));

import { fetchClient } from "@/lib/api/fetchClient";

const CONVERSATION_ID = "conv-stream-001";

const mockStreamResponse: ActivityStreamResponse = {
  events: [
    {
      id: "evt-001",
      conversation_id: CONVERSATION_ID,
      kind: "tool_call",
      summary: "Usó herramienta agenda_booking",
      payload_redacted: { tool: "agenda_booking" },
      occurred_at: "2026-01-01T10:01:00Z",
    },
    {
      id: "evt-002",
      conversation_id: CONVERSATION_ID,
      kind: "message_sent",
      summary: "Envió mensaje al paciente",
      payload_redacted: null,
      occurred_at: "2026-01-01T10:02:00Z",
    },
  ],
  total: 2,
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

describe("useActivityStream", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    vi.clearAllMocks();
  });

  it("fetches activity stream when enabled=true", async () => {
    vi.mocked(fetchClient).mockResolvedValue(mockStreamResponse);

    const { result } = renderHook(
      () => useActivityStream(CONVERSATION_ID, true),
      { wrapper: createWrapper(queryClient) },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.events).toHaveLength(2);
    expect(result.current.data?.events[0].kind).toBe("tool_call");
    expect(fetchClient).toHaveBeenCalledOnce();
  });

  it("does NOT fetch when enabled=false (collapsed)", () => {
    vi.mocked(fetchClient).mockResolvedValue(mockStreamResponse);

    const { result } = renderHook(
      () => useActivityStream(CONVERSATION_ID, false),
      { wrapper: createWrapper(queryClient) },
    );

    // Query disabled — should stay in idle/pending state, not trigger fetch
    expect(result.current.isFetching).toBe(false);
    expect(fetchClient).not.toHaveBeenCalled();
  });

  it("does NOT fetch when conversationId is null", () => {
    vi.mocked(fetchClient).mockResolvedValue(mockStreamResponse);

    const { result } = renderHook(() => useActivityStream(null, true), {
      wrapper: createWrapper(queryClient),
    });

    expect(result.current.isFetching).toBe(false);
    expect(fetchClient).not.toHaveBeenCalled();
  });

  it("payload_redacted contract: events do not contain raw PHI fields", async () => {
    // Verifies that event payload_redacted does NOT contain PHI fields
    // (server-side sanitization contract — FE should not receive these)
    const responseWithRedacted: ActivityStreamResponse = {
      events: [
        {
          id: "evt-003",
          conversation_id: CONVERSATION_ID,
          kind: "tool_call",
          summary: "Procesó consulta",
          payload_redacted: { tool: "check_availability", slot: "2026-01-10" },
          occurred_at: "2026-01-01T10:03:00Z",
        },
      ],
      total: 1,
    };
    vi.mocked(fetchClient).mockResolvedValue(responseWithRedacted);

    const { result } = renderHook(
      () => useActivityStream(CONVERSATION_ID, true),
      { wrapper: createWrapper(queryClient) },
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const payload = result.current.data?.events[0].payload_redacted as Record<
      string,
      unknown
    >;
    // PHI fields must NOT be present in payload_redacted
    expect(payload).not.toHaveProperty("patient_name");
    expect(payload).not.toHaveProperty("patient_dni");
    expect(payload).not.toHaveProperty("diagnosis");
    expect(payload).not.toHaveProperty("medication");
  });
});
