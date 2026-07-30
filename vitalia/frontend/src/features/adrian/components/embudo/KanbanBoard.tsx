// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * KanbanBoard — DndContext wrapper for Kanban columns (D.3 spec, @dnd-kit).
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Sensors: PointerSensor (mouse/touch) + KeyboardSensor (a11y SC-10).
 * Drop logic: calls onStageDrop(leadId, fromStage, toStage).
 * Reservado guard: toast + no-op (RN-4/5).
 * Same-column drop: no-op (RN-17).
 *
 * spec_anchor: 01-spec.md § V1 drag + D.3/D.13 + RN-4/17
 */
"use client";

import { useCallback } from "react";
import {
  DndContext,
  PointerSensor,
  KeyboardSensor,
  useSensor,
  useSensors,
  DragOverlay,
  type DragEndEvent,
  type DragStartEvent,
  closestCenter,
} from "@dnd-kit/core";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { PipelineColumn } from "./PipelineColumn";
import { LeadCard } from "./LeadCard";
import type { BoardColumn, LeadCardDTO, LeadFunnelStage } from "../../types/embudo.types";

export interface KanbanBoardProps {
  columns: BoardColumn[];
  activeLeadId: string | null;
  highlightLeadId?: string | null;
  onStageDrop: (
    leadId: string,
    lead: LeadCardDTO,
    fromStage: LeadFunnelStage,
    toStage: LeadFunnelStage,
  ) => void;
  /** Non-drag path: move lead to next adjacent stage (button on card for E2E/a11y). */
  onMoveStage?: (leadId: string) => void;
  onDragStart?: (leadId: string) => void;
  onDragCancel?: () => void;
  className?: string;
}

export function KanbanBoard({
  columns,
  activeLeadId,
  highlightLeadId,
  onStageDrop,
  onMoveStage,
  onDragStart,
  onDragCancel,
  className,
}: KanbanBoardProps) {
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 4 } }),
    useSensor(KeyboardSensor),
  );

  const findLead = useCallback(
    (id: string): { lead: LeadCardDTO; stage: LeadFunnelStage } | null => {
      for (const col of columns) {
        const lead = col.leads.find((l) => l.id === id);
        if (lead) return { lead, stage: col.stage };
      }
      return null;
    },
    [columns],
  );

  const handleDragStart = useCallback(
    (event: DragStartEvent) => {
      onDragStart?.(String(event.active.id));
    },
    [onDragStart],
  );

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;
      if (!over) { onDragCancel?.(); return; }
      const leadId = String(active.id);
      const toStage = String(over.id) as LeadFunnelStage;
      const found = findLead(leadId);
      if (!found) { onDragCancel?.(); return; }
      const { lead, stage: fromStage } = found;
      if (fromStage === toStage) { onDragCancel?.(); return; }
      if (toStage === "reservado") {
        toast.warning("🔒 Reservado se alcanza con el depósito", {
          description: "El pago confirma automáticamente esta etapa.",
        });
        onDragCancel?.();
        return;
      }
      onStageDrop(leadId, lead, fromStage, toStage);
    },
    [findLead, onStageDrop, onDragCancel],
  );

  const activeLead = activeLeadId ? findLead(activeLeadId)?.lead : null;

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
      onDragCancel={() => onDragCancel?.()}
      accessibility={{
        announcements: {
          onDragStart: () => "Moviendo lead. Usa las flechas para cambiar de columna. Presiona Esc para cancelar.",
          onDragOver: ({ over }) =>
            over ? `Lead sobre columna ${String(over.id)}. Suelta para mover.` : "Fuera de área válida.",
          onDragEnd: ({ over }) =>
            over ? `Lead movido a ${String(over.id)}.` : "Movimiento cancelado.",
          onDragCancel: () => "Movimiento cancelado.",
        },
        screenReaderInstructions: {
          draggable: "Para arrastrar, presiona Espacio. Usa flechas para mover. Suelta con Espacio.",
        },
      }}
    >
      <div
        className={cn("overflow-x-auto pb-2", className)}
        role="region"
        aria-label="Tablero de leads"
        data-testid="kanban-board"
      >
        <div className="flex gap-3 min-w-max pt-2">
          {columns.map((col) => (
            <PipelineColumn
              key={col.stage}
              column={col}
              activeDragId={activeLeadId}
              highlightLeadId={highlightLeadId}
              onLeadDragStart={(id) => onDragStart?.(id)}
              onLeadMoveStage={onMoveStage}
            />
          ))}
        </div>
      </div>

      <DragOverlay dropAnimation={null}>
        {activeLead ? (
          <LeadCard lead={activeLead} className="rotate-2 shadow-xl opacity-90" />
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
