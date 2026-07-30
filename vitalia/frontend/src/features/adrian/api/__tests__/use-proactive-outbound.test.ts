/**
 * use-proactive-outbound.test.ts — Tests for useProactiveOutbound hook.
 *
 * Covers:
 * - Happy path: sends proactive outbound → new conversation created
 * - Sends correct payload (lead_id, template_id, channel, template_vars)
 * - Invalidates conversations list on settle
 * - Error: ComplianceService blocked (422 from server) handled gracefully
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";
import { useProactiveOutbound } from "../use-proactive-outbound";
import { ApiError } from "@/lib/api/fetchClient";

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

function createWrapper(queryClient: QueryClient) {
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return createElement(
      QueryClientProvider,
      { client: queryClient },
      children,
    );
  };
}

describe("useProactiveOutbound", () => {
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

  it("sends proactive outbound and returns new conversation", async () => {
    const mockConversation = {
      id: "conv-new-001",
      lead_id: "lead-target",
      channel: "whatsapp",
      status: "active",
      handler_mode: "ai",
    };
    vi.mocked(fetchClient).mockResolvedValue({
      conversation: mockConversation,
    });

    const { result } = renderHook(() => useProactiveOutbound(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.mutate({
        leadId: "lead-target",
        templateId: "tmpl-bienvenida",
        templateVars: { patient_name: "Ana" },
        channel: "whatsapp",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.conversation).toMatchObject({
      id: "conv-new-001",
    });
    expect(fetchClient).toHaveBeenCalledWith(
      "/api/v1/vitalia/inbox/proactive-outbound",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          lead_id: "lead-target",
          template_id: "tmpl-bienvenida",
          template_vars: { patient_name: "Ana" },
          channel: "whatsapp",
        }),
      }),
    );
  });

  it("invalidates conversations list after success", async () => {
    vi.mocked(fetchClient).mockResolvedValue({
      conversation: { id: "conv-new-002" },
    });
    const invalidateSpy = vi.spyOn(queryClient, "invalidateQueries");

    const { result } = renderHook(() => useProactiveOutbound(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.mutate({
        leadId: "lead-target",
        templateId: "tmpl-foo",
        channel: "whatsapp",
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(invalidateSpy).toHaveBeenCalledWith(
      expect.objectContaining({ queryKey: ["adrian", "inbox", "conversations"] }),
    );
  });

  it("handles ComplianceService block error (422) gracefully", async () => {
    const complianceError = new ApiError({
      status: 422,
      statusText: "Unprocessable Entity",
    } as unknown as Response);
    vi.mocked(fetchClient).mockRejectedValue(complianceError);

    const { result } = renderHook(() => useProactiveOutbound(), {
      wrapper: createWrapper(queryClient),
    });

    await act(async () => {
      result.current.mutate({
        leadId: "lead-target",
        templateId: "tmpl-medical",
        channel: "whatsapp",
      });
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as ApiError).status).toBe(422);
  });
});
