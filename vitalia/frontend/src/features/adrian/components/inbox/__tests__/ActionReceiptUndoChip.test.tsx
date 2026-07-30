/**
 * ActionReceiptUndoChip.test.tsx
 *
 * SC-01 coverage: countdown visible after agent_ai message send.
 * Gherkin: test_5min_countdown — chip shows countdown; disappears on expire.
 *
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ActionReceiptUndoChip } from "../ActionReceiptUndoChip";

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


// Mock useClinicId
vi.mock("@/hooks/useClinicId", () => ({
  useClinicId: () => "clinic_test",
}));

// Mock fetchClient
vi.mock("@/lib/api/fetchClient", () => ({
  fetchClient: vi.fn(async () => ({
    message: { id: "msg-1", retracted_at: new Date().toISOString() },
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

// Mock @tanstack/react-query invalidation (allow mutations to run)
vi.mock("@tanstack/react-query", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@tanstack/react-query")>();
  return { ...actual };
});

function makeExpiresAt(secondsFromNow: number): string {
  return new Date(Date.now() + secondsFromNow * 1000).toISOString();
}

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("ActionReceiptUndoChip", () => {
  beforeEach(() => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });
  afterEach(() => {
    vi.useRealTimers();
  });

  /**
   * SC-01 gherkin test_5min_countdown
   * Given: a message with action_receipt_expires_at 5 minutes in future
   * When: ActionReceiptUndoChip is rendered
   * Then: countdown shows formatted time and chip is visible
   */
  it("test_5min_countdown — shows countdown label when within window", () => {
    const expiresAt = makeExpiresAt(298); // ~4:58
    render(
      <ActionReceiptUndoChip
        messageId="msg-1"
        conversationId="conv-1"
        expiresAt={expiresAt}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );

    // Chip is visible with "Revertir" label
    expect(screen.getByText("Revertir")).toBeInTheDocument();
    // Timer element exists
    const timer = screen.getByRole("timer");
    expect(timer).toBeInTheDocument();
    // Shows formatted time (something like 4:58)
    expect(timer.textContent).toMatch(/\(\d+:\d{2}\)/);
  });

  it("disappears when timer expires", async () => {
    const expiresAt = makeExpiresAt(2); // 2 seconds
    const { container } = render(
      <ActionReceiptUndoChip
        messageId="msg-1"
        conversationId="conv-1"
        expiresAt={expiresAt}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );

    // Initially visible
    expect(screen.getByText("Revertir")).toBeInTheDocument();

    // Advance timer by 3 seconds (expires)
    await act(async () => {
      vi.advanceTimersByTime(3000);
    });

    // Chip should be gone
    expect(container.querySelector("button")).toBeNull();
  });

  it("opens confirm dialog on click", async () => {
    const user = userEvent.setup({ delay: null });
    const expiresAt = makeExpiresAt(300);
    render(
      <ActionReceiptUndoChip
        messageId="msg-1"
        conversationId="conv-1"
        expiresAt={expiresAt}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );

    await act(async () => {
      await user.click(screen.getByRole("button", { name: /revertir/i }));
    });

    // Dialog should appear with confirm + cancel
    expect(screen.getByText("Sí, revertir")).toBeInTheDocument();
    expect(screen.getByText("Cancelar")).toBeInTheDocument();
  });

  it("renders nothing when expiresAt is null", () => {
    const { container } = render(
      <ActionReceiptUndoChip
        messageId="msg-1"
        conversationId="conv-1"
        expiresAt={null as unknown as string}
        conversationUpdatedAt="2026-01-01T00:00:00Z"
      />,
      { wrapper },
    );
    expect(container.firstChild).toBeNull();
  });
});
