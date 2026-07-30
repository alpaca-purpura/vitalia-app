// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-6
/**
 * servicios-ui-store.ts — Zustand UI state store for the Servicios surface.
 *
 * UI-ONLY state (ADR-vitalia-004 § 4: Zustand = UI state ONLY; server data lives
 * in React Query via serviciosKeys). NO server entities here.
 *
 * State tracked:
 *   - draggingOfferId : escalera card currently being dragged (null = none).
 *   - openKebabId     : which catalog card kebab menu is open (null = none).
 *   - bibliotecaOpen  : whether the "elegir de la biblioteca" picker is open.
 *
 * T-6 vitalia-fase2-lisa-servicios
 * spec_anchor: ADR-vitalia-004 § 4
 * downstream-regression-na: brand-local vitalia FE store; no cross-brand consumers
 */

"use client";

import { create } from "zustand/react"; // index export* falla en turbopack (HB-78)

interface ServiciosUiState {
  /** offer_id of the escalera card being dragged (null = no active drag). */
  draggingOfferId: string | null;
  /** offer_id whose catalog kebab menu is open (null = all closed). */
  openKebabId: string | null;
  /** True when the biblioteca picker (empty-state invite) is open. */
  bibliotecaOpen: boolean;

  setDraggingOfferId: (offerId: string | null) => void;
  setOpenKebabId: (offerId: string | null) => void;
  setBibliotecaOpen: (open: boolean) => void;
  resetUiState: () => void;
}

const initialState = {
  draggingOfferId: null as string | null,
  openKebabId: null as string | null,
  bibliotecaOpen: false,
};

export const useServiciosUiStore = create<ServiciosUiState>((set) => ({
  ...initialState,
  setDraggingOfferId: (draggingOfferId) => set({ draggingOfferId }),
  setOpenKebabId: (openKebabId) => set({ openKebabId }),
  setBibliotecaOpen: (bibliotecaOpen) => set({ bibliotecaOpen }),
  resetUiState: () => set({ ...initialState }),
}));
