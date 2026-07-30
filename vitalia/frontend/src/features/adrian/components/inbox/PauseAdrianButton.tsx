// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * PauseAdrianButton.tsx — Button to pause Adrián for 60 minutes.
 *
 * States:
 *   - Adrián active: shows "Pausar Adrián" (pause_until is null or expired)
 *   - Adrián paused: shows "Adrián pausado" (disabled, shows remaining time)
 *
 * Opens PauseAdrianConfirmModal on click (when active).
 * After confirmation: fires usePauseAdrian mutation.
 * On success: shows toast via onSuccess callback.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState } from "react";
import { Pause } from "lucide-react";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";
import { PauseAdrianConfirmModal } from "./PauseAdrianConfirmModal";
import { usePauseAdrian } from "../../api/use-pause-adrian";

interface PauseAdrianButtonProps {
  conversationId: string;
  /** ISO 8601 datetime when Adrián resumes (null = not paused) */
  pauseUntil: string | null;
  /** Called after successful pause (for toast) */
  onPauseSuccess?: () => void;
  className?: string;
}

/** Returns true if the pause_until timestamp is still in the future */
function isPausedNow(pauseUntil: string | null): boolean {
  if (!pauseUntil) return false;
  return new Date(pauseUntil) > new Date();
}

/**
 * PauseAdrianButton — trigger to pause Adrián for 60 minutes.
 * Opens confirmation modal on click; disabled when already paused.
 */
export function PauseAdrianButton({
  conversationId,
  pauseUntil,
  onPauseSuccess,
  className,
}: PauseAdrianButtonProps) {
  const [modalOpen, setModalOpen] = useState(false);
  const { mutate, isPending } = usePauseAdrian();

  const paused = isPausedNow(pauseUntil);

  const handleConfirm = (durationMinutes: number) => {
    mutate(
      { conversationId, durationMinutes },
      {
        onSuccess: () => {
          setModalOpen(false);
          onPauseSuccess?.();
        },
        onError: () => {
          setModalOpen(false);
        },
      },
    );
  };

  return (
    <>
      <button
        onClick={() => {
          if (!paused && !isPending) setModalOpen(true);
        }}
        disabled={paused || isPending}
        data-testid="pause-adrian-button"
        aria-label={
          paused
            ? INBOX_COPY.pauseAgent.buttonActive
            : INBOX_COPY.pauseAgent.button
        }
        title={
          paused
            ? INBOX_COPY.pauseAgent.buttonActive
            : INBOX_COPY.pauseAgent.button
        }
        className={cn(
          "inline-flex items-center gap-1.5 rounded-lg",
          "px-3 py-1.5 text-xs font-semibold transition-colors",
          "focus-visible:outline focus-visible:outline-2",
          "focus-visible:outline-[var(--vitalia-danger)]",
          // Soft-red, prominent so the operator can grab the conversation fast (Chris UI #4).
          paused
            ? "vt-text-muted opacity-50 cursor-not-allowed border vt-border"
            : "cursor-pointer vt-bg-danger-12 vt-text-danger hover:vt-bg-danger-soft",
          isPending && "opacity-50 cursor-wait",
          className,
        )}
        aria-busy={isPending}
      >
        <Pause className="h-3.5 w-3.5 shrink-0" aria-hidden focusable={false} />
        <span>{paused ? "Pausado" : "Pausar"}</span>
      </button>

      <PauseAdrianConfirmModal
        open={modalOpen}
        onConfirm={handleConfirm}
        onClose={() => setModalOpen(false)}
        isPending={isPending}
      />
    </>
  );
}
