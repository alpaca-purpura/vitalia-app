// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * NudgeButton.tsx — T-5 NEW.
 *
 * Button + confirm dialog to send a nudge (empujón 1:1 re-engagement)
 * to a stalled conversation.
 *
 * Uses useNudge mutation hook.
 * Shows toast on success/error via sonner.
 *
 * Only enabled when:
 *   - conversation is live (handler_mode = 'ai', not paused)
 *   - conversation appears stalled (last message > configured threshold)
 *   Fallback: always enabled unless explicitly disabled by caller.
 *
 * Confirm dialog (shadcn AlertDialog):
 *   "¿Dar un empujón a esta conversación?"
 *   "Adrián va a enviar un mensaje de reactivación al paciente."
 *   [Dar empujón] [Cancelar]
 *
 * "use client" required — uses hooks + event handlers.
 *
 * Spanish neutro LatAm — no voseo.
 * No hardcoded hex — tokens only.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

"use client";

import { useState, useCallback } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/cn";
import { useNudge } from "../../api/use-nudge";
import { INBOX_COPY } from "../../lib/copy";

// ── Props ────────────────────────────────────────────────────────────────────

export interface NudgeButtonProps {
  conversationId: string;
  /** When false, button is shown but greyed out with tooltip explanation */
  isEnabled?: boolean;
  className?: string;
}

// ── NudgeButton ──────────────────────────────────────────────────────────────

/**
 * NudgeButton — sends a 1:1 re-engagement nudge with confirm dialog.
 *
 * Renders as a single button (compact) for ThreadHeader area.
 * Confirm is done inline via a simple confirm state (no modal overhead for MVP).
 */
export function NudgeButton({
  conversationId,
  isEnabled = true,
  className,
}: NudgeButtonProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const { mutate: sendNudge, isPending } = useNudge();

  const handleOpenConfirm = useCallback(() => {
    if (!isEnabled || isPending) return;
    setConfirmOpen(true);
  }, [isEnabled, isPending]);

  const handleConfirm = useCallback(() => {
    setConfirmOpen(false);
    sendNudge(
      { conversationId },
      {
        onSuccess: () => {
          toast.success(INBOX_COPY.nudge.toastSuccess);
        },
        onError: () => {
          toast.error(INBOX_COPY.nudge.toastError);
        },
      },
    );
  }, [conversationId, sendNudge]);

  const handleCancel = useCallback(() => {
    setConfirmOpen(false);
  }, []);

  if (confirmOpen) {
    return (
      <div
        role="alertdialog"
        aria-modal="false"
        aria-label={INBOX_COPY.nudge.confirmTitle}
        data-testid="nudge-confirm"
        className={cn(
          "inline-flex items-center gap-1.5 rounded-lg border vt-border",
          "vt-bg-surface px-3 py-1.5 text-xs shadow-sm",
          className,
        )}
      >
        <span className="vt-text-foreground font-medium mr-1">
          {INBOX_COPY.nudge.confirmQuestion}
        </span>
        <button
          type="button"
          onClick={handleConfirm}
          disabled={isPending}
          data-testid="nudge-confirm-yes"
          className={cn(
            "cursor-pointer rounded px-2 py-0.5 text-xs font-semibold transition-colors",
            "vt-bg-primary/12 vt-text-primary hover:vt-bg-primary/20",
            "focus-visible:outline focus-visible:outline-2",
            "focus-visible:outline-[var(--agent-adrian)]",
            "disabled:opacity-50 disabled:cursor-not-allowed",
          )}
        >
          {isPending ? INBOX_COPY.nudge.sendingCta : INBOX_COPY.nudge.confirmCta}
        </button>
        <button
          type="button"
          onClick={handleCancel}
          data-testid="nudge-confirm-cancel"
          className={cn(
            "cursor-pointer rounded px-2 py-0.5 text-xs transition-colors",
            "vt-bg-muted vt-text-muted hover:vt-bg-muted/80",
            "focus-visible:outline focus-visible:outline-2",
            "focus-visible:outline-[var(--agent-adrian)]",
          )}
        >
          {INBOX_COPY.nudge.cancelCta}
        </button>
      </div>
    );
  }

  return (
    <button
      type="button"
      aria-label={
        isEnabled
          ? INBOX_COPY.nudge.ariaEnabled
          : INBOX_COPY.nudge.ariaDisabled
      }
      title={
        isEnabled
          ? INBOX_COPY.nudge.titleEnabled
          : INBOX_COPY.nudge.titleDisabled
      }
      data-testid="nudge-button"
      disabled={!isEnabled || isPending}
      onClick={handleOpenConfirm}
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-2.5 py-1.5",
        "text-xs font-medium transition-colors",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2",
        "focus-visible:outline-[var(--agent-adrian)]",
        "disabled:opacity-40 disabled:cursor-not-allowed",
        isEnabled
          ? "cursor-pointer vt-bg-surface vt-text-muted hover:vt-bg-muted"
          : "vt-bg-muted vt-text-muted",
        className,
      )}
    >
      <span aria-hidden="true">📤</span>
      <span>{INBOX_COPY.nudge.button}</span>
    </button>
  );
}
