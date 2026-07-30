// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadCard — Draggable card for Kanban board (D.4 spec).
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * spec_anchor: 01-spec.md § V1 LeadCard + D.4/D.13
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { useCallback, useMemo } from "react";
import { useDraggable } from "@dnd-kit/core";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { ChannelBadge } from "@/components/shared/shell-organism/ChannelBadge";
import { ScoreDonut } from "@/components/shared/score/ScoreDonut";
import { useTenantId } from "@/hooks/useTenantId";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { formatMoney } from "@/lib/format/formatMoney";
import { STAGE_SLA_DAYS } from "../../types/embudo-schema";
import { ChevronRight } from "lucide-react";
import type { LeadCardDTO, LeadFunnelStage } from "../../types/embudo.types";

type SlaStatus = "green" | "amber" | "red";

function computeSlaStatus(
  stage: LeadFunnelStage,
  stageEnteredAt: string | null,
): { status: SlaStatus; daysText: string } {
  const slaGreen = STAGE_SLA_DAYS[stage];
  if (!slaGreen || !stageEnteredAt) return { status: "green", daysText: "" };
  const days = Math.floor(
    (Date.now() - new Date(stageEnteredAt).getTime()) / (1000 * 60 * 60 * 24),
  );
  const status: SlaStatus =
    days >= slaGreen * 2 ? "red" : days >= slaGreen ? "amber" : "green";
  return { status, daysText: days === 0 ? "<1d" : `${days}d` };
}

const SLA_DOT_CLASS: Record<SlaStatus, string> = {
  green: "bg-emerald-500",
  amber: "bg-amber-500",
  red: "bg-red-500",
};
const SLA_TEXT_CLASS: Record<SlaStatus, string> = {
  green: "text-emerald-700 dark:text-emerald-400",
  amber: "text-amber-700 dark:text-amber-400",
  red: "text-red-700 dark:text-red-400",
};

export interface LeadCardProps {
  lead: LeadCardDTO;
  onDragStart?: (leadId: string) => void;
  /** Optional handler for non-drag stage move — fires the same PATCH as DnD.
   *  When provided, a ›Mover etapa button is shown for E2E/keyboard access (SC-10 a11y). */
  onMoveStage?: (leadId: string) => void;
  isHighlighted?: boolean;
  className?: string;
}

export function LeadCard({
  lead,
  onDragStart,
  onMoveStage,
  isHighlighted = false,
  className,
}: LeadCardProps) {
  const tenantId = useTenantId();
  const locale = useTenantLocale();

  const { attributes, listeners, setNodeRef, isDragging, transform } =
    useDraggable({ id: lead.id, data: { lead } });

  const sla = useMemo(
    () => computeSlaStatus(lead.stage, lead.stageEnteredAt ?? null),
    [lead.stage, lead.stageEnteredAt],
  );

  const handleMouseDown = useCallback(() => {
    onDragStart?.(lead.id);
  }, [lead.id, onDragStart]);

  const style = transform
    ? { transform: `translate3d(${transform.x}px, ${transform.y}px, 0)` }
    : undefined;

  const detailHref = tenantId
    ? `/${tenantId}/adrian/embudo/${lead.id}/resumen`
    : "#";

  const buyingSignals = lead.buyingSignals ?? [];
  const signalChips = buyingSignals.slice(0, 2);
  const extraSignals = buyingSignals.length - signalChips.length;

  const tempBorderClass =
    lead.temperature === "hot"
      ? "border-l-2 border-l-red-400"
      : lead.temperature === "warm"
        ? "border-l-2 border-l-amber-400"
        : "border-l-2 border-l-slate-300 dark:border-l-slate-600";

  return (
    <article
      ref={setNodeRef}
      data-testid={`lead-card-${lead.id}`}
      aria-label={`Lead en etapa ${lead.stage}`}
      aria-grabbed={isDragging}
      style={style}
      className={cn(
        "relative rounded-md border border-border bg-card p-2.5 text-xs",
        "cursor-grab active:cursor-grabbing",
        "hover:border-primary/40 hover:shadow-sm transition-[border,shadow] duration-150",
        tempBorderClass,
        isDragging && "opacity-50 z-50 shadow-lg",
        isHighlighted && "ring-2 ring-primary ring-offset-1 animate-pulse",
        className,
      )}
      onMouseDown={handleMouseDown}
      {...listeners}
      {...attributes}
    >
      {/* Row 1: Name + Operator badge */}
      <div className="flex items-start justify-between gap-1 mb-1.5">
        <Link
          href={detailHref}
          className="font-medium text-foreground hover:text-primary hover:underline truncate max-w-[120px]"
          onClick={(e) => { if (isDragging) e.preventDefault(); }}
          tabIndex={isDragging ? -1 : 0}
        >
          {lead.name}
        </Link>
        <span
          className={cn(
            "shrink-0 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded-full text-xs font-medium",
            lead.operatedBy === "agent"
              ? "bg-[hsl(var(--agent-adrian-soft))] text-[hsl(var(--agent-adrian))]"
              : "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
          )}
          title={lead.operatedBy === "agent" ? "Adrián opera esta conversación" : "Un humano tomó control"}
        >
          {lead.operatedBy === "agent" ? "🤖 Adrián" : "🙋 Tú"}
        </span>
      </div>

      {/* Row 2: Value + Channel + Score */}
      <div className="flex items-center gap-2 mb-1.5 flex-wrap">
        {lead.estimatedValue != null && (
          <span className="text-muted-foreground font-medium">
            {formatMoney(lead.estimatedValue, lead.currency ?? locale.currency)}
          </span>
        )}
        {lead.channel && <ChannelBadge channel={lead.channel} iconOnly />}
        {lead.score != null && (
          <ScoreDonut score={lead.score} className="ml-auto" />
        )}
      </div>

      {/* Row 3: Buying signals */}
      {signalChips.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-1.5">
          {signalChips.map((sig) => (
            <span
              key={sig}
              className="inline-flex items-center gap-0.5 bg-muted px-1.5 py-0.5 rounded text-xs"
            >
              {sig === "pregunto_precio" && "💬 preguntó precio"}
              {sig === "urgencia" && "⏰ urgencia"}
              {sig === "presupuesto_ok" && "✅ presupuesto ok"}
              {sig !== "pregunto_precio" && sig !== "urgencia" && sig !== "presupuesto_ok" && sig}
            </span>
          ))}
          {extraSignals > 0 && (
            <span className="text-muted-foreground">+{extraSignals}</span>
          )}
        </div>
      )}

      {/* Row 4: SLA + micro-log */}
      <div className="flex items-center justify-between gap-2">
        {sla.daysText && (
          <div className="flex items-center gap-1" aria-label={`Tiempo en etapa: ${sla.daysText}`}>
            <span className={cn("inline-block h-2 w-2 rounded-full", SLA_DOT_CLASS[sla.status])} aria-hidden />
            <span className={cn("text-xs", SLA_TEXT_CLASS[sla.status])}>{sla.daysText}</span>
          </div>
        )}
        {lead.lastActivityDescription && (
          <span className="text-muted-foreground text-xs truncate max-w-[100px]" title={lead.lastActivityDescription}>
            {lead.lastActivityDescription}
          </span>
        )}
      </div>

      {/* Row 5: Special badges + move affordance (non-drag for E2E/a11y) */}
      <div className="mt-1.5 flex flex-wrap gap-1 items-center justify-between">
        {lead.depositStatus === "pending" && (
          <span className="inline-flex items-center gap-0.5 bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 px-1.5 py-0.5 rounded text-xs font-medium">
            💳 Esperando pago
          </span>
        )}
        {lead.depositStatus === "received" && (
          <span className="inline-flex items-center gap-0.5 bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300 px-1.5 py-0.5 rounded text-xs font-medium">
            ✅ Depósito recibido
          </span>
        )}
        {lead.reactivationCohortAt && (
          <span className="inline-flex items-center gap-0.5 bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300 px-1.5 py-0.5 rounded text-xs">
            ↻ Camila reactiva 90d
          </span>
        )}
      </div>
      {/* Move-stage affordance: non-drag path for E2E + keyboard users (SC-10) */}
      {onMoveStage && lead.stage !== "reservado" && (
        <button
          type="button"
          data-testid={`move-stage-${lead.id}`}
          aria-label="Mover a siguiente etapa"
          title="Mover a siguiente etapa"
          className="shrink-0 inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded text-xs text-muted-foreground hover:text-primary hover:bg-primary/10 transition-colors"
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            onMoveStage(lead.id);
          }}
        >
          <ChevronRight className="h-3 w-3" aria-hidden />
        </button>
      )}
    </article>
  );
}
