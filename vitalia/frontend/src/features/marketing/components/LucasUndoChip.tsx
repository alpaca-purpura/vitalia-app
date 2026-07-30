// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * LucasUndoChip — 5-min countdown undo chip shown after approving a recommendation
 * Reads pendingUndoTimers from useMarketingStore.
 * When timer expires, chip disappears automatically.
 * SC-MK-01: post-approve undo window
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { useCallback, useEffect, useState } from "react";
import { MARKETING_COPY } from "../copy";
import { useMarketingStore } from "../store/marketing-store";
import { useUndoRecommendation } from "../api/use-undo-recommendation";

export type LucasUndoChipProps = {
  recId: string;
};

function formatCountdown(msRemaining: number): string {
  if (msRemaining <= 0) return "00:00";
  const totalSeconds = Math.floor(msRemaining / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
}

export function LucasUndoChip({ recId }: LucasUndoChipProps) {
  const pendingUndoTimers = useMarketingStore((s) => s.pendingUndoTimers);
  const clearPendingUndoTimer = useMarketingStore(
    (s) => s.clearPendingUndoTimer,
  );
  const undo = useUndoRecommendation();

  const [msRemaining, setMsRemaining] = useState<number | null>(null);

  const expiryMs = pendingUndoTimers.get(recId) ?? null;

  // Tick countdown every second
  useEffect(() => {
    if (expiryMs === null) {
      setMsRemaining(null);
      return;
    }

    const tick = () => {
      const remaining = expiryMs - Date.now();
      if (remaining <= 0) {
        setMsRemaining(0);
        clearPendingUndoTimer(recId);
      } else {
        setMsRemaining(remaining);
      }
    };

    tick(); // immediate
    const interval = setInterval(tick, 1000);
    return () => clearInterval(interval);
  }, [expiryMs, recId, clearPendingUndoTimer]);

  // Must be before any conditional return (hooks rules)
  const handleUndo = useCallback(async () => {
    try {
      await undo.mutateAsync({ recId });
      clearPendingUndoTimer(recId);
    } catch {
      // BE returns 410 if window expired; chip will auto-hide on next tick
    }
  }, [undo, recId, clearPendingUndoTimer]);

  // Not in store or expired
  if (expiryMs === null || msRemaining === null || msRemaining <= 0) {
    return null;
  }

  return (
    <div
      className="flex items-center gap-2 px-3 py-1.5 rounded-full border vt-border bg-amber-50 text-amber-800 text-xs font-medium"
      role="status"
      aria-live="polite"
      aria-label={`${MARKETING_COPY.recommendations.undoTimerLabel} ${formatCountdown(msRemaining)}`}
    >
      <span className="text-amber-600">
        {MARKETING_COPY.recommendations.undoTimerLabel}
      </span>
      <span className="font-mono font-semibold tabular-nums">
        {formatCountdown(msRemaining)}
      </span>
      <button
        type="button"
        onClick={() => void handleUndo()}
        disabled={undo.isPending}
        className="ml-1 px-2 py-0.5 rounded-full vt-bg-tab-active vt-text-cian-bold text-xs font-semibold hover:opacity-80 transition-opacity disabled:opacity-50"
        aria-label={MARKETING_COPY.recommendations.undoButton}
      >
        {undo.isPending ? "..." : MARKETING_COPY.recommendations.undoButton}
      </button>
    </div>
  );
}
