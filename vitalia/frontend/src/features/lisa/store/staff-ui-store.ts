// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * staff-ui-store.ts — Zustand UI state for Lisa Staff sub-tab.
 *
 * Manages client-only UI state (per ADR-vitalia-004 § 4: Zustand = UI state ONLY).
 * Server data lives in React Query (staffKeys.list, staffKeys.detail, etc.).
 *
 * State tracked:
 *   - nuevoIntegranteOpen: whether NuevoIntegrante modal is open
 *   - calendarWeek: ISO date string of start of currently viewed week
 *   - dragDraft: in-progress drag-to-create availability block
 *
 * T-FE-1 vitalia-fase2-lisa-doctores
 * spec_anchor: 03-arch-fe.md § Data layer + ADR-vitalia-004 § 4
 * downstream-regression-na: brand-local vitalia FE store; no cross-brand consumers
 */

"use client";

import { create } from "zustand/react"; // index export* falla en turbopack (HB-78)
import { mondayOfWeek } from "@/lib/format/calendarDates";

/** Drag draft for availability calendar (T-FE-3) */
export interface CalendarDragDraft {
  dayOfWeek: number;
  startHour: number;
  endHour: number;
}

interface StaffUiState {
  /** NuevoIntegranteModal open state */
  nuevoIntegranteOpen: boolean;
  /** ISO date string of the Monday of the currently viewed week */
  calendarWeek: string;
  /** In-progress drag-to-create block (null when not dragging) */
  dragDraft: CalendarDragDraft | null;

  // ── Actions ──────────────────────────────────────────────────────────────────
  openNuevoIntegrante: () => void;
  closeNuevoIntegrante: () => void;
  setCalendarWeek: (isoDate: string) => void;
  setDragDraft: (draft: CalendarDragDraft | null) => void;
  resetUiState: () => void;
}

/**
 * Get ISO string for the Monday of the current week.
 *
 * bug7 r4: was `monday.toISOString().split("T")[0]` AFTER a local setDate →
 * under a negative UTC offset (America/Lima −05) in the evening the UTC date is
 * the NEXT day → returned a TUESDAY → the whole week grid shifted one column →
 * a Monday block painted in the Sunday column. mondayOfWeek() builds the date
 * from LOCAL components only (TZ-stable). SSoT: lib/format/calendarDates.
 */
function getCurrentWeekMonday(): string {
  return mondayOfWeek(new Date());
}

const initialState = {
  nuevoIntegranteOpen: false,
  calendarWeek: getCurrentWeekMonday(),
  dragDraft: null as CalendarDragDraft | null,
};

export const useStaffUiStore = create<StaffUiState>((set) => ({
  ...initialState,

  openNuevoIntegrante: () => set({ nuevoIntegranteOpen: true }),
  closeNuevoIntegrante: () => set({ nuevoIntegranteOpen: false }),
  setCalendarWeek: (isoDate) => set({ calendarWeek: isoDate }),
  setDragDraft: (draft) => set({ dragDraft: draft }),
  resetUiState: () => set(initialState),
}));
