// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * embudo-ui-store.ts — Zustand UI state for Adrián Embudo (T-FE-2).
 *
 * UI-ONLY state: no server/API data here (that lives in React Query).
 * Per ADR-vitalia-004 § 3.4: Zustand = UI state; React Query = server data.
 *
 * State shape:
 *   - view: 'kanban' | 'lista' — toggle (URL-synced via ?view=)
 *   - sort: sort key (URL-synced via ?sort=)
 *   - filters: ephemeral filters (origin/doctor/etc.)
 *   - activeDragId: which lead is being dragged (null when idle)
 *   - dropTargetStage: which column is hovered during drag
 *   - pendingOverride: { leadId, fromStage, toStage } — waiting for OverrideReasonDialog
 *   - highlightLeadId: ring+pulse after create/move (null when idle)
 *
 * PHI constraint: NEVER put PHI (patient names, email, phone) in this store. IDs only.
 *
 * downstream-regression-na: brand-local vitalia FE store
 * spec_anchor: 03-arch-fe.md § Data layer + § Zustand
 */
"use client";

import { create } from "zustand/react"; // index export* falla en turbopack (HB-78)
import type { LeadFunnelStage, BoardFilters } from "../types/embudo.types";

// ── Pending override (waiting for OverrideReasonDialog) ──────────────────────

export interface PendingOverride {
  leadId: string;
  fromStage: LeadFunnelStage;
  toStage: LeadFunnelStage;
  leadVersion: number;
}

// ── State shape ───────────────────────────────────────────────────────────────

interface EmbudoUiState {
  /** Current board view mode */
  view: "kanban" | "lista";
  /** Current sort key */
  sort: BoardFilters["sort"];
  /** Ephemeral filter state (origin/doctor/etc.) */
  filters: Omit<BoardFilters, "view" | "sort">;
  /** ID of lead currently being dragged */
  activeDragId: string | null;
  /** Stage column currently being hovered during drag */
  dropTargetStage: LeadFunnelStage | null;
  /** Override dialog state — non-null when dialog is open */
  pendingOverride: PendingOverride | null;
  /** Lead to highlight with ring+pulse after create/move */
  highlightLeadId: string | null;
}

interface EmbudoUiActions {
  setView: (view: "kanban" | "lista") => void;
  setSort: (sort: BoardFilters["sort"]) => void;
  setFilters: (filters: Omit<BoardFilters, "view" | "sort">) => void;
  setActiveDragId: (id: string | null) => void;
  setDropTargetStage: (stage: LeadFunnelStage | null) => void;
  setPendingOverride: (override: PendingOverride | null) => void;
  setHighlightLeadId: (id: string | null) => void;
  clearDragState: () => void;
}

// ── Store ─────────────────────────────────────────────────────────────────────

export const useEmbudoUiStore = create<EmbudoUiState & EmbudoUiActions>(
  (set) => ({
    // Initial state
    view: "kanban",
    sort: "stage_age_desc",
    filters: {},
    activeDragId: null,
    dropTargetStage: null,
    pendingOverride: null,
    highlightLeadId: null,

    // Actions
    setView: (view) => set({ view }),
    setSort: (sort) => set({ sort }),
    setFilters: (filters) => set({ filters }),
    setActiveDragId: (id) => set({ activeDragId: id }),
    setDropTargetStage: (stage) => set({ dropTargetStage: stage }),
    setPendingOverride: (override) => set({ pendingOverride: override }),
    setHighlightLeadId: (id) => set({ highlightLeadId: id }),
    clearDragState: () =>
      set({ activeDragId: null, dropTargetStage: null, pendingOverride: null }),
  }),
);
