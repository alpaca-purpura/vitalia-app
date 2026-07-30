// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * AdrianEmbudoView — Client root for Adrián Embudo board (ADR-vitalia-004 § 3.3).
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Client root: "use client" L1. Receives initialBoard from Server Component page.tsx.
 * Manages:
 *   - View toggle (kanban/lista) — URL-synced via ?view=
 *   - Sort + filters — URL-synced + Zustand ephemeral
 *   - Drag-drop override flow (OverrideReasonDialog)
 *   - Optimistic updates on stage mutation
 *   - Highlight post-create lead from ?highlight= param
 *
 * Empty state, loading state, error state all handled here.
 *
 * spec_anchor: 01-spec.md § V1/V2 + D.2/D.3/D.4/D.9/D.12/D.13
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { useEffect, useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { EmptyState } from "@/components/shared/shell-organism/EmptyState";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useEmbudoBoard } from "../../api/embudo-board";
import { useLeadStageMutation } from "../../api/lead-stage-mutation";
import { useEmbudoUiStore } from "../../store/embudo-ui-store";
import { EmbudoHeader } from "./EmbudoHeader";
import { EmbudoMetrics } from "./EmbudoMetrics";
import { EmbudoFilters } from "./EmbudoFilters";
import { KanbanBoard } from "./KanbanBoard";
import { LeadsTable } from "./LeadsTable";
import { OverrideReasonDialog } from "./OverrideReasonDialog";
import { isAdjacentTransition, STAGE_ALLOWED_NEXT, BOARD_HOT_STAGES } from "../../types/embudo-schema";
import type {
  BoardResponse,
  BoardFilters,
  LeadCardDTO,
  LeadFunnelStage,
} from "../../types/embudo.types";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AdrianEmbudoViewProps {
  initialBoard?: BoardResponse | null;
  tenantId: string;
}

// ── Loading skeleton ──────────────────────────────────────────────────────────

function BoardSkeleton() {
  return (
    <div className="flex gap-3 overflow-x-auto pb-2 pt-2" aria-busy="true" aria-label="Cargando tablero" data-testid="embudo-skeleton">
      {[1, 2, 3, 4, 5].map((i) => (
        <div key={i} className="flex flex-col gap-2 min-w-[180px]">
          <Skeleton className="h-8 w-full rounded-md" />
          {[1, 2, 3].map((j) => (
            <Skeleton key={j} className="h-24 w-full rounded-md" />
          ))}
        </div>
      ))}
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

export function AdrianEmbudoView({ initialBoard, tenantId }: AdrianEmbudoViewProps) {
  const router = useRouter();
  const searchParams = useSearchParams();

  // URL-derived state
  const viewParam = (searchParams.get("view") as "kanban" | "lista") ?? "kanban";
  const highlightParam = searchParams.get("highlight");

  // Zustand UI state
  const {
    view, sort, filters, activeDragId, pendingOverride,
    setView, setSort, setFilters, setActiveDragId,
    setPendingOverride, setHighlightLeadId, highlightLeadId, clearDragState,
  } = useEmbudoUiStore();

  // Sync view from URL on mount
  useEffect(() => {
    if (viewParam !== view) setView(viewParam);
  }, [viewParam, setView]); // viewParam is the only meaningful dep (setView is stable)

  // Set highlight from URL param
  useEffect(() => {
    if (highlightParam) {
      setHighlightLeadId(highlightParam);
      // Clear after 3s (ring+pulse)
      const t = setTimeout(() => setHighlightLeadId(null), 3000);
      return () => clearTimeout(t);
    }
  }, [highlightParam, setHighlightLeadId]);

  const boardFilters: BoardFilters = useMemo(() => ({
    view,
    sort,
    ...filters,
  }), [view, sort, filters]);

  // React Query: board data
  const { data: boardData, isLoading, isError, refetch } = useEmbudoBoard(boardFilters);

  // Use SSR initial data until RQ loads
  const displayData = boardData ?? initialBoard ?? null;

  // Mutation: stage transition
  const stageMutation = useLeadStageMutation(boardFilters);

  // ── View toggle ─────────────────────────────────────────────────────────────

  const handleViewChange = useCallback(
    (v: "kanban" | "lista") => {
      setView(v);
      const sp = new URLSearchParams(searchParams.toString());
      sp.set("view", v);
      router.replace(`?${sp.toString()}`, { scroll: false });
    },
    [router, searchParams, setView],
  );

  // ── Drag handling ───────────────────────────────────────────────────────────

  const handleStageDrop = useCallback(
    (leadId: string, lead: LeadCardDTO, fromStage: LeadFunnelStage, toStage: LeadFunnelStage) => {
      if (isAdjacentTransition(fromStage, toStage)) {
        // Adjacent → direct transition (no dialog)
        stageMutation.mutate(
          { leadId, toStage, version: lead.version, triggeredBy: "manual_override" },
          {
            onSuccess: () => {
              toast.success(`Lead movido a ${toStage.replace(/_/g, " ")}`);
            },
            onError: (err) => {
              const apiErr = err as { status?: number; body?: { allowed_next?: string[] } };
              if (apiErr.status === 409) {
                toast.error("Este lead fue actualizado por otra persona.", {
                  description: "La vista se actualizó.",
                });
              } else if (apiErr.status === 422) {
                const allowed = apiErr.body?.allowed_next?.join(", ") ?? "";
                toast.error(`Etapa no permitida. Opciones: ${allowed}`);
              } else {
                toast.error("No se pudo mover el lead. Intenta de nuevo.");
              }
            },
          },
        );
        clearDragState();
      } else {
        // Non-adjacent → open OverrideReasonDialog
        setPendingOverride({
          leadId,
          fromStage,
          toStage,
          leadVersion: lead.version,
        });
      }
    },
    [stageMutation, clearDragState, setPendingOverride],
  );

  const handleOverrideConfirm = useCallback(
    ({ reason, toStage }: { reason: string; toStage: LeadFunnelStage }) => {
      if (!pendingOverride) return;

      stageMutation.mutate(
        {
          leadId: pendingOverride.leadId,
          toStage,
          reason,
          version: pendingOverride.leadVersion,
          triggeredBy: "manual_override",
        },
        {
          onSuccess: () => {
            toast.success("Adrián tomó nota y ajusta su próximo paso.", {
              description: "El movimiento quedó registrado en el Historial.",
            });
            setPendingOverride(null);
          },
          onError: (err) => {
            const apiErr = err as { status?: number };
            if (apiErr.status === 409) {
              toast.error("Este lead fue actualizado por otra persona.");
            } else {
              toast.error("No se pudo mover el lead. Intenta de nuevo.");
            }
            setPendingOverride(null);
          },
        },
      );
    },
    [pendingOverride, stageMutation, setPendingOverride],
  );

  const handleOverrideCancel = useCallback(() => {
    setPendingOverride(null);
    clearDragState();
  }, [setPendingOverride, clearDragState]);

  /**
   * handleMoveStage — non-drag path for stage transition (button on card).
   * Moves lead to next adjacent forward stage.
   * Used by E2E Playwright (data-testid="move-stage-{leadId}") and keyboard users (SC-10 a11y).
   */
  const handleMoveStage = useCallback(
    (leadId: string) => {
      if (!displayData) return;
      for (const col of displayData.columns) {
        const lead = col.leads.find((l) => l.id === leadId);
        if (!lead) continue;
        const fromStage = lead.stage;
        // Pick first allowed-next forward stage (adjacent, not reservado via button)
        const forwardStages = (STAGE_ALLOWED_NEXT[fromStage] ?? []).filter(
          (s) => s !== "decidio_no" && s !== "reservado" && BOARD_HOT_STAGES.includes(s),
        );
        const nextStage = forwardStages[0];
        if (!nextStage) return; // no forward move available (terminal stage)
        handleStageDrop(leadId, lead, fromStage, nextStage);
        return;
      }
    },
    [displayData, handleStageDrop],
  );

  // ── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="flex flex-col gap-4 p-4 min-h-0" data-testid="adrian-embudo-view">
      {/* Header (title + chip + toggles + CTA) */}
      <EmbudoHeader
        tenantId={tenantId}
        view={view}
        sort={sort ?? "stage_age_desc"}
        operatorFilter={(boardFilters.operatedBy as "agent" | "todos") ?? "agent"}
        onViewChange={handleViewChange}
        onSortChange={setSort}
        onOperatorFilterChange={(v) => setFilters({ ...filters, operatedBy: v === "todos" ? null : v })}
      />

      {/* KPI strip */}
      {displayData?.kpis && (
        <EmbudoMetrics kpis={displayData.kpis} tenantId={tenantId} />
      )}

      {/* Active filters */}
      <EmbudoFilters filters={filters} onChange={setFilters} />

      {/* Board content */}
      {isLoading && !displayData ? (
        <BoardSkeleton />
      ) : isError ? (
        <div
          role="alert"
          className="flex flex-col items-center gap-3 py-12 text-center"
        >
          <p className="text-muted-foreground">
            No se pudo cargar el embudo. Verifica tu conexión.
          </p>
          <Button variant="outline" size="sm" onClick={() => refetch()} data-testid="retry-button">
            Reintentar
          </Button>
        </div>
      ) : !displayData || displayData.columns.every((c) => c.count === 0) ? (
        <div data-testid="embudo-empty-state">
          <EmptyState
            icon="🎯"
            title="Sin leads en el embudo"
            description="Crea el primer lead para empezar a usar el embudo de Adrián."
            ctaLabel="+ Crear primer lead"
            onCtaClick={() => {
              window.location.href = `/${tenantId}/adrian/embudo/nuevo`;
            }}
          />
        </div>
      ) : view === "kanban" ? (
        <KanbanBoard
          columns={displayData.columns}
          activeLeadId={activeDragId}
          highlightLeadId={highlightLeadId}
          onStageDrop={handleStageDrop}
          onMoveStage={handleMoveStage}
          onDragStart={setActiveDragId}
          onDragCancel={clearDragState}
        />
      ) : (
        <LeadsTable
          columns={displayData.columns}
          highlightLeadId={highlightLeadId}
        />
      )}

      {/* Override reason dialog */}
      {pendingOverride && (
        <OverrideReasonDialog
          open={!!pendingOverride}
          fromStage={pendingOverride.fromStage}
          toStage={pendingOverride.toStage}
          onConfirm={handleOverrideConfirm}
          onCancel={handleOverrideCancel}
          isLoading={stageMutation.isPending}
        />
      )}
    </div>
  );
}
