// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * useFreshness.ts — Tracks last fetch time and formats "Actualizado hace X" string.
 * T-12 vitalia-fase2-valeria-agenda
 *
 * Updates every 30 seconds (matches grid polling interval) to keep relative time accurate.
 * Uses formatRelativeTime from lib/freshness.ts (Spanish neutro LatAm).
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 * spec_anchor: 01-spec.md § real-time + 06-tickets.yaml T-12
 */

import { useState, useEffect, useCallback } from "react";
import { formatRelativeTime } from "../lib/freshness";

// ── Hook ──────────────────────────────────────────────────────────────────────

export interface UseFreshnessReturn {
  /** Formatted string: "Actualizado hace 3 minutos" | "Actualizado hace unos segundos" | "—" */
  freshnessLabel: string;
  /** ISO 8601 timestamp of last successful fetch (from BE serverTime or local Date). */
  lastFetchedAt: string | null;
  /** Call this with BE serverTime on each successful data fetch. */
  updateFreshness: (serverTime: string) => void;
}

/**
 * Tracks last data fetch time and formats a live "Actualizado hace X" label.
 *
 * Updates every 30 seconds to keep the relative time string fresh.
 * Consumes serverTime from AgendaGridResponse (not local clock).
 *
 * @example
 * const { freshnessLabel, updateFreshness } = useFreshness();
 * // On data success:
 * useEffect(() => { if (data?.serverTime) updateFreshness(data.serverTime); }, [data]);
 * // Render:
 * <span aria-live="polite">{freshnessLabel}</span>
 */
export function useFreshness(): UseFreshnessReturn {
  const [lastFetchedAt, setLastFetchedAt] = useState<string | null>(null);
  const [freshnessLabel, setFreshnessLabel] = useState<string>("—");

  const updateFreshness = useCallback((serverTime: string) => {
    setLastFetchedAt(serverTime);
    setFreshnessLabel(formatRelativeTime(serverTime));
  }, []);

  // Refresh the relative time string every 30 seconds
  useEffect(() => {
    if (!lastFetchedAt) return;

    const interval = setInterval(() => {
      setFreshnessLabel(formatRelativeTime(lastFetchedAt));
    }, 30_000);

    return () => clearInterval(interval);
  }, [lastFetchedAt]);

  return { freshnessLabel, lastFetchedAt, updateFreshness };
}
