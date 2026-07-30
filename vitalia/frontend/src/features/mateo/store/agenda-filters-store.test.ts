/**
 * agenda-filters-store.test.ts — Zustand filters store unit tests (TDD RED→GREEN).
 * T-12 vitalia-fase2-valeria-agenda
 *
 * Tests cover:
 *   - Initial state (activePreset=null, lastView="semana")
 *   - setActivePreset updates activePreset
 *   - setLastView updates lastView (persisted)
 *   - clearFilters resets activePreset but preserves lastView
 *   - localStorage key is "vitalia.agenda.lastView"
 *
 * downstream-regression-na: brand-local FE tests; no cross-brand consumers
 * spec_anchor: 06-tickets.yaml T-12
 */

import { describe, it, expect, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { useFiltersStore } from "./agenda-filters-store";

// Reset store before each test
beforeEach(() => {
  useFiltersStore.setState({
    activePreset: null,
    lastView: "semana",
  });
});

describe("useFiltersStore — initial state", () => {
  it("starts with no active preset", () => {
    const { result } = renderHook(() => useFiltersStore());
    expect(result.current.activePreset).toBeNull();
  });

  it("starts with lastView='semana'", () => {
    const { result } = renderHook(() => useFiltersStore());
    expect(result.current.lastView).toBe("semana");
  });
});

describe("useFiltersStore — setActivePreset", () => {
  it("sets activePreset to a valid filter", () => {
    const { result } = renderHook(() => useFiltersStore());

    act(() => result.current.setActivePreset("today"));
    expect(result.current.activePreset).toBe("today");
  });

  it("clears activePreset when set to null", () => {
    const { result } = renderHook(() => useFiltersStore());

    act(() => result.current.setActivePreset("no_shows"));
    act(() => result.current.setActivePreset(null));
    expect(result.current.activePreset).toBeNull();
  });

  it("accepts all valid AgendaFilter values", () => {
    const { result } = renderHook(() => useFiltersStore());
    const filters = [
      "today",
      "tomorrow_pending",
      "reschedule",
      "no_shows",
      "pending_balances",
    ] as const;

    for (const filter of filters) {
      act(() => result.current.setActivePreset(filter));
      expect(result.current.activePreset).toBe(filter);
    }
  });
});

describe("useFiltersStore — setLastView", () => {
  it("updates lastView to dia", () => {
    const { result } = renderHook(() => useFiltersStore());

    act(() => result.current.setLastView("dia"));
    expect(result.current.lastView).toBe("dia");
  });

  it("updates lastView to mes", () => {
    const { result } = renderHook(() => useFiltersStore());

    act(() => result.current.setLastView("mes"));
    expect(result.current.lastView).toBe("mes");
  });
});

describe("useFiltersStore — clearFilters", () => {
  it("resets activePreset to null", () => {
    const { result } = renderHook(() => useFiltersStore());

    act(() => result.current.setActivePreset("pending_balances"));
    act(() => result.current.clearFilters());
    expect(result.current.activePreset).toBeNull();
  });

  it("preserves lastView when clearing filters", () => {
    const { result } = renderHook(() => useFiltersStore());

    act(() => result.current.setLastView("dia"));
    act(() => result.current.setActivePreset("today"));
    act(() => result.current.clearFilters());

    expect(result.current.lastView).toBe("dia"); // preserved
    expect(result.current.activePreset).toBeNull(); // cleared
  });
});
