// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadSummaryHeader — "lead-card dinámica" franja resumen (D.8).
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Renders below EntitySubNavBar in both Resumen and Historial views:
 * canal · procedimiento de interés · valor estimado · badge temperatura
 * score 0-100 · "última actividad hace X" · botón Tomar control.
 *
 * spec_anchor: 01-spec.md § V3 Cabecera del workspace (D.8)
 * downstream-regression-na: brand-local vitalia FE
 */

import { ChannelBadge } from "@/components/shared/shell-organism/ChannelBadge";
import { ScoreDonut } from "@/components/shared/score/ScoreDonut";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { LeadCardDTO } from "../../../types/embudo.types";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface LeadSummaryHeaderProps {
  lead: LeadCardDTO;
  onTakeControl?: () => void;
  className?: string;
}

// ── Temperature badge ─────────────────────────────────────────────────────────

const TEMP_META: Record<
  NonNullable<LeadCardDTO["temperature"]>,
  { emoji: string; label: string; class: string }
> = {
  hot: { emoji: "🔥", label: "Caliente", class: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300" },
  warm: { emoji: "🌡️", label: "Tibio", class: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300" },
  cold: { emoji: "❄️", label: "Frío", class: "bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300" },
};

// ── Time since helper ─────────────────────────────────────────────────────────

function timeSince(isoDate: string | null | undefined): string {
  if (!isoDate) return "—";
  const diff = Date.now() - new Date(isoDate).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `hace ${mins}m`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `hace ${hrs}h`;
  const days = Math.floor(hrs / 24);
  return `hace ${days}d`;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * LeadSummaryHeader — franja resumen siempre visible bajo EntitySubNavBar.
 *
 * Renders: canal · servicio · valor · temperatura · score · últ. actividad · Tomar control.
 * Empty-states: "Aún sin presupuesto", "Aún sin doctor" — shown, not hidden (spec V3).
 */
export function LeadSummaryHeader({
  lead,
  onTakeControl,
  className,
}: LeadSummaryHeaderProps) {
  const tempMeta = lead.temperature ? TEMP_META[lead.temperature] : null;

  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-2 border-b border-border/50 bg-muted/20",
        className,
      )}
      data-testid="lead-summary-header"
    >
      {/* Canal */}
      {lead.channel && (
        <ChannelBadge channel={lead.channel} />
      )}

      {/* Servicio de interés */}
      {lead.serviceInterest ? (
        <span className="text-sm text-muted-foreground">
          {lead.serviceInterest}
        </span>
      ) : (
        <span className="text-xs text-muted-foreground/60 italic">
          Aún sin servicio registrado
        </span>
      )}

      {/* Valor estimado */}
      {lead.estimatedValue !== null && lead.estimatedValue !== undefined ? (
        <span className="text-sm font-medium">
          {lead.currency ?? "?"} {lead.estimatedValue.toLocaleString()}
        </span>
      ) : (
        <span className="text-xs text-muted-foreground/60 italic">
          Aún sin presupuesto
        </span>
      )}

      {/* Temperatura badge */}
      {tempMeta && (
        <span
          className={cn(
            "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
            tempMeta.class,
          )}
          aria-label={`Temperatura: ${tempMeta.label}`}
        >
          <span aria-hidden="true">{tempMeta.emoji}</span>
          {tempMeta.label}
        </span>
      )}

      {/* Score donut */}
      {lead.score !== null && lead.score !== undefined && (
        <ScoreDonut score={lead.score} />
      )}

      {/* Última actividad */}
      {lead.lastActivityAt && (
        <span className="text-xs text-muted-foreground">
          Últ. actividad {timeSince(lead.lastActivityAt)}
        </span>
      )}

      {/* Spacer */}
      <div className="flex-1" />

      {/* Tomar control button */}
      {lead.operatedBy === "agent" && onTakeControl && (
        <Button
          size="sm"
          variant="outline"
          onClick={onTakeControl}
          className="shrink-0 text-xs"
          aria-label="Tomar control de este lead"
        >
          Tomar control
        </Button>
      )}

      {/* Human takeover badge */}
      {lead.operatedBy === "human" && (
        <Badge
          variant="secondary"
          className="text-xs bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
        >
          🙋 Tú tienes el control
        </Badge>
      )}
    </div>
  );
}
