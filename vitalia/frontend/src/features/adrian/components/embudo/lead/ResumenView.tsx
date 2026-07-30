// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * ResumenView — Resumen tab content for lead workspace (V3 spec).
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Three blocks (spec D.8):
 *   1. Datos del lead (nombre · teléfono · correo · canal · interés · valor · doctor · etapa)
 *   2. Estado del agente / autonomía (🤖 Adrián la atiende · Tomar control · instrucción oculta · Nudge · Mover de etapa)
 *   3. Score glass-box (score + temperatura + barra + breakdown)
 *
 * "Empty-states honestos" — missing data shown as placeholder, not hidden.
 * RN-2 firewall: NO clinical data rendered here.
 *
 * U1/U2 fix (2026-06-04): Nombre shown as plain text (non_phi marketing lead,
 * vendor needs to distinguish the lead). Phone + email added (non_phi marketing;
 * PHI masking applies only when lead converts to patient — different surface).
 * LeadDetailResponse.lead now typed as LeadDetailLeadDTO (mirrors LeadResponse).
 *
 * spec_anchor: 01-spec.md § V3 Vista Resumen + 03-arch-fe.md § ResumenView
 * downstream-regression-na: brand-local vitalia FE
 */
"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ChannelBadge } from "@/components/shared/shell-organism/ChannelBadge";
import { useLeadDetail } from "../../../api/lead";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { STAGE_LABELS } from "../../../types/embudo-schema";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ResumenViewProps {
  leadId: string;
  tenantId: string;
}

// ── Loading skeleton ──────────────────────────────────────────────────────────

function ResumenSkeleton() {
  return (
    <div className="flex flex-col gap-4 p-4" aria-busy="true">
      <Skeleton className="h-5 w-32" />
      {[1, 2, 3, 4, 5, 6].map((i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-4 w-24 shrink-0" />
          <Skeleton className="h-4 flex-1" />
        </div>
      ))}
      <Skeleton className="h-px w-full mt-2" />
      <Skeleton className="h-5 w-40" />
      <Skeleton className="h-16 w-full" />
      <Skeleton className="h-px w-full mt-2" />
      <Skeleton className="h-5 w-28" />
      <Skeleton className="h-24 w-full" />
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * ResumenView — three-block layout for lead detail Resumen tab.
 *
 * Renders: Datos · Estado agente · Score glass-box.
 * All empty states shown honestly ("Aún sin doctor asignado", etc.).
 * RN-2 firewall: server-side filters out clinical data.
 */
export function ResumenView({ leadId, tenantId: _tenantId }: ResumenViewProps) {
  const { data, isLoading, isError } = useLeadDetail(leadId);

  if (isLoading) return <ResumenSkeleton />;

  if (isError || !data) {
    return (
      <div className="p-4 text-sm text-muted-foreground" role="alert">
        No se pudo cargar el resumen del lead. Intenta recargar la página.
      </div>
    );
  }

  const { lead, scoreBreakdown, autonomy } = data;

  return (
    <div className="flex flex-col gap-6 p-4 max-w-2xl" data-testid="resumen-view">

      {/* ── Bloque 1: Datos del lead ─────────────────────────────────────── */}
      <section aria-labelledby="bloque-datos">
        <h2 id="bloque-datos" className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Datos del lead
        </h2>
        <dl className="flex flex-col gap-2 text-sm">
          {/* Nombre — plain text, non_phi marketing lead */}
          <div className="flex items-center gap-2">
            <dt className="w-32 shrink-0 text-muted-foreground">Nombre</dt>
            <dd data-testid="lead-name">{lead.name}</dd>
          </div>

          {/* Teléfono — plain text, non_phi marketing */}
          <div className="flex items-center gap-2">
            <dt className="w-32 shrink-0 text-muted-foreground">Teléfono</dt>
            <dd data-testid="lead-phone">
              {lead.phone ?? (
                <span className="text-muted-foreground/60 italic text-xs">Sin teléfono registrado</span>
              )}
            </dd>
          </div>

          {/* Correo — plain text, non_phi marketing */}
          <div className="flex items-center gap-2">
            <dt className="w-32 shrink-0 text-muted-foreground">Correo</dt>
            <dd data-testid="lead-email">
              {lead.email ?? (
                <span className="text-muted-foreground/60 italic text-xs">Sin correo registrado</span>
              )}
            </dd>
          </div>

          {/* Canal origen */}
          <div className="flex items-center gap-2">
            <dt className="w-32 shrink-0 text-muted-foreground">Canal origen</dt>
            <dd>
              {lead.channel ? (
                <ChannelBadge channel={lead.channel} />
              ) : (
                <span className="text-muted-foreground/60 italic text-xs">Sin canal registrado</span>
              )}
            </dd>
          </div>

          {/* Servicio de interés */}
          <div className="flex items-center gap-2">
            <dt className="w-32 shrink-0 text-muted-foreground">Interés</dt>
            <dd>
              {lead.serviceInterest ?? (
                <span className="text-muted-foreground/60 italic text-xs">Aún sin servicio de interés</span>
              )}
            </dd>
          </div>

          {/* Valor estimado */}
          <div className="flex items-center gap-2">
            <dt className="w-32 shrink-0 text-muted-foreground">Valor estimado</dt>
            <dd>
              {lead.estimatedValue !== null && lead.estimatedValue !== undefined ? (
                <span className="font-medium">
                  {lead.currency ?? "?"} {lead.estimatedValue.toLocaleString()}
                </span>
              ) : (
                <span className="text-muted-foreground/60 italic text-xs">Aún sin presupuesto presentado</span>
              )}
            </dd>
          </div>

          {/* Etapa actual */}
          <div className="flex items-center gap-2">
            <dt className="w-32 shrink-0 text-muted-foreground">Etapa</dt>
            <dd>
              <Badge variant="secondary" className="text-xs">
                {STAGE_LABELS[lead.stage] ?? lead.stage}
              </Badge>
            </dd>
          </div>

          {/* Doctor asignado */}
          <div className="flex items-center gap-2">
            <dt className="w-32 shrink-0 text-muted-foreground">Doctor</dt>
            <dd>
              {lead.assignedDoctorId ? (
                <span>{lead.assignedDoctorId}</span>
              ) : (
                <span className="text-muted-foreground/60 italic text-xs">Aún sin doctor asignado</span>
              )}
            </dd>
          </div>
        </dl>
      </section>

      <hr className="border-border/50" />

      {/* ── Bloque 2: Estado del agente ──────────────────────────────────── */}
      <section aria-labelledby="bloque-agente">
        <h2 id="bloque-agente" className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Estado del agente
        </h2>

        {lead.operatedBy === "agent" ? (
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-2">
              <span
                className="inline-flex items-center gap-1.5 text-sm font-medium"
                style={{ color: "var(--agent-adrian)" }}
              >
                <span aria-hidden="true">🤖</span>
                Adrián la atiende
              </span>
            </div>

            {/* Autonomy line */}
            {autonomy && (
              <div className="text-xs text-muted-foreground bg-muted/30 rounded-md p-2 flex flex-col gap-1">
                <span>
                  <strong>Puede:</strong>{" "}
                  {(autonomy.can ?? []).join(" · ")}
                </span>
                <span>
                  <strong>Necesita tu OK:</strong>{" "}
                  {(autonomy.needsOk ?? []).join(" · ")}
                </span>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <Badge
              variant="secondary"
              className="text-xs bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300"
            >
              🙋 Tú tienes el control
            </Badge>
            <Button
              size="sm"
              variant="ghost"
              className="text-xs text-muted-foreground"
            >
              Devolver a Adrián
            </Button>
          </div>
        )}
      </section>

      <hr className="border-border/50" />

      {/* ── Bloque 3: Score glass-box ────────────────────────────────────── */}
      <section aria-labelledby="bloque-score">
        <h2 id="bloque-score" className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-3">
          Puntuación del lead
        </h2>
        <ScoreBreakdown score={lead.score} factors={scoreBreakdown} />
      </section>
    </div>
  );
}
