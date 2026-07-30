// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * bloque-popover-delete-scope.test.tsx — TDD RED-first tests for recurrent block
 * delete scope dialog (bug7 round-5 follow-up #1).
 *
 * Covers:
 *   1. recurrent block → delete click shows 3-option scope dialog
 *   2. "Solo este turno" → delete with scope=occurrence + occurrenceDate
 *   3. "Este y los siguientes" → delete with scope=this_and_future + occurrenceDate
 *   4. "Cancelar" → dialog closes, no delete called
 *   5. one_off block → delete click shows simple confirm dialog (no scope options)
 *
 * T-FIX-bug7-round5 vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § SC-3b (eliminar bloque) — round-5 scope dialog
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import React from "react";

// ── next/navigation ────────────────────────────────────────────────────────────
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "t-001" }),
}));

// ── sonner toast ──────────────────────────────────────────────────────────────
vi.mock("sonner", () => ({ toast: { success: vi.fn(), error: vi.fn() } }));

// ── @clerk/nextjs ─────────────────────────────────────────────────────────────
vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn(async () => "test-token"),
    isLoaded: true,
    isSignedIn: true,
  })),
}));
vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));
vi.mock("@/hooks/useClinicId", () => ({ useClinicId: vi.fn(() => "clinic-001") }));

// ── @tanstack/react-query ─────────────────────────────────────────────────────
vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn(),
  useMutation: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
  useQueryClient: vi.fn(() => ({
    invalidateQueries: vi.fn(),
  })),
}));

// ── dnd-kit ───────────────────────────────────────────────────────────────────
vi.mock("@dnd-kit/core", () => ({
  DndContext: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", null, children),
  useDraggable: vi.fn(() => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    isDragging: false,
  })),
  useDroppable: vi.fn(() => ({ isOver: false, setNodeRef: vi.fn() })),
  PointerSensor: class {},
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
}));

// ── store ──────────────────────────────────────────────────────────────────────
const mockStoreState = {
  calendarWeek: "2025-09-01",
  dragDraft: null,
  setCalendarWeek: vi.fn(),
  setDragDraft: vi.fn(),
};
vi.mock("@/features/lisa/store/staff-ui-store", () => ({
  useStaffUiStore: vi.fn(
    (selector: (s: typeof mockStoreState) => unknown) => selector(mockStoreState),
  ),
}));
vi.mock("../../../../store/staff-ui-store", () => ({
  useStaffUiStore: vi.fn(
    (selector: (s: typeof mockStoreState) => unknown) => selector(mockStoreState),
  ),
}));

// ── api/staff mocks ────────────────────────────────────────────────────────────
// Path: src/features/lisa/components/staff/workspace/horarios/__tests__/
// → ../../../../../api/staff = src/features/lisa/api/staff

const mockDeleteMutateAsync = vi.fn();

vi.mock("../../../../../api/staff", () => ({
  useCreateBlock: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
  useUpdateBlock: vi.fn(() => ({
    mutateAsync: vi.fn(),
    isPending: false,
  })),
  useDeleteBlock: vi.fn(() => ({
    mutateAsync: mockDeleteMutateAsync,
    isPending: false,
  })),
  useAvailabilityBlocks: vi.fn(() => ({
    data: [],
    isLoading: false,
    isError: false,
  })),
  useAvailabilityOccurrences: vi.fn(() => ({
    data: [],
    isLoading: false,
    isError: false,
  })),
  staffKeys: {
    all: ["lisa", "staff"],
    lists: () => ["lisa", "staff", "list"],
    list: (f: unknown) => ["lisa", "staff", "list", f],
    details: () => ["lisa", "staff", "detail"],
    detail: (id: string) => ["lisa", "staff", "detail", id],
    blocks: (id: string) => ["lisa", "staff", "detail", id, "blocks"],
    occurrences: (id: string, from: string, to: string) => [
      "lisa", "staff", "detail", id, "occurrences", from, to,
    ],
    occurrencesAll: (id: string) => ["lisa", "staff", "detail", id, "occurrences"],
  },
}));

// ── Static imports after mocks ─────────────────────────────────────────────────
import { BloquePopover } from "../BloquePopover";

// ── Fixtures ───────────────────────────────────────────────────────────────────

const recurrentBlock = {
  id: "blk-rec-001",
  kind: "recurrent" as const,
  daysOfWeek: [0], // Monday
  interval: 1,
  startTime: "09:00",
  endTime: "13:00",
  endConditionKind: "open_ended" as const,
};

const oneOffBlock = {
  id: "blk-one-001",
  kind: "one_off" as const,
  specificDate: "2025-09-01",
  startTime: "09:00",
  endTime: "13:00",
};

// Monday 2025-09-01
const OCCURRENCE_DATE = "2025-09-01";

function renderPopoverWithBlock(
  block: typeof recurrentBlock | typeof oneOffBlock,
  occurrenceDate?: string,
) {
  const onClose = vi.fn();
  render(
    React.createElement(BloquePopover, {
      doctorId: "doctor-123",
      block,
      draft: null,
      isOpen: true,
      onClose,
      anchor: { x: 100, y: 100 },
      calendarWeek: "2025-09-01",
      isExisting: true,
      occurrenceDate,
    }),
  );
  return { onClose };
}

// ── Tests ──────────────────────────────────────────────────────────────────────

describe("BloquePopover — recurrent delete scope dialog (bug7 round-5 #1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockDeleteMutateAsync.mockReset();
    mockDeleteMutateAsync.mockResolvedValue({ deleted: true, preservedAppointments: 0, scope: "occurrence" });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("RED 1: recurrent block → delete click shows scope dialog with 3 options", async () => {
    const user = userEvent.setup();
    renderPopoverWithBlock(recurrentBlock, OCCURRENCE_DATE);

    // Click the delete button in the popover
    const deleteBtn = screen.getByTestId("btn-delete-block");
    await user.click(deleteBtn);

    // Scope dialog should appear
    await waitFor(() => {
      expect(screen.getByTestId("dialog-delete-scope")).toBeTruthy();
    });

    // All 3 scope options present
    expect(screen.getByTestId("btn-delete-occurrence")).toBeTruthy();
    expect(screen.getByTestId("btn-delete-this-and-future")).toBeTruthy();
    expect(screen.getByTestId("btn-delete-scope-cancel")).toBeTruthy();
  });

  it("RED 2: 'Solo este turno' → delete called with scope=occurrence + occurrenceDate", async () => {
    const user = userEvent.setup();
    renderPopoverWithBlock(recurrentBlock, OCCURRENCE_DATE);

    const deleteBtn = screen.getByTestId("btn-delete-block");
    await user.click(deleteBtn);

    await waitFor(() => {
      expect(screen.getByTestId("btn-delete-occurrence")).toBeTruthy();
    });

    await user.click(screen.getByTestId("btn-delete-occurrence"));

    await waitFor(() => {
      expect(mockDeleteMutateAsync).toHaveBeenCalledWith({
        blockId: "blk-rec-001",
        scope: "occurrence",
        occurrenceDate: OCCURRENCE_DATE,
      });
    });
  });

  it("RED 3: 'Este y los siguientes' → delete called with scope=this_and_future + occurrenceDate", async () => {
    const user = userEvent.setup();
    renderPopoverWithBlock(recurrentBlock, OCCURRENCE_DATE);

    const deleteBtn = screen.getByTestId("btn-delete-block");
    await user.click(deleteBtn);

    await waitFor(() => {
      expect(screen.getByTestId("btn-delete-this-and-future")).toBeTruthy();
    });

    await user.click(screen.getByTestId("btn-delete-this-and-future"));

    await waitFor(() => {
      expect(mockDeleteMutateAsync).toHaveBeenCalledWith({
        blockId: "blk-rec-001",
        scope: "this_and_future",
        occurrenceDate: OCCURRENCE_DATE,
      });
    });
  });

  it("RED 4: 'Cancelar' → dialog closes, delete NOT called", async () => {
    const user = userEvent.setup();
    renderPopoverWithBlock(recurrentBlock, OCCURRENCE_DATE);

    const deleteBtn = screen.getByTestId("btn-delete-block");
    await user.click(deleteBtn);

    await waitFor(() => {
      expect(screen.getByTestId("btn-delete-scope-cancel")).toBeTruthy();
    });

    await user.click(screen.getByTestId("btn-delete-scope-cancel"));

    await waitFor(() => {
      expect(screen.queryByTestId("dialog-delete-scope")).toBeFalsy();
    });
    expect(mockDeleteMutateAsync).not.toHaveBeenCalled();
  });

  it("RED 5: one_off block → delete click shows simple confirm (no scope dialog)", async () => {
    const user = userEvent.setup();
    mockDeleteMutateAsync.mockResolvedValue({ deleted: true, preservedAppointments: 0, scope: "series" });
    renderPopoverWithBlock(oneOffBlock);

    const deleteBtn = screen.getByTestId("btn-delete-block");
    await user.click(deleteBtn);

    // Simple warning dialog, not the scope dialog
    await waitFor(() => {
      // No scope dialog
      expect(screen.queryByTestId("dialog-delete-scope")).toBeFalsy();
      // Simple confirm present
      expect(screen.getByTestId("btn-delete-confirm")).toBeTruthy();
    });
  });

  it("RED 6: one_off delete confirm → delete called with only blockId (no scope params)", async () => {
    const user = userEvent.setup();
    mockDeleteMutateAsync.mockResolvedValue({ deleted: true, preservedAppointments: 0, scope: "series" });
    renderPopoverWithBlock(oneOffBlock);

    const deleteBtn = screen.getByTestId("btn-delete-block");
    await user.click(deleteBtn);

    await waitFor(() => {
      expect(screen.getByTestId("btn-delete-confirm")).toBeTruthy();
    });

    await user.click(screen.getByTestId("btn-delete-confirm"));

    await waitFor(() => {
      expect(mockDeleteMutateAsync).toHaveBeenCalledWith({
        blockId: "blk-one-001",
      });
    });
  });
});
