// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
/**
 * agenda-filters-store.ts — Zustand SSR-safe filter + view preference store for Valeria Agenda.
 * T-12 vitalia-fase2-valeria-agenda
 * Migrated to createSsrSafePersistedStore (vitalia-shell-state-persistence T-3).
 *
 * WHY MIGRATED: The raw persist() middleware auto-writes the default lastView during
 * SSR/skeleton/pre-hydration, potentially clobbering user view preferences on reload.
 * The factory wraps persist with skipHydration:true + setItem NO-OP until client rehydrate.
 * ADR-vitalia-006 documents the pattern (defense-in-depth transversal convention).
 *
 * Persists lastView to localStorage key "vitalia.agenda.lastView" (Q3).
 * activePreset is session-only (URL is SSoT, store is derived state for fast access).
 *
 * partialize strategy:
 * - lastView → persisted (user's view preference)
 * - activePreset → NOT persisted (session state — URL is SSoT)
 * - _hasHydrated → NOT persisted (transient hydration flag)
 * - setHasHydrated → NOT persisted (recreated on hydration)
 * - action setters → NOT persisted (recreated on hydration)
 *
 * REHYDRATION: call useStoreHydration(useFiltersStore) from the first client-side
 * component that consumes this store (within an ssr:false dynamic chunk).
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE store; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.5 + 06-tickets.yaml T-12
 */

import {
  createSsrSafePersistedStore,
  type SsrSafeHydration,
} from "@luana/hooks/create-ssr-safe-persisted-store";
import type { AgendaFilter, AgendaView } from "../types/agenda.types";

// ── Constants ─────────────────────────────────────────────────────────────────

const LAST_VIEW_STORAGE_KEY = "vitalia.agenda.lastView";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FiltersState {
  /** Active preset filter chip. Null = no filter active. Session-only. */
  activePreset: AgendaFilter | null;
  /**
   * Last view used by this user. Persisted in localStorage.
   * Used to restore preferred view on page revisit when no URL param present.
   */
  lastView: AgendaView;
}

export interface FiltersActions {
  /** Set active preset filter. Pass null to clear. */
  setActivePreset: (preset: AgendaFilter | null) => void;
  /** Update last view (called when user changes view mode). */
  setLastView: (view: AgendaView) => void;
  /** Clear all filters (preserves lastView). */
  clearFilters: () => void;
}

export type FiltersStore = FiltersState & FiltersActions;

/** Full store state — extends SsrSafeHydration for factory compliance */
type FiltersStoreWithHydration = FiltersStore & SsrSafeHydration;

// ── Persisted slice (only lastView) ───────────────────────────────────────────

type PersistedState = {
  lastView: AgendaView;
};

// ── Store ─────────────────────────────────────────────────────────────────────

/**
 * Filters store — manages preset chip state + view preference.
 *
 * URL is the SSoT for view + date (useAgendaFilters syncs URL ↔ store).
 * This store provides fast in-memory access and persistence for lastView.
 *
 * Uses createSsrSafePersistedStore for SSR-safe hydration:
 * - setItem NO-OP while _hasHydrated === false (prevents default clobber)
 * - onRehydrateStorage flips _hasHydrated = true post-rehydrate
 * - useStoreHydration(useFiltersStore) triggers rehydrate() once client-side
 */
export const useFiltersStore = createSsrSafePersistedStore<FiltersStoreWithHydration>(
  (set) => ({
    // ── SsrSafeHydration ────────────────────────────────────────────────────
    _hasHydrated: false,
    setHasHydrated: (v: boolean) => set({ _hasHydrated: v }),

    // ── State ─────────────────────────────────────────────────────────────
    activePreset: null,
    lastView: "semana",

    // ── Actions ───────────────────────────────────────────────────────────

    setActivePreset: (preset) => set({ activePreset: preset }),

    setLastView: (view) => set({ lastView: view }),

    clearFilters: () => set({ activePreset: null }),
  }),
  {
    name: LAST_VIEW_STORAGE_KEY,
    // Only persist lastView — activePreset is session state (URL is SSoT)
    // _hasHydrated and setters are intentionally excluded from persist
    partialize: (state): PersistedState => ({
      lastView: state.lastView,
    }),
  },
);
