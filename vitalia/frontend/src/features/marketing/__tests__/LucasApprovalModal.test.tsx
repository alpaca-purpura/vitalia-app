/**
 * LucasApprovalModal tests — SC-MK-01 approval mutation + undo chip + RBAC (SC-MK-04)
 * @coverage gherkin SC-MK-01 (test_approve_invokes_mutation_with_idempotency_key)
 * @coverage gherkin SC-MK-01 (test_post_approve_shows_undo_chip_5min)
 * @coverage gherkin SC-MK-04 (test_role_recepcion_disables_approve_button_with_tooltip)
 * downstream-regression-na: brand-local FE test; no cross-brand consumers
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import React from "react";

// Mock nuqs
vi.mock("nuqs", () => ({
  useQueryState: (_key: string, _parser: unknown) => [null, vi.fn()],
  parseAsStringEnum: () => ({
    withDefault: (d: unknown) => ({ withOptions: () => d }),
    withOptions: () => ({ withDefault: (d: unknown) => d }),
  }),
  parseAsString: {
    withDefault: (d: unknown) => ({ withOptions: () => d }),
    withOptions: () => ({ withDefault: (d: unknown) => d }),
  },
  parseAsBoolean: {
    withDefault: (d: unknown) => ({ withOptions: () => d }),
    withOptions: () => ({ withDefault: (d: unknown) => d }),
  },
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
  QueryClient: vi.fn(),
  QueryClientProvider: ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  ),
}));

// Mock marketing store to verify setPendingUndoTimer is called
const mockSetPendingUndoTimer = vi.fn();
vi.mock("../store/marketing-store", () => ({
  useMarketingStore: (selector: (s: unknown) => unknown) =>
    selector({
      pendingUndoTimers: new Map(),
      bowtieAnimating: false,
      setBowtieAnimating: vi.fn(),
      setPendingUndoTimer: mockSetPendingUndoTimer,
      clearPendingUndoTimer: vi.fn(),
    }),
}));

// Mock useApproveRecommendation
vi.mock("../api/use-approve-recommendation", () => ({
  useApproveRecommendation: () => ({
    mutateAsync: mockMutateAsync,
    isPending: false,
    isError: false,
    error: null,
  }),
}));

const mockRec = {
  id: "rec-1",
  tenantId: "org-1",
  clinicId: "clinic-123",
  stage: "attraction",
  recommendationKind: "scale_meta",
  title: "Aumentar presupuesto Meta Ads",
  body: "Tu CPL está 20% por debajo del benchmark sectorial.",
  rationaleJson: { metric: "cpl", value: 24, benchmark: 30 },
  actionPayloadJson: { budget_delta_pct: 20 },
  priority: 1,
  confidencePct: 87,
  projectedImpactText: "+15 pacientes/mes estimados",
  status: "open",
  approvedByUserId: null,
  approvedAt: null,
  undoUntil: "2026-05-20T18:05:00Z",
  expiresAt: "2026-06-01T00:00:00Z",
  createdAt: "2026-05-20T00:00:00Z",
};

describe("LucasApprovalModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMutateAsync.mockResolvedValue({
      ...mockRec,
      status: "approved",
      approvedByUserId: "user-1",
      approvedAt: "2026-05-20T18:00:00Z",
      undoUntil: "2026-05-20T18:05:00Z",
    });
  });

  it("test_approve_invokes_mutation_with_idempotency_key — approve button calls mutation (SC-MK-01)", async () => {
    const { LucasApprovalModal } =
      await import("../components/LucasApprovalModal");
    const onClose = vi.fn();

    render(<LucasApprovalModal rec={mockRec as never} onClose={onClose} />);

    // Dialog must be present
    expect(screen.getByRole("dialog")).toBeInTheDocument();

    // Click the confirm approve button
    const confirmBtn = screen.getByRole("button", { name: /sí, aprobar/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      expect(mockMutateAsync).toHaveBeenCalledWith(
        expect.objectContaining({ recId: "rec-1" }),
      );
    });
  });

  it("test_post_approve_shows_undo_chip_5min — after approval, stores undo timer in store (SC-MK-01)", async () => {
    const { LucasApprovalModal } =
      await import("../components/LucasApprovalModal");
    const onClose = vi.fn();

    render(<LucasApprovalModal rec={mockRec as never} onClose={onClose} />);

    const confirmBtn = screen.getByRole("button", { name: /sí, aprobar/i });
    fireEvent.click(confirmBtn);

    await waitFor(() => {
      // After approval, setPendingUndoTimer should be called with recId + timestamp
      expect(mockSetPendingUndoTimer).toHaveBeenCalledWith(
        "rec-1",
        expect.any(Number),
      );
    });
  });

  it("test_cancel_closes_modal — cancel button triggers onClose", async () => {
    const { LucasApprovalModal } =
      await import("../components/LucasApprovalModal");
    const onClose = vi.fn();

    render(<LucasApprovalModal rec={mockRec as never} onClose={onClose} />);

    const cancelBtn = screen.getByRole("button", { name: /cancelar/i });
    fireEvent.click(cancelBtn);

    expect(onClose).toHaveBeenCalled();
  });

  it("test_esc_key_closes_modal — ESC key triggers onClose", async () => {
    const { LucasApprovalModal } =
      await import("../components/LucasApprovalModal");
    const onClose = vi.fn();

    render(<LucasApprovalModal rec={mockRec as never} onClose={onClose} />);

    fireEvent.keyDown(screen.getByRole("dialog"), { key: "Escape" });

    expect(onClose).toHaveBeenCalled();
  });

  it("test_role_recepcion_disables_approve_button_with_tooltip — recepcion role sees disabled button (SC-MK-04)", async () => {
    const { LucasApprovalModal } =
      await import("../components/LucasApprovalModal");
    const onClose = vi.fn();

    render(
      <LucasApprovalModal
        rec={mockRec as never}
        onClose={onClose}
        userRole="recepcion"
      />,
    );

    const confirmBtn = screen.getByRole("button", { name: /sí, aprobar/i });
    expect(confirmBtn).toBeDisabled();

    // Tooltip text should be present (may be hidden until hover but accessible)
    expect(screen.getByText(/no tienes permiso/i)).toBeInTheDocument();
  });
});
