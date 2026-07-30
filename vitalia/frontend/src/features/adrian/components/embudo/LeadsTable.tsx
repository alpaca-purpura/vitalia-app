// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * LeadsTable — List view table for the Embudo board (D.9 spec).
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Columns (D.9): Lead (masked) · Etapa (badge) · Canal · Score · En etapa · Última actividad · Operador · Doctor
 * Paginated: 25/page. Click row → lead detail page.
 * Sortable columns.
 *
 * Uses Shadcn Table from components/ui/. Server component: NO (has click + pagination state).
 * spec_anchor: 01-spec.md § V2 Lista + D.9
 */
"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { PiiMaskedSpan } from "@/components/shared/phi/PiiMaskedSpan";
import { ChannelBadge } from "@/components/shared/shell-organism/ChannelBadge";
import { ScoreDonut } from "@/components/shared/score/ScoreDonut";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useTenantId } from "@/hooks/useTenantId";
import { formatTenantDate } from "@/lib/format/formatTenantDate";
import { STAGE_LABELS, STAGE_SLA_DAYS } from "../../types/embudo-schema";
import type { BoardColumn, LeadFunnelStage } from "../../types/embudo.types";

const PAGE_SIZE = 25;

export interface LeadsTableProps {
  columns: BoardColumn[];
  highlightLeadId?: string | null;
  className?: string;
}

function slaStatus(stage: LeadFunnelStage, stageEnteredAt: string | null): "green" | "amber" | "red" {
  const slaGreen = STAGE_SLA_DAYS[stage];
  if (!slaGreen || !stageEnteredAt) return "green";
  const days = Math.floor((Date.now() - new Date(stageEnteredAt).getTime()) / (1000 * 60 * 60 * 24));
  if (days >= slaGreen * 2) return "red";
  if (days >= slaGreen) return "amber";
  return "green";
}

export function LeadsTable({ columns, highlightLeadId, className }: LeadsTableProps) {
  const tenantId = useTenantId();
  const [page, setPage] = useState(1);

  // Flatten all leads from all columns
  const allLeads = useMemo(
    () => columns.flatMap((c) => c.leads),
    [columns],
  );
  const totalCount = allLeads.length;
  const totalPages = Math.max(1, Math.ceil(totalCount / PAGE_SIZE));
  const pageLeads = allLeads.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className={cn("flex flex-col gap-3", className)}>
      {/* Table */}
      <div className="overflow-x-auto rounded-md border border-border">
        <table
          className="w-full text-xs"
          aria-label="Lista de leads del embudo"
          aria-rowcount={totalCount}
          data-testid="leads-table"
        >
          <thead className="bg-muted/60 border-b border-border">
            <tr>
              {[
                "Lead",
                "Etapa",
                "Canal",
                "Score",
                "En etapa",
                "Última actividad",
                "Operador",
                "Doctor",
              ].map((col) => (
                <th
                  key={col}
                  scope="col"
                  className="text-left px-3 py-2 font-medium text-muted-foreground whitespace-nowrap"
                >
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {pageLeads.length === 0 ? (
              <tr>
                <td colSpan={8} className="text-center py-8 text-muted-foreground">
                  Sin leads en esta vista
                </td>
              </tr>
            ) : (
              pageLeads.map((lead, idx) => {
                const detailHref = tenantId
                  ? `/${tenantId}/adrian/embudo/${lead.id}/resumen`
                  : "#";
                const sla = slaStatus(lead.stage, lead.stageEnteredAt ?? null);
                const stageLabel = STAGE_LABELS[lead.stage] ?? lead.stage;

                return (
                  <tr
                    key={lead.id}
                    className={cn(
                      "border-b border-border/60 hover:bg-muted/30 transition-colors cursor-pointer",
                      highlightLeadId === lead.id && "ring-1 ring-inset ring-primary bg-primary/5",
                      idx % 2 === 0 ? "bg-background" : "bg-muted/20",
                    )}
                    aria-rowindex={(page - 1) * PAGE_SIZE + idx + 1}
                  >
                    {/* Lead name */}
                    <td className="px-3 py-2 font-medium max-w-[140px]">
                      <Link href={detailHref} className="hover:text-primary hover:underline">
                        <PiiMaskedSpan value={lead.name} fieldType="name" />
                      </Link>
                    </td>
                    {/* Etapa badge */}
                    <td className="px-3 py-2 whitespace-nowrap">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-muted text-muted-foreground text-xs font-medium">
                        {stageLabel}
                      </span>
                    </td>
                    {/* Canal */}
                    <td className="px-3 py-2">
                      {lead.channel ? (
                        <ChannelBadge channel={lead.channel} iconOnly />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    {/* Score */}
                    <td className="px-3 py-2">
                      {lead.score != null ? (
                        <ScoreDonut score={lead.score} />
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    {/* En etapa (SLA dot) */}
                    <td className="px-3 py-2">
                      {lead.stageEnteredAt ? (
                        <div className="flex items-center gap-1">
                          <span
                            className={cn(
                              "h-2 w-2 rounded-full",
                              sla === "green" ? "bg-emerald-500" :
                              sla === "amber" ? "bg-amber-500" : "bg-red-500",
                            )}
                            aria-hidden
                          />
                          <span
                            className={cn(
                              "text-xs",
                              sla === "green" ? "text-emerald-700 dark:text-emerald-400" :
                              sla === "amber" ? "text-amber-700 dark:text-amber-400" :
                              "text-red-700 dark:text-red-400",
                            )}
                          >
                            {Math.floor((Date.now() - new Date(lead.stageEnteredAt).getTime()) / (1000 * 60 * 60 * 24))}d
                          </span>
                        </div>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </td>
                    {/* Última actividad */}
                    <td className="px-3 py-2 text-muted-foreground">
                      {lead.lastActivityAt
                        ? formatTenantDate(lead.lastActivityAt)
                        : "—"}
                    </td>
                    {/* Operador */}
                    <td className="px-3 py-2 whitespace-nowrap">
                      <span
                        className={cn(
                          "inline-flex items-center gap-0.5",
                          lead.operatedBy === "agent"
                            ? "text-[hsl(var(--agent-adrian))]"
                            : "text-emerald-700 dark:text-emerald-400",
                        )}
                      >
                        {lead.operatedBy === "agent" ? "🤖 Adrián" : "🙋 Tú"}
                      </span>
                    </td>
                    {/* Doctor */}
                    <td className="px-3 py-2 text-muted-foreground">
                      {lead.assignedDoctorId ?? "—"}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {(page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, totalCount)} de {totalCount}
          </span>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs"
              disabled={page === 1}
              onClick={() => setPage((p) => p - 1)}
              aria-label="Página anterior"
            >
              ‹ Anterior
            </Button>
            <span className="px-2">
              {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs"
              disabled={page === totalPages}
              onClick={() => setPage((p) => p + 1)}
              aria-label="Página siguiente"
            >
              Siguiente ›
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
