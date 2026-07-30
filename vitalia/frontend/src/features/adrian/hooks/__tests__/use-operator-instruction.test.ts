// cap: adrian.inbox
/**
 * use-operator-instruction.test.ts — RED-first TDD tests for useOperatorInstruction hook.
 *
 * SC-8 coverage: instruction mode + POST mutation + cache invalidation.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement } from "react";

// ── Mocks ─────────────────────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: async () => "mock-token",
    isLoaded: true,
    isSignedIn: true,
  }),
}));

vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: () => "mock-tenant-id",
}));

const mockSet = vi.fn();
vi.mock("../../api/operator-instruction", () => ({
  operatorInstructionApi: {
    set: (...args: unknown[]) => mockSet(...args),
  },
}));

// ── Wrapper ───────────────────────────────────────────────────────────────────

function makeWrapper() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return {
    wrapper: ({ children }: { children: React.ReactNode }) =>
      createElement(QueryClientProvider, { client: qc }, children),
    qc,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useOperatorInstruction", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("exposes a mutate function", async () => {
    const { useOperatorInstruction } = await import(
      "../use-operator-instruction"
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useOperatorInstruction(), { wrapper });
    expect(typeof result.current.mutate).toBe("function");
  });

  it("calls operatorInstructionApi.set with token + tenantId + payload on mutate", async () => {
    mockSet.mockResolvedValueOnce({
      conversationId: "conv-1",
      instructionActive: true,
      updatedAt: "2026-01-01T00:00:00Z",
    });

    const { useOperatorInstruction } = await import(
      "../use-operator-instruction"
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useOperatorInstruction(), { wrapper });

    await act(async () => {
      result.current.mutate({
        conversationId: "conv-1",
        instruction: "Ofrécele 10% de descuento",
      });
    });

    expect(mockSet).toHaveBeenCalledWith("mock-token", "mock-tenant-id", {
      conversationId: "conv-1",
      instruction: "Ofrécele 10% de descuento",
    });
  });

  it("is idle initially (not loading)", async () => {
    const { useOperatorInstruction } = await import(
      "../use-operator-instruction"
    );
    const { wrapper } = makeWrapper();
    const { result } = renderHook(() => useOperatorInstruction(), { wrapper });
    expect(result.current.isPending).toBe(false);
  });
});

// ── effectiveMode logic tests (pure — no hook needed) ─────────────────────────

describe("getEffectiveMode (composer mode logic)", () => {
  it("returns 'direct' when handler_mode is 'human' (Adrián paused)", async () => {
    const { getEffectiveMode } = await import("../use-operator-instruction");
    expect(getEffectiveMode("human")).toBe("direct");
  });

  it("returns 'instruction' when handler_mode is 'ai' (Adrián decide)", async () => {
    const { getEffectiveMode } = await import("../use-operator-instruction");
    expect(getEffectiveMode("ai")).toBe("instruction");
  });
});
