// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * PauseAdrianConfirmModal.tsx — Pause dialog with two duration choices.
 *
 * Chris UI (round 8): only two action buttons — "Pausar permanente" and
 * "Pausar 60 minutos". No reason/comment field. An X in the corner closes it.
 *
 * Pattern: controlled modal (native dialog semantics, role="dialog" + aria-modal).
 * Each button triggers usePauseAdrian via onConfirm(durationMinutes).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { X } from "lucide-react";
import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";
import { PERMANENT_PAUSE_MINUTES } from "../../api/use-pause-adrian";

interface PauseAdrianConfirmModalProps {
  /** Whether the modal is open */
  open: boolean;
  /** Called with the chosen pause duration in minutes */
  onConfirm: (durationMinutes: number) => void;
  /** Called when the user closes/cancels */
  onClose: () => void;
  /** Whether the pause mutation is in-flight */
  isPending?: boolean;
}

/**
 * PauseAdrianConfirmModal — pick a pause duration (permanent or 60 minutes).
 */
export function PauseAdrianConfirmModal({
  open,
  onConfirm,
  onClose,
  isPending = false,
}: PauseAdrianConfirmModalProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    if (e.key === "Escape" && !isPending) onClose();
  };

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget && !isPending) onClose();
      }}
      onKeyDown={handleKeyDown}
    >
      <div className="absolute inset-0 bg-black/40" aria-hidden="true" />

      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="pause-modal-title"
        aria-describedby="pause-modal-body"
        data-testid="pause-adrian-modal"
        className={cn(
          "relative z-10 w-full max-w-sm rounded-xl border vt-border",
          "vt-bg-surface p-6 shadow-lg",
        )}
      >
        {/* Close (X) — corner, not an action button */}
        <button
          type="button"
          onClick={onClose}
          disabled={isPending}
          data-testid="pause-modal-cancel"
          aria-label={INBOX_COPY.pauseAgent.cancelCta}
          title={INBOX_COPY.pauseAgent.cancelCta}
          className={cn(
            "absolute right-3 top-3 inline-flex h-7 w-7 items-center justify-center",
            "rounded-md cursor-pointer vt-text-muted hover:vt-text-foreground hover:vt-bg-muted",
            "transition-colors disabled:opacity-50",
          )}
        >
          <X className="h-4 w-4" aria-hidden focusable={false} />
        </button>

        <h2
          id="pause-modal-title"
          className="text-base font-semibold vt-text-foreground mb-2 pr-7"
        >
          {INBOX_COPY.pauseAgent.modalTitle}
        </h2>

        <p id="pause-modal-body" className="text-sm vt-text-muted mb-5">
          {INBOX_COPY.pauseAgent.modalBody}
        </p>

        {/* Two duration actions */}
        <div className="flex flex-col gap-2">
          <button
            type="button"
            onClick={() => onConfirm(60)}
            disabled={isPending}
            data-testid="pause-modal-60"
            className={cn(
              "w-full px-4 py-2.5 rounded-lg text-sm font-semibold cursor-pointer",
              "vt-bg-danger-12 vt-text-danger hover:vt-bg-danger-soft",
              "transition-colors disabled:opacity-50",
            )}
            aria-busy={isPending}
          >
            {INBOX_COPY.pauseAgent.confirm60}
          </button>

          <button
            type="button"
            onClick={() => onConfirm(PERMANENT_PAUSE_MINUTES)}
            disabled={isPending}
            data-testid="pause-modal-permanent"
            className={cn(
              "w-full px-4 py-2.5 rounded-lg text-sm font-semibold cursor-pointer",
              "text-white bg-[var(--vitalia-danger-color)] hover:opacity-90",
              "transition-opacity disabled:opacity-50",
            )}
            aria-busy={isPending}
          >
            {INBOX_COPY.pauseAgent.confirmPermanent}
          </button>
        </div>
      </div>
    </div>
  );
}
