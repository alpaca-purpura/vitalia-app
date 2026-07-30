// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * FrozenLeadRow — single frozen lead row in the Recuperar view (D.11).
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Shows: nombre masked · etapa donde se enfrió · frozen_reason ·
 * antigüedad · Diagnose (AI) · Reactivar.
 *
 * spec_anchor: 01-spec.md § V4 + 03-arch-fe.md § FrozenLeadRow D.11
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { useState } from "react";
import { toast } from "sonner";
import { ChannelBadge } from "@/components/shared/shell-organism/ChannelBadge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { useDiagnose } from "../../api/diagnose";
import { useReactivateLead } from "../../api/frozen";
import { STAGE_LABELS } from "../../types/embudo-schema";
import type { FrozenLeadDTO, DiagnoseResponse } from "../../types/embudo.types";

// ── Frozen reason labels ──────────────────────────────────────────────────────

const FROZEN_REASON_LABEL: Partial<Record<string, string>> = {
  inactividad_lead: "Inactividad del lead",
  sin_respuesta_presupuesto: "Sin respuesta al presupuesto",
  agente_trabado: "Adrián se trabó",
};

// ── Types ─────────────────────────────────────────────────────────────────────

export interface FrozenLeadRowProps {
  lead: FrozenLeadDTO;
  /** "recien" = recently frozen | "decidio_no" = decided no */
  segment: "recien" | "decidio_no";
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * FrozenLeadRow — displays a frozen lead with Diagnose + Reactivar actions.
 *
 * AI Diagnose: POST /crm/leads/{id}/diagnose → shows recommendation inline.
 * Reactivar: POST /crm/leads/{id}/reactivate → returns lead to board.
 */
export function FrozenLeadRow({ lead, segment, className }: FrozenLeadRowProps) {
  const [diagnosis, setDiagnosis] = useState<DiagnoseResponse | null>(null);
  const { mutateAsync: diagnose, isPending: isDiagnosing } = useDiagnose();
  const { mutateAsync: reactivate, isPending: isReactivating } =
    useReactivateLead();

  const handleDiagnose = async () => {
    try {
      const result = await diagnose(lead.id);
      setDiagnosis(result);
    } catch {
      toast.error("No se pudo obtener el diagnóstico. Intenta nuevamente.");
    }
  };

  const handleReactivate = async () => {
    try {
      await reactivate(lead.id);
      toast.success("Lead reactivado. Volvió al tablero en su última etapa.");
    } catch {
      toast.error("No se pudo reactivar el lead. Intenta nuevamente.");
    }
  };

  const frozenReasonLabel = lead.frozenReason
    ? (FROZEN_REASON_LABEL[lead.frozenReason] ?? lead.frozenReason)
    : null;

  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-lg border border-border/60 p-3 bg-card",
        className,
      )}
      data-testid={`frozen-lead-row-${lead.id}`}
    >
      {/* Header row */}
      <div className="flex items-start gap-3 flex-wrap">
        {/* Name + stage */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium">{lead.name}</span>
            <Badge variant="secondary" className="text-xs">
              {STAGE_LABELS[lead.lastStage] ?? lead.lastStage}
            </Badge>
            {lead.channel && <ChannelBadge channel={lead.channel} iconOnly />}
          </div>

          {/* Frozen reason */}
          {frozenReasonLabel && (
            <p className="text-xs text-muted-foreground mt-0.5">
              🧊 {frozenReasonLabel}
            </p>
          )}

          {/* Closure reason (decidio_no segment) */}
          {segment === "decidio_no" && lead.closureReason && (
            <p className="text-xs text-muted-foreground mt-0.5">
              Razón: {lead.closureReason}
            </p>
          )}

          {/* Camila cohorte badge (decidio_no) */}
          {segment === "decidio_no" && lead.reactivationCohortAt && (
            <p className="text-xs text-muted-foreground/70 mt-0.5">
              ↻ Camila reactiva{" "}
              {new Date(lead.reactivationCohortAt).toLocaleDateString("es-419", {
                month: "short",
                day: "numeric",
              })}
            </p>
          )}
        </div>

        {/* Frozen at */}
        {lead.frozenAt && (
          <time
            className="text-xs text-muted-foreground shrink-0"
            dateTime={lead.frozenAt}
          >
            {new Date(lead.frozenAt).toLocaleDateString("es-419", {
              month: "short",
              day: "numeric",
            })}
          </time>
        )}
      </div>

      {/* AI Diagnosis result */}
      {diagnosis && (
        <>
          <Separator />
          <div
            className="text-sm bg-muted/40 rounded-md p-2 flex flex-col gap-1"
            role="status"
            aria-label="Diagnóstico de Adrián"
          >
            <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
              🤖 Adrián sugiere
            </span>
            <p>{diagnosis.recommendation}</p>
            {diagnosis.suggestedAction && (
              <p className="text-xs text-muted-foreground">
                Acción: {diagnosis.suggestedAction}
              </p>
            )}
          </div>
        </>
      )}

      {/* Actions */}
      <div className="flex items-center gap-2 flex-wrap">
        {segment === "recien" && !diagnosis && (
          <Button
            size="sm"
            variant="outline"
            onClick={handleDiagnose}
            disabled={isDiagnosing}
            aria-busy={isDiagnosing}
            className="text-xs"
          >
            {isDiagnosing ? "Diagnosticando…" : "AI Diagnose"}
          </Button>
        )}

        <Button
          size="sm"
          variant="default"
          onClick={handleReactivate}
          disabled={isReactivating}
          aria-busy={isReactivating}
          className="text-xs"
        >
          {isReactivating ? "Reactivando…" : "Reactivar"}
        </Button>
      </div>
    </div>
  );
}
