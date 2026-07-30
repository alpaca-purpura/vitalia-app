// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ActionReceiptUndoChip.tsx — Countdown chip for reversing an AI-sent message.
 *
 * Displays "↩ Revertir (4:58)" with a live countdown until the 5-minute window expires.
 * On click: shows a confirm dialog, then calls useRetractMessage mutation.
 *
 * SC-01 coverage: countdown visible after agent_ai message send.
 *
 * Accessibility: aria-live="polite" for countdown, role="timer".
 * Dialog pattern: native role="dialog" + aria-modal (no Shadcn dependency).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { useState } from "react";
import { cn } from "@/lib/cn";
import { useActionReceiptTimer } from "../../hooks/use-action-receipt-timer";
import { useRetractMessage } from "../../api/use-retract-message";
import { INBOX_COPY } from "../../lib/copy";

export interface ActionReceiptUndoChipProps {
  /** Message ID to retract */
  messageId: string;
  /** Conversation ID (needed for mutation) */
  conversationId: string;
  /** ISO 8601 expiry timestamp from action_receipt_expires_at */
  expiresAt: string;
  /** OCC: conversation.updated_at used as ETag */
  conversationUpdatedAt: string;
  className?: string;
}

/**
 * ActionReceiptUndoChip — inline countdown chip for AI-sent message undo.
 * Disappears automatically when the timer expires.
 */
export function ActionReceiptUndoChip({
  messageId,
  conversationId,
  expiresAt,
  conversationUpdatedAt,
  className,
}: ActionReceiptUndoChipProps) {
  const { isExpired, formattedRemaining } = useActionReceiptTimer(expiresAt);
  const retractMutation = useRetractMessage();
  const [open, setOpen] = useState(false);

  // Once expired, chip disappears
  if (isExpired) return null;

  const isRetracting = retractMutation.isPending;

  const handleConfirm = () => {
    retractMutation.mutate(
      { conversationId, messageId, expectedUpdatedAt: conversationUpdatedAt },
      {
        onSuccess: () => {
          setOpen(false);
        },
        onError: () => {
          setOpen(false);
        },
      },
    );
  };

  const ariaLabel = INBOX_COPY.actionReceipt.revertAriaLabel.replace(
    "{remaining}",
    formattedRemaining,
  );

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        disabled={isRetracting}
        aria-label={ariaLabel}
        className={cn(
          "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5",
          "text-xs font-medium border",
          "vt-bg-muted vt-text-muted vt-border",
          "hover:vt-bg-cian-8 hover:vt-text-cian hover:vt-border-cian",
          "transition-colors duration-150 cursor-pointer",
          "disabled:opacity-60 disabled:cursor-not-allowed",
          className,
        )}
      >
        <span aria-hidden="true">↩</span>
        <span>{INBOX_COPY.actionReceipt.revertCta}</span>
        <span role="timer" aria-live="polite" aria-label={ariaLabel}>
          ({formattedRemaining})
        </span>
      </button>

      {/* Confirm modal */}
      {open && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          role="presentation"
          onClick={(e) => {
            if (e.target === e.currentTarget && !isRetracting) setOpen(false);
          }}
        >
          <div className="absolute inset-0 bg-black/40" aria-hidden="true" />
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="retract-modal-title"
            aria-describedby="retract-modal-body"
            data-testid="retract-confirm-modal"
            className={cn(
              "relative z-10 w-full max-w-sm rounded-xl border vt-border",
              "vt-bg-surface p-6 shadow-lg",
            )}
          >
            <h2
              id="retract-modal-title"
              className="text-base font-semibold vt-text mb-2"
            >
              {INBOX_COPY.actionReceipt.modalTitle}
            </h2>
            <p id="retract-modal-body" className="text-sm vt-text-muted mb-6">
              {INBOX_COPY.actionReceipt.modalBody}
            </p>
            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={() => setOpen(false)}
                disabled={isRetracting}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium",
                  "vt-text-muted vt-bg-muted border vt-border",
                  "hover:vt-text transition-colors disabled:opacity-50",
                )}
              >
                {INBOX_COPY.actionReceipt.cancelCta}
              </button>
              <button
                type="button"
                onClick={handleConfirm}
                disabled={isRetracting}
                aria-busy={isRetracting}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium",
                  "vt-bg-danger-12 vt-text-danger border vt-border-danger-30",
                  "hover:vt-bg-danger-soft transition-colors disabled:opacity-50",
                )}
              >
                {isRetracting ? "…" : INBOX_COPY.actionReceipt.confirmCta}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
