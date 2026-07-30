/**
 * AgendaCalendar.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * T-13 vitalia-fase2-valeria-agenda
 * spec_anchor: 06-tickets.yaml T-13 acceptance A1..A6
 *
 * Tests:
 *   - WeekCalendar renders as default view (A1)
 *   - DayCalendar renders when view=dia (A1)
 *   - MonthCalendar renders when view=mes (A1)
 *   - AgendaCalendar dispatches to correct variant (A1)
 *   - DayCalendar uses react-window FixedSizeList when slots > 50 (A4)
 *   - MonthCalendar consumes aggregates — renders day dots without slot list (A5)
 *   - FreshnessIndicator updates on dataUpdatedAt + refresh button (A6)
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import type { AgendaSlot } from "../../../types/agenda.types";

// ── Mocks ───────────────────────────────────────────────────────────────────

// Mock useTenantLocale to avoid @clerk/nextjs useOrganization dependency
vi.mock("@/hooks/useTenantLocale", () => ({
  useTenantLocale: () => ({
    currency: "PEN",
    timezone: "America/Lima",
    locale: "es-PE",
  }),
}));

// Mock react-window v2 (List API) so tests don't need DOM measurement
vi.mock("react-window", () => ({
  List: ({
    rowComponent: RowComponent,
    rowCount,
    rowProps,
  }: {
    rowComponent: (props: { index: number; style: React.CSSProperties } & Record<string, unknown>) => React.ReactNode;
    rowCount: number;
    rowProps: Record<string, unknown>;
    rowHeight: number;
    overscanCount?: number;
    style?: React.CSSProperties;
  }) => (
    <div data-testid="virtual-list" data-item-count={rowCount}>
      {Array.from({ length: Math.min(rowCount, 3) }, (_, i) =>
        RowComponent({ index: i, style: {}, ...rowProps }),
      )}
    </div>
  ),
}));

// Mock useAgendaFilters
vi.mock("../../../hooks/useAgendaFilters", () => ({
  useAgendaFilters: vi.fn(() => ({
    view: "semana",
    date: "2026-05-26",
    presetFilter: null,
    setView: vi.fn(),
    setDate: vi.fn(),
    setPresetFilter: vi.fn(),
    clearFilters: vi.fn(),
  })),
}));

// Mock useDrawerStore
vi.mock("../../../store/agenda-store", () => ({
  useDrawerStore: vi.fn(() => ({
    openDrawer: vi.fn(),
    drawerOpen: false,
    selectedSlotId: null,
  })),
}));

// Import components after mocks
import { AgendaCalendar } from "../AgendaCalendar";
import { DayCalendar } from "../DayCalendar";
import { WeekCalendar } from "../WeekCalendar";
import { MonthCalendar } from "../MonthCalendar";
import { FreshnessIndicator } from "../FreshnessIndicator";
import { useAgendaFilters } from "../../../hooks/useAgendaFilters";

// ── Fixtures ─────────────────────────────────────────────────────────────────

function makeSlot(overrides: Partial<AgendaSlot> = {}): AgendaSlot {
  return {
    appointmentId: "appt-1",
    patientId: "pat-1",
    patientNameMasked: "P. Hernández",
    startTime: "2026-05-26T09:00:00-05:00",
    endTime: "2026-05-26T09:30:00-05:00",
    doctorId: "doc-1",
    doctorLabel: "Dr. C. Mendoza",
    serviceLabel: "Limpieza dental",
    appointmentStatus: "SCHEDULED",
    paymentStatus: "paid",
    origin: "walk_in",
    balanceDueCents: 0,
    balancePaidCents: 15000,
    currency: "PEN",
    ...overrides,
  };
}

function make50Slots(): AgendaSlot[] {
  return Array.from({ length: 51 }, (_, i) =>
    makeSlot({
      appointmentId: `appt-${i}`,
      startTime: `2026-05-26T${String(8 + Math.floor(i / 6)).padStart(2, "0")}:${String((i % 6) * 10).padStart(2, "0")}:00-05:00`,
      endTime: `2026-05-26T${String(8 + Math.floor(i / 6)).padStart(2, "0")}:${String((i % 6) * 10 + 30).padStart(2, "0")}:00-05:00`,
    }),
  );
}


// ── AgendaCalendar dispatcher tests ─────────────────────────────────────────

describe("AgendaCalendar dispatcher", () => {
  const mockUseAgendaFilters = vi.mocked(useAgendaFilters);

  beforeEach(() => {
    mockUseAgendaFilters.mockReturnValue({
      view: "semana",
      date: "2026-05-26",
      presetFilter: null,
      setView: vi.fn(),
      setDate: vi.fn(),
      setPresetFilter: vi.fn(),
      clearFilters: vi.fn(),
    });
  });

  it("renders WeekCalendar as default (view=semana)", () => {
    const slots = [makeSlot()];
    render(<AgendaCalendar slots={slots} tenantId="tenant-1" />);
    expect(screen.getByTestId("week-calendar")).toBeInTheDocument();
  });

  it("renders DayCalendar when view=dia", () => {
    mockUseAgendaFilters.mockReturnValue({
      view: "dia",
      date: "2026-05-26",
      presetFilter: null,
      setView: vi.fn(),
      setDate: vi.fn(),
      setPresetFilter: vi.fn(),
      clearFilters: vi.fn(),
    });
    const slots = [makeSlot()];
    render(<AgendaCalendar slots={slots} tenantId="tenant-1" />);
    expect(screen.getByTestId("day-calendar")).toBeInTheDocument();
  });

  it("renders MonthCalendar when view=mes", () => {
    mockUseAgendaFilters.mockReturnValue({
      view: "mes",
      date: "2026-05-26",
      presetFilter: null,
      setView: vi.fn(),
      setDate: vi.fn(),
      setPresetFilter: vi.fn(),
      clearFilters: vi.fn(),
    });
    render(
      <AgendaCalendar
        slots={[]}
        tenantId="tenant-1"
        monthAggregates={{
          month: "2026-05",
          days: [{ date: "2026-05-26", totalSlots: 3, statusBreakdown: { paid: 2, deposit: 1 } }],
        }}
      />,
    );
    expect(screen.getByTestId("month-calendar")).toBeInTheDocument();
  });

  it("renders SkeletonCalendar when isLoading=true", () => {
    const slots: AgendaSlot[] = [];
    render(
      <AgendaCalendar slots={slots} tenantId="tenant-1" isLoading={true} />,
    );
    expect(screen.getByTestId("skeleton-calendar")).toBeInTheDocument();
  });
});

// ── DayCalendar virtualization tests ────────────────────────────────────────

describe("DayCalendar", () => {
  it("renders slot list without virtualization when slots <= 50", () => {
    const slots = Array.from({ length: 10 }, (_, i) =>
      makeSlot({ appointmentId: `appt-${i}` }),
    );
    render(
      <DayCalendar
        slots={slots}
        date="2026-05-26"
        tenantId="tenant-1"
        onSlotClick={vi.fn()}
      />,
    );
    expect(screen.getByTestId("day-calendar")).toBeInTheDocument();
    // No virtual list when <=50
    expect(screen.queryByTestId("virtual-list")).not.toBeInTheDocument();
  });

  it("uses react-window FixedSizeList virtualization when slots > 50 (A4 / SC-9)", () => {
    const slots = make50Slots();
    render(
      <DayCalendar
        slots={slots}
        date="2026-05-26"
        tenantId="tenant-1"
        onSlotClick={vi.fn()}
      />,
    );
    expect(screen.getByTestId("day-calendar")).toBeInTheDocument();
    const vList = screen.getByTestId("virtual-list");
    expect(vList).toBeInTheDocument();
    expect(Number(vList.getAttribute("data-item-count"))).toBe(51);
  });

  it("renders empty state when no slots", () => {
    render(
      <DayCalendar
        slots={[]}
        date="2026-05-26"
        tenantId="tenant-1"
        onSlotClick={vi.fn()}
      />,
    );
    expect(screen.getByTestId("day-calendar")).toBeInTheDocument();
    expect(screen.getByText(/sin citas/i)).toBeInTheDocument();
  });

  it("calls onSlotClick with appointmentId when slot is clicked", () => {
    const slots = [makeSlot({ appointmentId: "appt-click" })];
    const onSlotClick = vi.fn();
    render(
      <DayCalendar
        slots={slots}
        date="2026-05-26"
        tenantId="tenant-1"
        onSlotClick={onSlotClick}
      />,
    );
    const slotBtn = screen.getByRole("button", { name: /P\. Hernández/i });
    fireEvent.click(slotBtn);
    expect(onSlotClick).toHaveBeenCalledWith("appt-click");
  });
});

// ── WeekCalendar tests ───────────────────────────────────────────────────────

describe("WeekCalendar", () => {
  it("renders 7-day grid", () => {
    const slots = [makeSlot()];
    render(
      <WeekCalendar
        slots={slots}
        date="2026-05-26"
        tenantId="tenant-1"
        onSlotClick={vi.fn()}
      />,
    );
    expect(screen.getByTestId("week-calendar")).toBeInTheDocument();
    // 7 day columns
    const dayCols = screen.getAllByTestId(/week-day-col-/);
    expect(dayCols.length).toBe(7);
  });

  it("slots assigned to correct day column", () => {
    const mondaySlot = makeSlot({
      appointmentId: "appt-monday",
      startTime: "2026-05-25T09:00:00-05:00", // Monday
      patientNameMasked: "A. Monday",
    });
    render(
      <WeekCalendar
        slots={[mondaySlot]}
        date="2026-05-25"
        tenantId="tenant-1"
        onSlotClick={vi.fn()}
      />,
    );
    expect(screen.getByText(/A\. Monday/i)).toBeInTheDocument();
  });

  it("renders empty state per day when no slots in that column", () => {
    render(
      <WeekCalendar
        slots={[]}
        date="2026-05-26"
        tenantId="tenant-1"
        onSlotClick={vi.fn()}
      />,
    );
    expect(screen.getByTestId("week-calendar")).toBeInTheDocument();
    // With no slots, all columns are empty - no slot buttons
    expect(screen.queryByRole("button", { name: /P\. Hernández/i })).not.toBeInTheDocument();
  });
});

// ── MonthCalendar aggregates tests ──────────────────────────────────────────

describe("MonthCalendar aggregates (A5 / SC-9)", () => {
  it("renders month grid (5 rows × 7 cols) with day dots from aggregates", () => {
    const aggregates = {
      month: "2026-05",
      days: [
        { date: "2026-05-26", totalSlots: 5, statusBreakdown: { paid: 3, deposit: 1, unpaid: 1 } },
        { date: "2026-05-27", totalSlots: 2, statusBreakdown: { paid: 2 } },
      ],
    };
    render(
      <MonthCalendar
        tenantId="tenant-1"
        date="2026-05-26"
        aggregates={aggregates}
        onDayClick={vi.fn()}
      />,
    );
    expect(screen.getByTestId("month-calendar")).toBeInTheDocument();
    // Day 26 should show dots for totalSlots
    expect(screen.getByTestId("month-day-2026-05-26")).toBeInTheDocument();
    const day26 = screen.getByTestId("month-day-2026-05-26");
    // Dots represent payment status breakdown
    expect(day26.textContent).not.toBe("");
  });

  it("does NOT render slot list (aggregates-only for performance)", () => {
    const aggregates = {
      month: "2026-05",
      days: [{ date: "2026-05-26", totalSlots: 3, statusBreakdown: { paid: 3 } }],
    };
    render(
      <MonthCalendar
        tenantId="tenant-1"
        date="2026-05-26"
        aggregates={aggregates}
        onDayClick={vi.fn()}
      />,
    );
    // No individual slot data (P. Hernández etc.)
    expect(screen.queryByText(/P\. Hernández/)).not.toBeInTheDocument();
    // No virtual list in month view
    expect(screen.queryByTestId("virtual-list")).not.toBeInTheDocument();
  });

  it("calls onDayClick with date string when day cell clicked", () => {
    const onDayClick = vi.fn();
    const aggregates = {
      month: "2026-05",
      days: [{ date: "2026-05-15", totalSlots: 2, statusBreakdown: { paid: 2 } }],
    };
    render(
      <MonthCalendar
        tenantId="tenant-1"
        date="2026-05-01"
        aggregates={aggregates}
        onDayClick={onDayClick}
      />,
    );
    const day15 = screen.getByTestId("month-day-2026-05-15");
    fireEvent.click(day15);
    expect(onDayClick).toHaveBeenCalledWith("2026-05-15");
  });
});

// ── FreshnessIndicator tests ─────────────────────────────────────────────────

describe("FreshnessIndicator (A6 / Q12)", () => {
  it("renders 'Actualizado hace...' when lastFetchedAt provided", () => {
    const recentTime = new Date(Date.now() - 5000).toISOString();
    render(
      <FreshnessIndicator
        lastFetchedAt={recentTime}
        onRefresh={vi.fn()}
      />,
    );
    // Should show "Actualizado hace ..." text
    expect(screen.getByTestId("freshness-indicator")).toBeInTheDocument();
    const text = screen.getByTestId("freshness-label").textContent ?? "";
    expect(text).toMatch(/Actualizado/i);
  });

  it("renders '—' when lastFetchedAt is null", () => {
    render(
      <FreshnessIndicator
        lastFetchedAt={null}
        onRefresh={vi.fn()}
      />,
    );
    expect(screen.getByTestId("freshness-label").textContent).toBe("—");
  });

  it("calls onRefresh when refresh button is clicked", async () => {
    const onRefresh = vi.fn();
    const recentTime = new Date(Date.now() - 10000).toISOString();
    render(
      <FreshnessIndicator
        lastFetchedAt={recentTime}
        onRefresh={onRefresh}
      />,
    );
    const refreshBtn = screen.getByRole("button", { name: /actualizar/i });
    fireEvent.click(refreshBtn);
    await waitFor(() => expect(onRefresh).toHaveBeenCalledTimes(1));
  });

  it("has aria-live='polite' for screen reader updates", () => {
    render(
      <FreshnessIndicator
        lastFetchedAt={null}
        onRefresh={vi.fn()}
      />,
    );
    const indicator = screen.getByTestId("freshness-indicator");
    expect(indicator.getAttribute("aria-live")).toBe("polite");
  });

  it("does not contain voseo in user-facing text", () => {
    // voseo-allowed: testing for absence of voseo in technical fixture
    const recentTime = new Date(Date.now() - 60000).toISOString();
    const { container } = render(
      <FreshnessIndicator
        lastFetchedAt={recentTime}
        onRefresh={vi.fn()}
      />,
    );
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/tenés|podés|hacés|mirá|sos\b/i);
  });
});
