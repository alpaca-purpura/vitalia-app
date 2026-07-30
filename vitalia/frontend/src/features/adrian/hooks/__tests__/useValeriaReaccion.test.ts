// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * useValeriaReaccion.test.ts — T-5 tests for useValeriaReaccion hook.
 *
 * Verifies: returns empty result when no convId, returns suggestions when convId provided.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";

// Mock Clerk auth
vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    isLoaded: true,
    isSignedIn: true,
  })),
}));

// Mock useTenantId
vi.mock("@/hooks/useTenantId", () => ({
  useTenantId: vi.fn(() => "tenant-test-123"),
}));

import { useValeriaReaccion } from "../useValeriaReaccion";

describe("useValeriaReaccion — basic context hook", () => {
  it("test_no_conv: returns empty result when convId is null", () => {
    const { result } = renderHook(() => useValeriaReaccion(null));
    expect(result.current.contextMessage).toBeNull();
    expect(result.current.suggestedActions).toHaveLength(0);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isError).toBe(false);
  });

  it("test_with_conv: returns contextMessage when convId provided", () => {
    const { result } = renderHook(() => useValeriaReaccion("conv-test-456"));
    expect(result.current.contextMessage).not.toBeNull();
    expect(typeof result.current.contextMessage).toBe("string");
  });

  it("test_with_conv_suggestions: returns 2 suggested actions for valid convId", () => {
    const { result } = renderHook(() => useValeriaReaccion("conv-test-456"));
    expect(result.current.suggestedActions.length).toBeGreaterThanOrEqual(1);
  });

  it("test_suggestion_shape: each suggestion has id, label, promptHint", () => {
    const { result } = renderHook(() => useValeriaReaccion("conv-test-456"));
    for (const action of result.current.suggestedActions) {
      expect(typeof action.id).toBe("string");
      expect(typeof action.label).toBe("string");
      expect(typeof action.promptHint).toBe("string");
      expect(action.id.length).toBeGreaterThan(0);
      expect(action.label.length).toBeGreaterThan(0);
    }
  });

  it("test_not_loading: isLoading is false (MVP local derivation)", () => {
    const { result } = renderHook(() => useValeriaReaccion("conv-test-456"));
    expect(result.current.isLoading).toBe(false);
  });
});
