// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * FreshnessIndicator.tsx — "Actualizado hace Xs/Xm" live timestamp + manual refresh.
 * T-13 vitalia-fase2-valeria-agenda · F2-S1
 *
 * Displays time since last successful data fetch.
 * Auto-updates every 30 seconds (matches polling interval).
 * Manual refresh button triggers parent invalidation via onRefresh callback.
 *
 * Spec anchor: 03-arch.md § real-time + 01-spec.md Q12 batch_3
 * Spanish neutro LatAm — sin voseo.
 * ARIA: aria-live="polite" for screen readers.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState, useEffect, useCallback } from "react";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";
import { formatRelativeTime } from "../../lib/freshness";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FreshnessIndicatorProps {
  /**
   * ISO 8601 timestamp of last successful data fetch.
   * Null = no data fetched yet (renders "—").
   */
  lastFetchedAt: string | null;
  /**
   * Callback to trigger a manual refresh.
   * Should invalidate the relevant React Query keys.
   */
  onRefresh: () => void;
  /** Whether a refresh is currently in progress. */
  isRefreshing?: boolean;
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Live freshness label + manual refresh button.
 *
 * Renders "Actualizado hace X" with live updates every 30 seconds.
 * Uses aria-live="polite" so screen readers announce updates without interrupting.
 */
export function FreshnessIndicator({
  lastFetchedAt,
  onRefresh,
  isRefreshing = false,
  className,
}: FreshnessIndicatorProps) {
  const [label, setLabel] = useState<string>(() =>
    lastFetchedAt ? formatRelativeTime(lastFetchedAt) : "—",
  );

  // Update label whenever lastFetchedAt changes
  useEffect(() => {
    setLabel(lastFetchedAt ? formatRelativeTime(lastFetchedAt) : "—");
  }, [lastFetchedAt]);

  // Refresh label every 30 seconds (matches grid polling interval)
  useEffect(() => {
    if (!lastFetchedAt) return;

    const interval = setInterval(() => {
      setLabel(formatRelativeTime(lastFetchedAt));
    }, 30_000);

    return () => clearInterval(interval);
  }, [lastFetchedAt]);

  const handleRefresh = useCallback(() => {
    onRefresh();
  }, [onRefresh]);

  return (
    <div
      className={cn(
        "flex items-center gap-1.5 text-xs text-muted-foreground",
        className,
      )}
      data-testid="freshness-indicator"
      aria-live="polite"
      aria-label="Estado de actualización"
    >
      <span
        data-testid="freshness-label"
        className="tabular-nums"
      >
        {label}
      </span>

      <Button
        variant="ghost"
        size="icon"
        className="h-5 w-5 rounded-sm text-muted-foreground hover:text-foreground"
        onClick={handleRefresh}
        aria-label="Actualizar agenda"
        disabled={isRefreshing}
        title="Actualizar"
      >
        <RefreshCw
          className={cn("h-3 w-3", isRefreshing && "animate-spin")}
          aria-hidden="true"
        />
      </Button>
    </div>
  );
}
