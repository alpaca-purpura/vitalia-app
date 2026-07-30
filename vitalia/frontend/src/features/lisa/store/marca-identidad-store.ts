// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
"use client";

/**
 * marca-identidad-store.ts — Zustand UI state store for Identidad sub-sub-tab.
 *
 * Manages client-only UI state (per ADR-vitalia-004 § 4: Zustand = UI state ONLY).
 * Server data lives in React Query (useQuery/useMutation via marcaKeys).
 *
 * State tracked:
 *   - dropzoneActive: whether the logo dropzone shows drag-over highlight
 *   - colorPickerOpen: which color swatch popover is open (null = none)
 *   - logoUploading: in-progress logo upload (separate from React Query to avoid flicker)
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 deliverables + ADR-vitalia-004 § 4
 * downstream-regression-na: brand-local vitalia FE store; no cross-brand consumers
 */


import { create } from "zustand/react"; // index export* falla en turbopack (HB-78)

export type ColorPickerSlot = "primary" | "accent" | "background" | null;

interface MarcaIdentidadState {
  /** True when user is dragging a file over the logo dropzone. */
  dropzoneActive: boolean;
  /** Which color swatch popover is currently open (null = all closed). */
  colorPickerOpen: ColorPickerSlot;
  /** True when a logo is being uploaded to S3. */
  logoUploading: boolean;

  // ── Actions ──────────────────────────────────────────────────────────────────
  setDropzoneActive: (active: boolean) => void;
  setColorPickerOpen: (slot: ColorPickerSlot) => void;
  setLogoUploading: (uploading: boolean) => void;
  /** Reset all UI state (e.g., on route change or unmount). */
  resetUiState: () => void;
}

const initialState = {
  dropzoneActive: false,
  colorPickerOpen: null as ColorPickerSlot,
  logoUploading: false,
};

export const useMarcaIdentidadStore = create<MarcaIdentidadState>((set) => ({
  ...initialState,

  setDropzoneActive: (active) => set({ dropzoneActive: active }),
  setColorPickerOpen: (slot) => set({ colorPickerOpen: slot }),
  setLogoUploading: (uploading) => set({ logoUploading: uploading }),
  resetUiState: () => set(initialState),
}));
