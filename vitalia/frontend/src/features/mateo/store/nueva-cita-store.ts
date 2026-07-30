// cap: scheduling.mateo-agenda
/**
 * nueva-cita-store.ts — Zustand UI state for the "Nueva cita" leaf sheet.
 * T-FE-1 vitalia-fase2-mateo-nueva-cita
 *
 * UI state ONLY (no server data — that lives in React Query).
 * Tracks:
 *   - selectedServiceId: UUID | null — chosen service (drives duration prefill)
 *   - selectedDoctorId:  UUID | null — chosen doctor
 *   - availabilityStatus: string | null — last check result
 *   - patientId: UUID | null — resolved patient (typeahead OR inline create)
 *   - isInlinePatientMode: boolean — true = show inline create form
 *
 * Session-only: NOT persisted to localStorage (appointment creation is
 * single-session, no resume needed). Using plain Zustand create().
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE store; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § F3 + 06-tickets.yaml T-FE-1
 */

"use client";

import { create } from "zustand";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface NuevaCitaStoreState {
  /** UUID of the selected service offer, or null (not yet selected). */
  selectedServiceId: string | null;
  /** UUID of the selected doctor, or null. */
  selectedDoctorId: string | null;
  /** Last availability check status ("available"|"busy"|"out_of_hours"|"no_schedule"|null). */
  availabilityStatus: string | null;
  /** Resolved patient UUID (from typeahead or inline create). */
  patientId: string | null;
  /** True = user clicked "nuevo paciente" (show inline create form). */
  isInlinePatientMode: boolean;
}

export interface NuevaCitaStoreActions {
  setSelectedServiceId: (id: string | null) => void;
  setSelectedDoctorId: (id: string | null) => void;
  setAvailabilityStatus: (status: string | null) => void;
  setPatientId: (id: string | null) => void;
  setIsInlinePatientMode: (mode: boolean) => void;
  /** Reset all fields (use on successful create or cancel). */
  reset: () => void;
}

type NuevaCitaStore = NuevaCitaStoreState & NuevaCitaStoreActions;

// ── Initial state ─────────────────────────────────────────────────────────────

const INITIAL_STATE: NuevaCitaStoreState = {
  selectedServiceId: null,
  selectedDoctorId: null,
  availabilityStatus: null,
  patientId: null,
  isInlinePatientMode: false,
};

// ── Store ─────────────────────────────────────────────────────────────────────

/**
 * useNuevaCitaStore — session-only UI state for the "Nueva cita" form page.
 *
 * Usage:
 * ```tsx
 * const selectedServiceId = useNuevaCitaStore((s) => s.selectedServiceId);
 * const setSelectedServiceId = useNuevaCitaStore((s) => s.setSelectedServiceId);
 * ```
 */
export const useNuevaCitaStore = create<NuevaCitaStore>()((set) => ({
  ...INITIAL_STATE,

  setSelectedServiceId: (id) => set({ selectedServiceId: id }),
  setSelectedDoctorId: (id) => set({ selectedDoctorId: id }),
  setAvailabilityStatus: (status) => set({ availabilityStatus: status }),
  setPatientId: (id) => set({ patientId: id }),
  setIsInlinePatientMode: (mode) => set({ isInlinePatientMode: mode }),

  reset: () => set(INITIAL_STATE),
}));
