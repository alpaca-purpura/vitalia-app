/**
 * AgendaPresetFilters.test.tsx — Vitest unit tests (TDD RED→GREEN).
 *
 * T-16 vitalia-fase2-valeria-agenda
 * spec_anchor: 06-tickets.yaml T-16 acceptance A1
 *
 * Tests:
 *   - Renders 5 filter chips (A1)
 *   - No chip is active on initial render with no presetFilter (A1)
 *   - Clicking a chip calls setPresetFilter with the correct filter value (A1)
 *   - Active chip has aria-checked="true" (A1 + SC-1 ARIA)
 *   - Inactive chips have aria-checked="false" (A1 + SC-1 ARIA)
 *   - Clicking the active chip calls setPresetFilter(null) to toggle off (A1)
 *   - Each chip has correct role="switch" (spec SC-1)
 *   - All 5 chips visible with correct labels (Spanish neutro)
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AgendaPresetFilters } from "../AgendaPresetFilters";
import type { AgendaFilter } from "../../../types/agenda.types";

// ── Mocks ─────────────────────────────────────────────────────────────────────

const mockSetPresetFilter = vi.fn();
const mockUseAgendaFilters = vi.fn();

vi.mock("../../../hooks/useAgendaFilters", () => ({
  useAgendaFilters: () => mockUseAgendaFilters(),
}));

// Mock next/navigation (used inside useAgendaFilters indirectly)
vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({ replace: vi.fn() })),
  usePathname: vi.fn(() => "/test/mateo/agenda"),
  useSearchParams: vi.fn(() => new URLSearchParams()),
}));

// ── Helpers ───────────────────────────────────────────────────────────────────

function renderFilters(presetFilter: AgendaFilter | null = null) {
  mockUseAgendaFilters.mockReturnValue({
    view: "semana",
    date: "2026-05-26",
    presetFilter,
    setView: vi.fn(),
    setDate: vi.fn(),
    setPresetFilter: mockSetPresetFilter,
    clearFilters: vi.fn(),
  });

  return render(<AgendaPresetFilters />);
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("AgendaPresetFilters — chip rendering (A1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders 5 filter chips", () => {
    renderFilters();
    const chips = screen.getAllByRole("switch");
    expect(chips).toHaveLength(5);
  });

  it("renders Hoy chip with correct label", () => {
    renderFilters();
    expect(screen.getByText("Hoy")).toBeDefined();
  });

  it("renders 'Por confirmar mañana' chip", () => {
    renderFilters();
    expect(screen.getByText("Por confirmar mañana")).toBeDefined();
  });

  it("renders 'Re-agendar pendientes' chip", () => {
    renderFilters();
    expect(screen.getByText("Re-agendar pendientes")).toBeDefined();
  });

  it("renders 'No-shows del día' chip", () => {
    renderFilters();
    expect(screen.getByText("No-shows del día")).toBeDefined();
  });

  it("renders 'Saldos pendientes' chip", () => {
    renderFilters();
    expect(screen.getByText("Saldos pendientes")).toBeDefined();
  });

  it("renders a group with aria-label 'Filtros rápidos de agenda'", () => {
    renderFilters();
    expect(
      screen.getByRole("group", { name: "Filtros rápidos de agenda" }),
    ).toBeDefined();
  });
});

describe("AgendaPresetFilters — ARIA state (A1 + SC-1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("all chips have aria-checked=false when no filter active", () => {
    renderFilters(null);
    const chips = screen.getAllByRole("switch");
    chips.forEach((chip) => {
      expect(chip.getAttribute("aria-checked")).toBe("false");
    });
  });

  it("active chip has aria-checked=true", () => {
    renderFilters("today");
    const todayChip = screen.getByTestId("preset-chip-today");
    expect(todayChip.getAttribute("aria-checked")).toBe("true");
  });

  it("inactive chips have aria-checked=false when one is active", () => {
    renderFilters("today");
    const otherChips = [
      screen.getByTestId("preset-chip-tomorrow_pending"),
      screen.getByTestId("preset-chip-reschedule"),
      screen.getByTestId("preset-chip-no_shows"),
      screen.getByTestId("preset-chip-pending_balances"),
    ];
    otherChips.forEach((chip) => {
      expect(chip.getAttribute("aria-checked")).toBe("false");
    });
  });
});

describe("AgendaPresetFilters — interactions (A1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("clicking an inactive chip calls setPresetFilter with its filter value", () => {
    renderFilters(null);
    const todayChip = screen.getByTestId("preset-chip-today");
    fireEvent.click(todayChip);
    expect(mockSetPresetFilter).toHaveBeenCalledWith("today");
  });

  it("clicking 'no_shows' chip calls setPresetFilter('no_shows')", () => {
    renderFilters(null);
    const chip = screen.getByTestId("preset-chip-no_shows");
    fireEvent.click(chip);
    expect(mockSetPresetFilter).toHaveBeenCalledWith("no_shows");
  });

  it("clicking 'pending_balances' chip calls setPresetFilter('pending_balances')", () => {
    renderFilters(null);
    const chip = screen.getByTestId("preset-chip-pending_balances");
    fireEvent.click(chip);
    expect(mockSetPresetFilter).toHaveBeenCalledWith("pending_balances");
  });

  it("clicking the currently active chip calls setPresetFilter(null) — toggle off", () => {
    // When today is active, clicking it again should clear it
    renderFilters("today");
    const todayChip = screen.getByTestId("preset-chip-today");
    fireEvent.click(todayChip);
    expect(mockSetPresetFilter).toHaveBeenCalledWith(null);
  });

  it("clicking different chip while one is active calls setPresetFilter with new value", () => {
    renderFilters("today");
    const rescheduleChip = screen.getByTestId("preset-chip-reschedule");
    fireEvent.click(rescheduleChip);
    expect(mockSetPresetFilter).toHaveBeenCalledWith("reschedule");
  });
});

describe("AgendaPresetFilters — accessibility (SC-1)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("each chip has role=switch", () => {
    renderFilters();
    const chips = screen.getAllByRole("switch");
    expect(chips).toHaveLength(5);
  });

  it("container has data-testid=agenda-preset-filters", () => {
    renderFilters();
    expect(screen.getByTestId("agenda-preset-filters")).toBeDefined();
  });

  it("today chip has aria-label describing its filter action", () => {
    renderFilters();
    const todayChip = screen.getByTestId("preset-chip-today");
    expect(todayChip.getAttribute("aria-label")).toBe("Filtrar citas de hoy");
  });
});
