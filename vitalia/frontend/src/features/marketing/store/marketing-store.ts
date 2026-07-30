// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * marketingStore — Zustand store for ephemeral UI state (not URL-serializable)
 * URL state (tabs, period, selected rec, modals) lives in nuqs (url-state.ts)
 * This store handles: animation state + pending undo countdowns
 * downstream-regression-na: brand-local FE store; no cross-brand consumers
 */
"use client";

import { create } from "zustand/react"; // index export* falla en turbopack (HB-78)

type MarketingStoreState = {
  /** Whether the bowtie funnel SVG animation is running */
  bowtieAnimating: boolean;
  setBowtieAnimating: (animating: boolean) => void;

  /** Map of rec_id → unix timestamp (ms) when undo expires */
  pendingUndoTimers: Map<string, number>;
  setPendingUndoTimer: (recId: string, expiryMs: number) => void;
  clearPendingUndoTimer: (recId: string) => void;
};

export const useMarketingStore = create<MarketingStoreState>((set) => ({
  bowtieAnimating: false,
  setBowtieAnimating: (animating) => set({ bowtieAnimating: animating }),

  pendingUndoTimers: new Map(),
  setPendingUndoTimer: (recId, expiryMs) =>
    set((state) => {
      const updated = new Map(state.pendingUndoTimers);
      updated.set(recId, expiryMs);
      return { pendingUndoTimers: updated };
    }),
  clearPendingUndoTimer: (recId) =>
    set((state) => {
      const updated = new Map(state.pendingUndoTimers);
      updated.delete(recId);
      return { pendingUndoTimers: updated };
    }),
}));
