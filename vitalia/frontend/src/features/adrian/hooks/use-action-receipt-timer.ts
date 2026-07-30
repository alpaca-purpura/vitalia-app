// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * use-action-receipt-timer.ts — Countdown timer for ActionReceipt undo chip.
 *
 * Tracks remaining seconds until the undo window expires (5 minutes = 300s).
 * Returns remainingSeconds + isExpired + formatted label for the undo chip.
 *
 * Updates every second via setInterval.
 * Cleans up interval on unmount (no memory leak).
 *
 * downstream-regression-na: brand-local FE hook; no cross-brand consumers
 */

import { useState, useEffect, useCallback } from "react";

export interface UseActionReceiptTimerResult {
  /** Remaining seconds (0 when expired) */
  remainingSeconds: number;
  /** True when the window has expired */
  isExpired: boolean;
  /** Formatted label e.g. "4:32" */
  formattedRemaining: string;
}

/**
 * Countdown timer for the undo chip.
 *
 * @param expiresAt - ISO 8601 string from action_receipt_expires_at. Pass null to disable.
 */
export function useActionReceiptTimer(
  expiresAt: string | null | undefined,
): UseActionReceiptTimerResult {
  const computeRemaining = useCallback((): number => {
    if (!expiresAt) return 0;
    const diffMs = new Date(expiresAt).getTime() - Date.now();
    return Math.max(0, Math.floor(diffMs / 1000));
  }, [expiresAt]);

  const [remainingSeconds, setRemainingSeconds] =
    useState<number>(computeRemaining);

  useEffect(() => {
    if (!expiresAt) {
      setRemainingSeconds(0);
      return;
    }

    // Update immediately on mount
    setRemainingSeconds(computeRemaining());

    const interval = setInterval(() => {
      const remaining = computeRemaining();
      setRemainingSeconds(remaining);
      if (remaining === 0) {
        clearInterval(interval);
      }
    }, 1000);

    return () => {
      clearInterval(interval);
    };
  }, [expiresAt, computeRemaining]);

  const isExpired = remainingSeconds <= 0;

  const formattedRemaining: string = isExpired
    ? "0:00"
    : `${Math.floor(remainingSeconds / 60)}:${String(remainingSeconds % 60).padStart(2, "0")}`;

  return { remainingSeconds, isExpired, formattedRemaining };
}
