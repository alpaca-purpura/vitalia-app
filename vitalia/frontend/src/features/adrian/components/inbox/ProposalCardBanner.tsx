// cap: adrian.inbox
// story-origin: TBD
"use client";

/**
 * ProposalCardBanner.tsx — Banner displayed when handler_mode="Adrián consulta"
 * and there is a pending proposal waiting for operator approval.
 *
 * Shows:
 *   - "Adrián tiene una propuesta lista" heading
 *   - [Aprobar y enviar] / [Editar propuesta] buttons
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

export interface ProposalCardBannerProps {
  proposedText: string;
  onApprove: () => void;
  onEdit: () => void;
  isApproving?: boolean;
  className?: string;
}

/**
 * ProposalCardBanner — approval banner for agent-waiting-approval state.
 */
export function ProposalCardBanner({
  proposedText,
  onApprove,
  onEdit,
  isApproving,
  className,
}: ProposalCardBannerProps) {
  return (
    <div
      className={cn(
        "rounded-xl border vt-border-cian vt-bg-cian-8 p-3 flex flex-col gap-2",
        className,
      )}
      role="region"
      aria-label={INBOX_COPY.proposalCardBanner.heading}
    >
      {/* Header */}
      <div className="flex items-start gap-2">
        <span
          className={cn(
            "text-xs font-semibold px-1.5 py-0.5 rounded-full",
            "vt-bg-gradient-agent text-white",
          )}
          aria-hidden="true"
        >
          ✨
        </span>
        <div className="flex flex-col gap-0.5 min-w-0">
          <p className="text-xs font-semibold vt-text">
            {INBOX_COPY.proposalCardBanner.heading}
          </p>
          <p className="text-xs vt-text-muted">
            {INBOX_COPY.proposalCardBanner.body}
          </p>
        </div>
      </div>

      {/* Proposed text preview (read-only) */}
      {proposedText && (
        <div
          className={cn(
            "rounded-lg px-2.5 py-2 text-sm vt-text",
            "vt-bg-surface border vt-border-soft",
            "max-h-24 overflow-y-auto",
          )}
        >
          {/* SC-04: React escapes proposedText — no dangerouslySetInnerHTML */}
          {proposedText}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={onEdit}
          disabled={isApproving}
          className={cn(
            "text-xs px-3 py-1.5 rounded-lg",
            "vt-bg-surface border vt-border vt-text-muted",
            "hover:vt-text-cian hover:vt-border-cian transition-colors",
            "disabled:opacity-50 disabled:cursor-not-allowed",
          )}
        >
          {INBOX_COPY.proposalCardBanner.editCta}
        </button>
        <button
          type="button"
          onClick={onApprove}
          disabled={isApproving}
          aria-busy={isApproving}
          className={cn(
            "text-xs px-3 py-1.5 rounded-lg font-semibold",
            "text-white vt-bg-gradient-agent",
            "disabled:opacity-50 disabled:cursor-not-allowed",
            "transition-opacity",
          )}
        >
          {isApproving ? "…" : INBOX_COPY.proposalCardBanner.approveCta}
        </button>
      </div>
    </div>
  );
}
