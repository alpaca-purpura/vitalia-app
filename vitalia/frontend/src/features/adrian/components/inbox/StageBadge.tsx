// cap: adrian.inbox
// story-origin: vitalia-fase2-adrian-inbox
/**
 * StageBadge.tsx — Reusable lead-stage chip (UI-AUDIT-2026-06-04 #5b).
 *
 * Resolves label + differentiated color from `lead-stage-meta.ts` (SSoT), so the
 * inbox stops rendering flat neutral stage chips. Consumed by ConversationItem
 * (list row) and ContactSidebar (Estado / Etapa). Mirrors ChannelBadge's shape.
 *
 * Server-safe (no state/effects). Dark-aware via the meta color classes.
 *
 * downstream-regression-na: brand-local component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { getLeadStageMeta } from "@/lib/stages/lead-stage-meta";

interface StageBadgeProps {
  /** Lead stage slug (a LeadStage value). Unknown values get a neutral fallback.
   *  Typed as string (not the LeadStage union) so this molecule needs no
   *  cross-feature type import — getLeadStageMeta resolves + falls back. */
  stage: string;
  /** Override the test id (defaults to `stage-badge-{stage}`). Used to keep the
   *  legacy `stage-chip` id the inbox list tests + e2e POM depend on. */
  "data-testid"?: string;
  className?: string;
}

/**
 * StageBadge — compact pill identifying a lead's sales stage with a
 * stage-specific color (sky/amber/violet/indigo/emerald/rose).
 */
export function StageBadge({
  stage,
  "data-testid": testId,
  className,
}: StageBadgeProps) {
  const meta = getLeadStageMeta(stage);
  return (
    <span
      data-testid={testId ?? `stage-badge-${stage}`}
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium",
        meta.colorClass,
        className,
      )}
    >
      {meta.label}
    </span>
  );
}
