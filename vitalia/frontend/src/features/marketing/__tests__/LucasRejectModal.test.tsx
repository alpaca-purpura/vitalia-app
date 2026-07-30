/**
 * LucasRejectModal tests — RHF + Zod reason enum validation (SC-MK-01)
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// Mock nuqs
vi.mock("nuqs", () => ({
  useQueryState: () => [null, vi.fn()],
  parseAsStringEnum: () => ({ withDefault: (d: unknown) => d }),
  parseAsString: { withDefault: (d: unknown) => d },
}));

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
  useQuery: vi.fn(),
  useMutation: vi.fn(() => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
    error: null,
  })),
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

vi.mock("../api/use-reject-recommendation", () => ({
  useRejectRecommendation: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
  }),
}));

describe("LucasRejectModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMutateAsync.mockResolvedValue({ id: "rec-1", status: "rejected" });
  });

  it("test_renders_reason_select — reason dropdown renders all 5 options", async () => {
    const { LucasRejectModal } = await import("../components/LucasRejectModal");
    render(<LucasRejectModal recId="rec-1" onClose={vi.fn()} />);

    expect(screen.getByRole("dialog")).toBeInTheDocument();
    // Expect a combobox (Select) or radio group for reasons
    expect(screen.getByText(/no es prioridad ahora/i)).toBeInTheDocument();
    expect(screen.getByText(/ya lo estamos haciendo/i)).toBeInTheDocument();
    expect(screen.getByText(/los datos son incorrectos/i)).toBeInTheDocument();
    expect(screen.getByText(/es demasiado arriesgado/i)).toBeInTheDocument();
    expect(screen.getByText(/otro motivo/i)).toBeInTheDocument();
  });

  it("test_submit_without_reason_shows_error — Zod validation blocks submit with no reason", async () => {
    const { LucasRejectModal } = await import("../components/LucasRejectModal");
    render(<LucasRejectModal recId="rec-1" onClose={vi.fn()} />);

    const submitBtn = screen.getByRole("button", { name: /rechazar/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      // Should NOT call mutation
      expect(mockMutateAsync).not.toHaveBeenCalled();
    });
  });

  it("test_submit_with_valid_reason_calls_mutation — selecting reason + submit invokes mutation", async () => {
    const user = userEvent.setup();
    const { LucasRejectModal } = await import("../components/LucasRejectModal");
    render(<LucasRejectModal recId="rec-1" onClose={vi.fn()} />);

    // Select a reason option using userEvent (properly triggers React state)
    const notPriorityLabel = screen.getByText(/no es prioridad ahora/i);
    await user.click(notPriorityLabel);

    const submitBtn = screen.getByRole("button", { name: /rechazar/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({ recId: "rec-1", reason: "not_priority" }),
      );
    });
  });

  it("test_cancel_closes_modal — cancel button triggers onClose", async () => {
    const { LucasRejectModal } = await import("../components/LucasRejectModal");
    const onClose = vi.fn();
    render(<LucasRejectModal recId="rec-1" onClose={onClose} />);

    const cancelBtn = screen.getByRole("button", { name: /cancelar/i });
    fireEvent.click(cancelBtn);

    expect(onClose).toHaveBeenCalled();
  });
});
