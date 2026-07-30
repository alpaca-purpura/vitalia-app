// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * HistorialView — Historial tab content for lead workspace (V3 spec).
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Timeline chronológica: mensajes (WA/IG) · transiciones de etapa · acciones
 * del agente · eventos (presupuesto, depósito). Todo atribuido.
 *
 * RN-2 FIREWALL: NO clinical data. Server-side filters it out.
 * The timeline contains only commercial activities (stage moves, messages, deposits).
 * Link to Inbox (PHI-gated) for the actual conversation.
 *
 * spec_anchor: 01-spec.md § V3 Vista Historial (D.8) + RN-2
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { useLeadTimeline } from "../../../api/lead";
import type { TimelineEntry } from "../../../types/embudo.types";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface HistorialViewProps {
  leadId: string;
  tenantId: string;
  /** Link to Inbox conversation (PHI-gated — shown as external link, not inline) */
  inboxHref?: string;
}

// ── Entry icon map ────────────────────────────────────────────────────────────

const KIND_ICON: Record<TimelineEntry["kind"], string> = {
  stage_move: "➡️",
  message: "💬",
  info_sent: "📋",
  deposit: "💳",
  note: "📝",
  freeze: "🧊",
  reactivation: "↻",
};

const ACTOR_ICON: Record<TimelineEntry["actor"], string> = {
  agent: "🤖",
  human: "🙋",
  lead: "👤",
  system: "⚙️",
};

// ── Loading skeleton ──────────────────────────────────────────────────────────

function HistorialSkeleton() {
  return (
    <div className="flex flex-col gap-3 p-4" aria-busy="true">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="flex gap-3">
          <Skeleton className="h-8 w-8 rounded-full shrink-0" />
          <div className="flex-1 flex flex-col gap-1">
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Single timeline entry ─────────────────────────────────────────────────────

function TimelineItem({ entry }: { entry: TimelineEntry }) {
  const kindIcon = KIND_ICON[entry.kind] ?? "•";
  const actorIcon = ACTOR_ICON[entry.actor] ?? "•";

  return (
    <li
      className="flex gap-3 group"
      data-testid={`timeline-entry-${entry.id}`}
    >
      {/* Icon column */}
      <div className="flex flex-col items-center">
        <div
          className={cn(
            "w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0",
            "bg-muted/50 border border-border/50",
          )}
          aria-hidden="true"
        >
          {kindIcon}
        </div>
        {/* Vertical line */}
        <div className="w-px flex-1 bg-border/30 mt-1 mb-0 group-last:hidden" />
      </div>

      {/* Content column */}
      <div className="flex-1 pb-4">
        <div className="flex items-baseline gap-2 flex-wrap">
          <span className="text-sm">{entry.descriptionEs}</span>
          <span
            className="text-xs text-muted-foreground/60"
            aria-label={`Actor: ${entry.actor}`}
          >
            {actorIcon}
          </span>
        </div>
        <time
          className="text-xs text-muted-foreground"
          dateTime={entry.occurredAt}
        >
          {new Date(entry.occurredAt).toLocaleString("es-419", {
            year: "numeric",
            month: "short",
            day: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </time>
      </div>
    </li>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * HistorialView — chronological timeline of commercial activities.
 *
 * Grows turn-by-turn as Adrián/human act on the lead.
 * Does NOT show clinical data (RN-2 firewall — server-side filtered).
 * Links to Inbox for the full conversation.
 */
export function HistorialView({
  leadId,
  tenantId: _tenantId,
  inboxHref,
}: HistorialViewProps) {
  const { data, isLoading, isError } = useLeadTimeline(leadId);

  if (isLoading) return <HistorialSkeleton />;

  if (isError || !data) {
    return (
      <div className="p-4 text-sm text-muted-foreground" role="alert">
        No se pudo cargar el historial. Intenta recargar la página.
      </div>
    );
  }

  const events = data.events;

  return (
    <div
      className="flex flex-col gap-0 p-4 max-w-2xl"
      data-testid="historial-view"
    >
      {/* Inbox link — PHI-gated (RN-2) */}
      {inboxHref && (
        <div className="mb-4">
          <a
            href={inboxHref}
            className="text-sm text-primary hover:underline inline-flex items-center gap-1"
            aria-label="Abrir conversación completa en el Inbox"
          >
            Abrir conversación en el Inbox →
          </a>
          <p className="text-xs text-muted-foreground mt-0.5">
            El historial muestra actividades comerciales. Los datos clínicos
            están en el expediente del paciente.
          </p>
        </div>
      )}

      {/* Timeline */}
      {events.length === 0 ? (
        <div
          className="text-sm text-muted-foreground/60 italic py-8 text-center"
          data-testid="historial-empty"
        >
          Aún sin actividad registrada en este lead.
        </div>
      ) : (
        <ol
          className="flex flex-col gap-0"
          aria-label="Historial de actividades del lead"
        >
          {events.map((entry) => (
            <TimelineItem key={entry.id} entry={entry} />
          ))}
        </ol>
      )}
    </div>
  );
}
