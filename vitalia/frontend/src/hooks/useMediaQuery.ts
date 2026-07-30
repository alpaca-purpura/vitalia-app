// cap: platform.design-tokens-foundation
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * useMediaQuery — reactive media query hook.
 *
 * Returns true when the CSS media query matches. Initializes to false
 * (SSR-safe) and updates on mount + subsequent viewport changes.
 *
 * Usage:
 *   const isMobile = useMediaQuery("(max-width: 767px)");
 *
 * Named export only — NO default export (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useState, useEffect } from "react";

/**
 * useMediaQuery — returns true when the CSS media query string matches.
 *
 * Initializes to `false` (SSR-safe). Subscribes to `MediaQueryList` change
 * events for efficient viewport reactivity (no polling).
 *
 * @param query - CSS media query string, e.g. "(max-width: 767px)"
 * @returns boolean — true when the query matches
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    // Guard: not available in SSR / test environments without jsdom
    if (typeof window === "undefined") return;

    const mql = window.matchMedia(query);
    // Set initial value immediately on mount
    setMatches(mql.matches);

    const handler = (e: MediaQueryListEvent) => {
      setMatches(e.matches);
    };

    mql.addEventListener("change", handler);
    return () => {
      mql.removeEventListener("change", handler);
    };
  }, [query]);

  return matches;
}
