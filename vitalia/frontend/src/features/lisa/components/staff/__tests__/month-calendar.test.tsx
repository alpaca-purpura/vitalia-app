// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * month-calendar.test.tsx — Vitest RED-first TDD tests for MonthCalendar + D3-E toggle.
 *
 * T-FE-vista-mes vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-E · validators: RN-D3E-1, RN-D3E-2, SC-D3E-1..4
 *
 * TDD order: RED (write failing tests) → GREEN (implement) → REFACTOR.
 * These tests exercise:
 *   - MonthCalendar renders correct 6×7 grid structure
 *   - Chips appear on EXACTLY the dates returned by useAvailabilityOccurrences (RN-D3E-1)
 *   - Click day → onSwitchToWeek called with correct Monday ISO (SC-D3E-2)
 *   - Empty month renders empty state (SC-D3E-3)
 *   - Overflow "+N más" for >MAX_CHIPS_PER_DAY (SC-D3E-4)
 *   - Month navigation: prev, hoy, next
 *   - Skeleton loading state
 *   - Error state + retry
 *   - DoctorHorariosView toggle Semana|Mes
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import React from "react";

// ── Mocks (declared before static imports) ───────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: vi.fn(() => ({
    getToken: vi.fn(async () => "test-token"),
    isLoaded: true,
    isSignedIn: true,
  })),
}));

vi.mock("@/hooks/useTenantId", () => ({ useTenantId: () => "mock-tenant-id" }));
vi.mock("@/hooks/useClinicId", () => ({ useClinicId: vi.fn(() => "clinic-001") }));

// Staff UI store mock
const mockStoreState = {
  calendarWeek: "2025-11-03", // Monday 2025-11-03
  dragDraft: null as null | { dayOfWeek: number; startHour: number; endHour: number },
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

// dnd-kit mock (MonthCalendar does NOT use DnD — but AvailabilityCalendar does)
vi.mock("@dnd-kit/core", () => ({
  DndContext: ({ children }: { children: React.ReactNode }) =>
    React.createElement("div", { "data-testid": "dnd-context" }, children),
  useDraggable: vi.fn(() => ({ attributes: {}, listeners: {}, setNodeRef: vi.fn(), transform: null, isDragging: false })),
  useDroppable: vi.fn(() => ({ isOver: false, setNodeRef: vi.fn() })),
  PointerSensor: class {},
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
}));

// useAvailabilityOccurrences mock (controllable per test)
const mockUseAvailabilityOccurrences = vi.fn(() => ({
  data: [] as import("../../../types/staff.types").AvailabilityOccurrence[],
  isLoading: false,
  isError: false,
  refetch: vi.fn(),
}));

vi.mock("../../../api/staff", () => ({
  useAvailabilityOccurrences: (..._args: unknown[]) => mockUseAvailabilityOccurrences(),
  useAvailabilityBlocks: vi.fn(() => ({ data: [], isLoading: false, isError: false })),
  useCreateBlock: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useUpdateBlock: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  useDeleteBlock: vi.fn(() => ({ mutateAsync: vi.fn(), isPending: false })),
  staffKeys: {
    all: ["lisa", "staff"],
    lists: () => ["lisa", "staff", "list"],
    list: (f: unknown) => ["lisa", "staff", "list", f],
    details: () => ["lisa", "staff", "detail"],
    detail: (id: string) => ["lisa", "staff", "detail", id],
    blocks: (id: string) => ["lisa", "staff", "detail", id, "blocks"],
    occurrences: (id: string, from: string, to: string) => ["lisa", "staff", "detail", id, "occurrences", from, to],
  },
}));

// ── Static imports (after mocks) ─────────────────────────────────────────────

import { MonthCalendar } from "../workspace/horarios/MonthCalendar";
import { DoctorHorariosView } from "../workspace/horarios/DoctorHorariosView";
import type { AvailabilityOccurrence } from "../../../types/staff.types";

// ── Helper ────────────────────────────────────────────────────────────────────

function makeOccurrence(
  occurrenceDate: string,
  blockId = "blk-001",
): AvailabilityOccurrence {
  return {
    blockId,
    occurrenceDate,
    startTime: "09:00",
    endTime: "13:00",
    kind: "recurrent",
    freq: "weekly",
    patternSummary: "Semanal",
  };
}

// ── MonthCalendar — grid structure ────────────────────────────────────────────

describe("MonthCalendar — grid structure", () => {
  beforeEach(() => {
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
  });

  it("renders the month calendar container", () => {
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );
    expect(screen.getByTestId("month-calendar")).toBeTruthy();
  });

  it("renders day-of-week headers (Lun..Dom)", () => {
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );
    expect(screen.getByText("Lun")).toBeTruthy();
    expect(screen.getByText("Mar")).toBeTruthy();
    expect(screen.getByText("Dom")).toBeTruthy();
  });

  it("renders 6×7=42 day cells for November 2025", () => {
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );
    const cells = screen.getAllByTestId(/^month-day-/);
    expect(cells.length).toBe(42);
  });

  it("renders month nav buttons: prev, hoy, next", () => {
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );
    expect(screen.getByTestId("month-nav-prev")).toBeTruthy();
    expect(screen.getByTestId("month-nav-hoy")).toBeTruthy();
    expect(screen.getByTestId("month-nav-next")).toBeTruthy();
  });

  it("renders month+year label", () => {
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );
    const label = screen.getByTestId("month-label");
    expect(label.textContent).toMatch(/noviembre/i);
    expect(label.textContent).toMatch(/2025/);
  });
});

// ── MonthCalendar — RN-D3E-1: EXACTLY projected occurrences ──────────────────

describe("MonthCalendar — RN-D3E-1: paint exactly BE-projected occurrences", () => {
  it("shows chips on exactly 2 dates when occurrences=2 (SC-D3E-1)", () => {
    const occ1 = makeOccurrence("2025-11-10", "blk-001");
    const occ2 = makeOccurrence("2025-11-17", "blk-001");
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [occ1, occ2],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );

    // day-10 cell has chip, day-17 cell has chip
    const day10 = screen.getByTestId("month-day-2025-11-10");
    const day17 = screen.getByTestId("month-day-2025-11-17");
    expect(within(day10).getAllByTestId(/^month-chip-/).length).toBe(1);
    expect(within(day17).getAllByTestId(/^month-chip-/).length).toBe(1);
  });

  it("shows NO chips on days outside projected occurrences (RN-D3E-1 — zero extra dates)", () => {
    const occ1 = makeOccurrence("2025-11-10", "blk-001");
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [occ1],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );

    // day-17 should have NO chip
    const day17 = screen.getByTestId("month-day-2025-11-17");
    const chipsIn17 = within(day17).queryAllByTestId(/^month-chip-/);
    expect(chipsIn17.length).toBe(0);
  });

  it("chip text shows time range (HH:mm–HH:mm)", () => {
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [makeOccurrence("2025-11-10")],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );

    const chip = screen.getByTestId("month-chip-2025-11-10-blk-001");
    expect(chip.textContent).toMatch(/09:00/);
    expect(chip.textContent).toMatch(/13:00/);
  });
});

// ── MonthCalendar — SC-D3E-2: click day → switch to week ─────────────────────

describe("MonthCalendar — SC-D3E-2: click day triggers onSwitchToWeek", () => {
  beforeEach(() => {
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
  });

  it("clicking a day cell calls onSwitchToWeek with the Monday of that week", () => {
    const onSwitchToWeek = vi.fn();
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek,
      }),
    );

    // 2025-11-10 is a Monday → expect "2025-11-10"
    const day10 = screen.getByTestId("month-day-2025-11-10");
    fireEvent.click(day10);
    expect(onSwitchToWeek).toHaveBeenCalledWith("2025-11-10");
  });

  it("clicking 2025-11-12 (Wednesday) calls onSwitchToWeek with Monday 2025-11-10", () => {
    const onSwitchToWeek = vi.fn();
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek,
      }),
    );

    const day12 = screen.getByTestId("month-day-2025-11-12");
    fireEvent.click(day12);
    expect(onSwitchToWeek).toHaveBeenCalledWith("2025-11-10");
  });
});

// ── MonthCalendar — SC-D3E-3: empty state ────────────────────────────────────

describe("MonthCalendar — SC-D3E-3: empty state", () => {
  it("renders empty-state message when month has no occurrences", () => {
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );

    expect(screen.getByTestId("month-empty-state")).toBeTruthy();
  });

  it("does NOT show empty state when there are occurrences", () => {
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [makeOccurrence("2025-11-10")],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );

    expect(screen.queryByTestId("month-empty-state")).toBeNull();
  });
});

// ── MonthCalendar — SC-D3E-4: overflow "+N más" ───────────────────────────────

describe("MonthCalendar — SC-D3E-4: overflow +N más", () => {
  it("shows +N más when day has >2 occurrences (MAX_CHIPS_PER_DAY=2)", () => {
    // 3 occurrences on the same day
    const occs: AvailabilityOccurrence[] = [
      { blockId: "blk-001", occurrenceDate: "2025-11-10", startTime: "08:00", endTime: "09:00", kind: "recurrent", freq: "weekly", patternSummary: "" },
      { blockId: "blk-002", occurrenceDate: "2025-11-10", startTime: "10:00", endTime: "11:00", kind: "recurrent", freq: "weekly", patternSummary: "" },
      { blockId: "blk-003", occurrenceDate: "2025-11-10", startTime: "12:00", endTime: "13:00", kind: "one_off", freq: null, patternSummary: "" },
    ];

    mockUseAvailabilityOccurrences.mockReturnValue({
      data: occs,
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });

    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );

    const day10 = screen.getByTestId("month-day-2025-11-10");
    // Should show 2 chips + 1 overflow
    const chips = within(day10).getAllByTestId(/^month-chip-/);
    expect(chips.length).toBe(2);
    const overflow = within(day10).getByTestId("month-overflow-2025-11-10");
    expect(overflow.textContent).toMatch(/\+1/);
  });
});

// ── MonthCalendar — loading skeleton ─────────────────────────────────────────

describe("MonthCalendar — loading skeleton", () => {
  it("renders skeleton when isLoading=true", () => {
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [],
      isLoading: true,
      isError: false,
      refetch: vi.fn(),
    });

    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );

    expect(screen.getByTestId("month-skeleton")).toBeTruthy();
    expect(screen.queryByTestId("month-calendar")).toBeNull();
  });
});

// ── MonthCalendar — error state ───────────────────────────────────────────────

describe("MonthCalendar — error + retry", () => {
  it("renders error state when isError=true", () => {
    const refetch = vi.fn();
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [],
      isLoading: false,
      isError: true,
      refetch,
    });

    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );

    expect(screen.getByTestId("month-error-state")).toBeTruthy();
    const retryBtn = screen.getByTestId("month-retry-btn");
    fireEvent.click(retryBtn);
    expect(refetch).toHaveBeenCalled();
  });
});

// ── MonthCalendar — month navigation ─────────────────────────────────────────

describe("MonthCalendar — navigation", () => {
  beforeEach(() => {
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
  });

  it("clicking next updates month label to following month", () => {
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );
    const nextBtn = screen.getByTestId("month-nav-next");
    fireEvent.click(nextBtn);
    const label = screen.getByTestId("month-label");
    expect(label.textContent).toMatch(/diciembre/i);
  });

  it("clicking prev updates month label to previous month", () => {
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );
    const prevBtn = screen.getByTestId("month-nav-prev");
    fireEvent.click(prevBtn);
    const label = screen.getByTestId("month-label");
    expect(label.textContent).toMatch(/octubre/i);
  });

  it("clicking hoy resets to current month", () => {
    render(
      React.createElement(MonthCalendar, {
        doctorId: "doctor-123",
        currentMonth: "2025-11-01",
        onSwitchToWeek: vi.fn(),
      }),
    );
    // Navigate away first
    fireEvent.click(screen.getByTestId("month-nav-next"));
    // Now click hoy
    fireEvent.click(screen.getByTestId("month-nav-hoy"));
    const label = screen.getByTestId("month-label");
    // Current date is 2026-06-12, so "hoy" should show junio 2026
    expect(label.textContent).toMatch(/2026/);
  });
});

// ── DoctorHorariosView — Semana|Mes toggle ────────────────────────────────────

describe("DoctorHorariosView — Semana|Mes toggle (D3-E)", () => {
  beforeEach(() => {
    mockUseAvailabilityOccurrences.mockReturnValue({
      data: [],
      isLoading: false,
      isError: false,
      refetch: vi.fn(),
    });
  });

  it("renders Semana and Mes toggle pills", () => {
    render(React.createElement(DoctorHorariosView, { doctorId: "doctor-123" }));
    expect(screen.getByTestId("toggle-semana")).toBeTruthy();
    expect(screen.getByTestId("toggle-mes")).toBeTruthy();
  });

  it("default view is Semana (week calendar visible)", () => {
    render(React.createElement(DoctorHorariosView, { doctorId: "doctor-123" }));
    // Week calendar has availability-calendar testid
    expect(screen.getByTestId("availability-calendar")).toBeTruthy();
    expect(screen.queryByTestId("month-calendar")).toBeNull();
  });

  it("clicking Mes shows month calendar and hides week calendar", () => {
    render(React.createElement(DoctorHorariosView, { doctorId: "doctor-123" }));
    const mesToggle = screen.getByTestId("toggle-mes");
    fireEvent.click(mesToggle);
    expect(screen.getByTestId("month-calendar")).toBeTruthy();
    expect(screen.queryByTestId("availability-calendar")).toBeNull();
  });

  it("switching from Mes back to Semana shows week calendar again", () => {
    render(React.createElement(DoctorHorariosView, { doctorId: "doctor-123" }));
    fireEvent.click(screen.getByTestId("toggle-mes"));
    fireEvent.click(screen.getByTestId("toggle-semana"));
    expect(screen.getByTestId("availability-calendar")).toBeTruthy();
    expect(screen.queryByTestId("month-calendar")).toBeNull();
  });

  it("clicking a day in month view switches back to Semana (onSwitchToWeek)", () => {
    render(React.createElement(DoctorHorariosView, { doctorId: "doctor-123" }));
    // Switch to Mes
    fireEvent.click(screen.getByTestId("toggle-mes"));
    // Click a day cell — 2026-06-10 (the current month the component will show)
    // We need to find ANY day cell in the current month
    const anyCells = screen.getAllByTestId(/^month-day-/);
    expect(anyCells.length).toBeGreaterThan(0);
    fireEvent.click(anyCells[0]!);
    // Should switch to week view
    expect(screen.getByTestId("availability-calendar")).toBeTruthy();
    expect(screen.queryByTestId("month-calendar")).toBeNull();
    // setCalendarWeek should have been called
    expect(mockStoreState.setCalendarWeek).toHaveBeenCalled();
  });
});
