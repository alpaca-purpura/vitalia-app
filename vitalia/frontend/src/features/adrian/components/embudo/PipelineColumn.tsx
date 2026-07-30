// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * PipelineColumn — Droppable Kanban column for one funnel stage (D.3 spec).
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Shows: stage emoji + label · count + Σ value · overSLA badge · lead cards (ordered by stage_age_desc).
 * Droppable: useDroppable from @dnd-kit.
 * Accessible: aria-label on the column, aria-dropeffect during drag.
 *
 * spec_anchor: 01-spec.md § V1 D.3 + RN-11/17/18
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { useDroppable } from "@dnd-kit/core";
import { cn } from "@/lib/utils";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { formatMoney } from "@/lib/format/formatMoney";
import { LeadCard } from "./LeadCard";
import { STAGE_EMOJI, STAGE_LABELS } from "../../types/embudo-schema";
import type { BoardColumn, LeadFunnelStage } from "../../types/embudo.types";

// ── Props ─────────────────────────────────────────────────────────────────────

export interface PipelineColumnProps {
  column: BoardColumn;
  activeDragId: string | null;
  highlightLeadId?: string | null;
  onLeadDragStart: (leadId: string) => void;
  onLeadMoveStage?: (leadId: string) => void;
  isDropTarget?: boolean;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function PipelineColumn({
  column,
  activeDragId,
  highlightLeadId,
  onLeadDragStart,
  onLeadMoveStage,
  isDropTarget = false,
}: PipelineColumnProps) {
  const locale = useTenantLocale();

  const { setNodeRef, isOver } = useDroppable({
    id: column.stage,
    data: { stage: column.stage },
  });

  const emoji = STAGE_EMOJI[column.stage as LeadFunnelStage] ?? "⚪";
  const label = STAGE_LABELS[column.stage as LeadFunnelStage] ?? column.label;
  const sumFormatted =
    column.sumValue > 0
      ? formatMoney(column.sumValue, column.currency ?? locale.currency)
      : null;

  return (
    <div
      className="flex flex-col gap-2 min-w-[180px] max-w-[220px] flex-1"
      aria-label={`Columna ${label}: ${column.count} leads`}
      data-testid={`pipeline-column-${column.stage}`}
    >
      {/* Column header */}
      <div className="flex items-center justify-between px-1 pb-1 border-b border-border/60">
        <div className="flex items-center gap-1">
          <span aria-hidden="true" className="text-sm">{emoji}</span>
          <span className="font-medium text-sm text-foreground">{label}</span>
        </div>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <span>{column.count}</span>
          {sumFormatted && <span>· {sumFormatted}</span>}
          {column.overSlaCount > 0 && (
            <span
              className="ml-1 inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300 font-medium"
              title={`${column.overSlaCount} lead${column.overSlaCount > 1 ? "s" : ""} estancado${column.overSlaCount > 1 ? "s" : ""}`}
              aria-label={`${column.overSlaCount} estancados`}
            >
              ⚠ {column.overSlaCount}
            </span>
          )}
        </div>
      </div>

      {/* Drop zone */}
      <div
        ref={setNodeRef}
        className={cn(
          "flex flex-col gap-2 min-h-[120px] rounded-md p-1 transition-colors duration-150",
          isOver || isDropTarget
            ? "bg-primary/5 ring-1 ring-primary/30"
            : "bg-transparent",
        )}
        aria-dropeffect={activeDragId ? "move" : "none"}
        role="region"
        aria-label={`Soltar aquí para mover a ${label}`}
      >
        {column.leads.length === 0 ? (
          <div className="flex items-center justify-center h-16 text-xs text-muted-foreground italic">
            Sin leads
          </div>
        ) : (
          column.leads.map((lead) => (
            <LeadCard
              key={lead.id}
              lead={lead}
              onDragStart={onLeadDragStart}
              onMoveStage={onLeadMoveStage}
              isHighlighted={highlightLeadId === lead.id}
            />
          ))
        )}
      </div>
    </div>
  );
}
