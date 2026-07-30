// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * useAgendaFilters.ts — Merges URL search params with Zustand filters store.
 * T-12 vitalia-fase2-valeria-agenda
 *
 * URL is SSoT for view + date + preset_filter.
 * Zustand store provides fast access + lastView persistence.
 *
 * On mount: syncs URL → store.
 * On change: updates URL → React Query invalidation triggers re-fetch.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.5 + 06-tickets.yaml T-12
 */

import { useCallback } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useFiltersStore } from "../store/agenda-filters-store";
import type { AgendaFilter, AgendaView } from "../types/agenda.types";

// ── Type guards ────────────────────────────────────────────────────────────────

const VALID_VIEWS: AgendaView[] = ["dia", "semana", "mes"];
const VALID_FILTERS: AgendaFilter[] = [
  "today",
  "tomorrow_pending",
  "reschedule",
  "no_shows",
  "pending_balances",
];

function isAgendaView(value: string): value is AgendaView {
  return (VALID_VIEWS as string[]).includes(value);
}

function isAgendaFilter(value: string): value is AgendaFilter {
  return (VALID_FILTERS as string[]).includes(value);
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export interface AgendaFiltersState {
  view: AgendaView;
  date: string;
  presetFilter: AgendaFilter | null;
}

export interface AgendaFiltersActions {
  setView: (view: AgendaView) => void;
  setDate: (date: string) => void;
  setPresetFilter: (preset: AgendaFilter | null) => void;
  clearFilters: () => void;
}

export type UseAgendaFiltersReturn = AgendaFiltersState & AgendaFiltersActions;

/**
 * Merges URL search params with Zustand store for agenda filtering.
 *
 * URL params take precedence (SSoT).
 * Zustand lastView fallback when no URL view param present.
 *
 * @example
 * const { view, date, presetFilter, setView, setDate } = useAgendaFilters();
 */
export function useAgendaFilters(): UseAgendaFiltersReturn {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const { lastView, setLastView, activePreset, setActivePreset } =
    useFiltersStore();

  // Resolve current values from URL (SSoT) with fallbacks
  const rawView = searchParams.get("view") ?? "";
  const view: AgendaView = isAgendaView(rawView) ? rawView : lastView;
  const date: string =
    searchParams.get("date") ?? new Date().toISOString().slice(0, 10);
  const rawPreset = searchParams.get("preset_filter") ?? "";
  const presetFilter: AgendaFilter | null = isAgendaFilter(rawPreset)
    ? rawPreset
    : null;

  // Sync store with URL-derived preset (URL is SSoT)
  if (presetFilter !== activePreset) {
    setActivePreset(presetFilter);
  }

  // ── Actions ──────────────────────────────────────────────────────────────────

  const updateParams = useCallback(
    (updates: Partial<Record<"view" | "date" | "preset_filter", string | null>>) => {
      const current = new URLSearchParams(searchParams.toString());

      for (const [key, value] of Object.entries(updates)) {
        if (value === null || value === undefined) {
          current.delete(key);
        } else {
          current.set(key, value);
        }
      }

      // Use router.replace to avoid polluting browser history on every filter change
      router.replace(`${pathname}?${current.toString()}`, { scroll: false });
    },
    [router, pathname, searchParams],
  );

  const setView = useCallback(
    (newView: AgendaView) => {
      setLastView(newView);
      updateParams({ view: newView });
    },
    [updateParams, setLastView],
  );

  const setDate = useCallback(
    (newDate: string) => {
      updateParams({ date: newDate });
    },
    [updateParams],
  );

  const setPresetFilter = useCallback(
    (preset: AgendaFilter | null) => {
      setActivePreset(preset);
      updateParams({ preset_filter: preset });
    },
    [updateParams, setActivePreset],
  );

  const clearFilters = useCallback(() => {
    setActivePreset(null);
    updateParams({ preset_filter: null });
  }, [updateParams, setActivePreset]);

  return {
    view,
    date,
    presetFilter,
    setView,
    setDate,
    setPresetFilter,
    clearFilters,
  };
}
