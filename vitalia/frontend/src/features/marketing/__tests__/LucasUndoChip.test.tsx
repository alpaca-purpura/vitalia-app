/**
 * LucasUndoChip tests — 5-min countdown reads marketing store
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("tok"),
    orgId: "org-1",
    isLoaded: true,
    isSignedIn: true,
  }),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));


// Mock clinic hook
vi.mock("@/hooks/useClinicId", () => ({ useClinicId: () => "clinic-123" }));

// Mock React Query
const mockMutateAsync = vi.fn();
vi.mock("@tanstack/react-query", () => ({
  useMutation: vi.fn(() => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
  })),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

vi.mock("../api/use-undo-recommendation", () => ({
  useUndoRecommendation: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
  }),
}));

// Mock marketing store
const mockClearPendingUndoTimer = vi.fn();
let mockTimerExpiryMs = Date.now() + 5 * 60 * 1000; // 5 minutes from now

vi.mock("../store/marketing-store", () => ({
  useMarketingStore: (selector: (s: unknown) => unknown) =>
    selector({
      pendingUndoTimers: new Map([["rec-1", mockTimerExpiryMs]]),
      bowtieAnimating: false,
      setBowtieAnimating: vi.fn(),
      setPendingUndoTimer: vi.fn(),
      clearPendingUndoTimer: mockClearPendingUndoTimer,
    }),
}));

describe("LucasUndoChip", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockTimerExpiryMs = Date.now() + 5 * 60 * 1000;
    mockMutateAsync.mockResolvedValue({ id: "rec-1", status: "undone" });
  });

  it("test_shows_undo_button_when_timer_active — renders undo chip with countdown (SC-MK-01)", async () => {
    const { LucasUndoChip } = await import("../components/LucasUndoChip");
    render(<LucasUndoChip recId="rec-1" />);

    // Undo button must be visible
    expect(
      screen.getByRole("button", { name: /deshacer/i }),
    ).toBeInTheDocument();
    // Timer countdown text must be present
    expect(screen.getByText(/puedes deshacer hasta/i)).toBeInTheDocument();
  });

  it("test_hidden_when_no_timer — renders nothing when recId not in store", async () => {
    const { LucasUndoChip } = await import("../components/LucasUndoChip");
    const { container } = render(<LucasUndoChip recId="rec-99-no-timer" />);
    // Nothing rendered when no timer entry exists
    expect(container.firstChild).toBeNull();
  });

  it("test_undo_button_calls_mutation — clicking undo calls useUndoRecommendation", async () => {
    const { LucasUndoChip } = await import("../components/LucasUndoChip");
    render(<LucasUndoChip recId="rec-1" />);

    const undoBtn = screen.getByRole("button", { name: /deshacer/i });
    undoBtn.click();

    await vi.waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith({ recId: "rec-1" });
    });
  });
});
