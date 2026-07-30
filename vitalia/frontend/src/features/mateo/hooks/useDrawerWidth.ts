// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * useDrawerWidth.ts — Drawer resize hook for Valeria Agenda appointment drawer.
 * T-12 vitalia-fase2-valeria-agenda
 *
 * Wraps useDrawerStore to provide:
 * - Current drawerWidth (persisted in localStorage)
 * - setDrawerWidth with clamp [440, 640]
 * - CSS variable style object for drawer container
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.5 + 06-tickets.yaml T-12
 */

import { useCallback } from "react";
import {
  useDrawerStore,
  DRAWER_WIDTH_MIN,
  DRAWER_WIDTH_MAX,
} from "../store/agenda-store";

// ── Hook ──────────────────────────────────────────────────────────────────────

export interface UseDrawerWidthReturn {
  /** Current drawer width in pixels (clamped to [440, 640]). */
  drawerWidth: number;
  /** Set drawer width — clamps automatically. */
  setDrawerWidth: (width: number) => void;
  /** CSS inline style object for the drawer container. */
  drawerStyle: { width: string; minWidth: string; maxWidth: string };
}

/**
 * Provides drawer width state with CSS style object.
 *
 * Persisted to localStorage key "vitalia.agenda.drawerWidth".
 *
 * @example
 * const { drawerWidth, drawerStyle, setDrawerWidth } = useDrawerWidth();
 * return <div style={drawerStyle} onMouseUp={handleResizeEnd}>...</div>
 */
export function useDrawerWidth(): UseDrawerWidthReturn {
  const { drawerWidth, setDrawerWidth: storeSetWidth } = useDrawerStore();

  const setDrawerWidth = useCallback(
    (width: number) => {
      storeSetWidth(width);
    },
    [storeSetWidth],
  );

  const drawerStyle = {
    width: `${drawerWidth}px`,
    minWidth: `${DRAWER_WIDTH_MIN}px`,
    maxWidth: `${DRAWER_WIDTH_MAX}px`,
  };

  return { drawerWidth, setDrawerWidth, drawerStyle };
}
