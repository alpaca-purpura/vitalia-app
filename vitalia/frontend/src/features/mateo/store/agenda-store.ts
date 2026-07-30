// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
/**
 * agenda-store.ts — Zustand SSR-safe drawer state store for Valeria Agenda.
 * T-12 vitalia-fase2-valeria-agenda
 * Migrated to createSsrSafePersistedStore (vitalia-shell-state-persistence T-3).
 *
 * WHY MIGRATED: The raw persist() middleware auto-writes the default drawerWidth during
 * SSR/skeleton/pre-hydration, potentially clobbering user resize preferences on reload.
 * The factory wraps persist with skipHydration:true + setItem NO-OP until client rehydrate.
 * ADR-vitalia-006 documents the pattern (defense-in-depth transversal convention).
 *
 * Persists drawerWidth to localStorage key "vitalia.agenda.drawerWidth" (Q5).
 * drawerWidth constrained to [440, 640] px — per 03-arch.md § 6.5.
 * All other state (selectedSlotId, drawerOpen, staleDetected) is session-only.
 *
 * partialize strategy:
 * - drawerWidth → persisted (user's resize preference)
 * - selectedSlotId, drawerOpen, staleDetected → NOT persisted (session-only)
 * - _hasHydrated → NOT persisted (transient hydration flag)
 * - setHasHydrated → NOT persisted (recreated on hydration)
 * - action setters → NOT persisted (recreated on hydration)
 *
 * REHYDRATION: call useStoreHydration(useDrawerStore) from the first client-side
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

// ── Constants ─────────────────────────────────────────────────────────────────

export const DRAWER_WIDTH_MIN = 440;
export const DRAWER_WIDTH_MAX = 640;
export const DRAWER_WIDTH_DEFAULT = 520;

const DRAWER_WIDTH_STORAGE_KEY = "vitalia.agenda.drawerWidth";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface DrawerState {
  /** ID of the currently selected appointment slot. Null = no selection. */
  selectedSlotId: string | null;
  /** Whether the drawer panel is open. */
  drawerOpen: boolean;
  /** Drawer width in pixels. Clamped to [440, 640]. Persisted. */
  drawerWidth: number;
  /**
   * True when polling detects that the currently open appointment was updated
   * remotely (updated_at newer than local cached version).
   * Triggers the stale banner in AppointmentDrawer.
   */
  staleDetected: boolean;
}

export interface DrawerActions {
  /** Open drawer for a specific slot. */
  openDrawer: (slotId: string) => void;
  /** Close the drawer and clear selection. */
  closeDrawer: () => void;
  /** Toggle drawer open/closed for current selection. */
  toggleDrawer: () => void;
  /** Set drawer width (clamped to [440, 640]). */
  setDrawerWidth: (width: number) => void;
  /** Mark current appointment as stale (remote update detected via polling). */
  setStaleDetected: (stale: boolean) => void;
}

export type DrawerStore = DrawerState & DrawerActions;

/** Full store state — extends SsrSafeHydration for factory compliance */
type DrawerStoreWithHydration = DrawerStore & SsrSafeHydration;

// ── Persisted slice (only drawerWidth) ────────────────────────────────────────

type PersistedState = {
  drawerWidth: number;
};

// ── Store ─────────────────────────────────────────────────────────────────────

/**
 * Drawer store — controls appointment detail panel state.
 *
 * Only drawerWidth is persisted (user resize preference).
 * selectedSlotId and drawerOpen are session-only (reset on page reload).
 *
 * Uses createSsrSafePersistedStore for SSR-safe hydration:
 * - setItem NO-OP while _hasHydrated === false (prevents default clobber)
 * - onRehydrateStorage flips _hasHydrated = true post-rehydrate
 * - useStoreHydration(useDrawerStore) triggers rehydrate() once client-side
 */
export const useDrawerStore = createSsrSafePersistedStore<DrawerStoreWithHydration>(
  (set) => ({
    // ── SsrSafeHydration ────────────────────────────────────────────────────
    _hasHydrated: false,
    setHasHydrated: (v: boolean) => set({ _hasHydrated: v }),

    // ── State ─────────────────────────────────────────────────────────────
    selectedSlotId: null,
    drawerOpen: false,
    drawerWidth: DRAWER_WIDTH_DEFAULT,
    staleDetected: false,

    // ── Actions ───────────────────────────────────────────────────────────

    openDrawer: (slotId: string) =>
      set({ selectedSlotId: slotId, drawerOpen: true, staleDetected: false }),

    closeDrawer: () =>
      set({ drawerOpen: false, selectedSlotId: null, staleDetected: false }),

    toggleDrawer: () =>
      set((state) => ({ drawerOpen: !state.drawerOpen })),

    setDrawerWidth: (width: number) =>
      set({
        drawerWidth: Math.min(
          DRAWER_WIDTH_MAX,
          Math.max(DRAWER_WIDTH_MIN, Math.round(width)),
        ),
      }),

    setStaleDetected: (stale: boolean) =>
      set({ staleDetected: stale }),
  }),
  {
    name: DRAWER_WIDTH_STORAGE_KEY,
    // Only persist drawerWidth — all other state is session-only
    // _hasHydrated and setters are intentionally excluded from persist
    partialize: (state): PersistedState => ({
      drawerWidth: state.drawerWidth,
    }),
  },
);
