// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * NPSResumenTab — NPS reduced table tab.
 *
 * Shows NPS summary + compact row list.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { FIDELIZACION_COPY } from "../../copy";
import { useNpsResponses } from "../../api/use-nps-responses";
import { NPSRowCompact } from "../NPSRowCompact";
import type { FidelizacionPeriod } from "../../types/url-state";

interface NPSResumenTabProps {
  period: FidelizacionPeriod;
}

export function NPSResumenTab({ period }: NPSResumenTabProps) {
  const { data, isPending, isError } = useNpsResponses(period);

  return (
    <section
      id="panel-nps"
      role="tabpanel"
      aria-labelledby="tab-nps"
      className="p-4"
    >
      {isPending && (
        <div aria-busy="true" className="space-y-2">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-12 animate-pulse rounded bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))]"
            />
          ))}
        </div>
      )}
      {isError && (
        <div
          role="alert"
          className="text-sm text-[hsl(var(--vitalia-danger,0_75%_45%))]"
        >
          {FIDELIZACION_COPY.errors.generic}
        </div>
      )}
      {!isPending && !isError && (!data || data.rows.length === 0) && (
        <div className="py-4 text-center text-sm text-[hsl(var(--vitalia-muted,220_10%_55%))]">
          {FIDELIZACION_COPY.empty.nps}
        </div>
      )}
      {!isPending && !isError && data && data.rows.length > 0 && (
        <>
          {/* NPS summary header */}
          <div className="mb-4 flex gap-4 rounded-lg border border-[hsl(var(--vitalia-border,220_13%_91%))] bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))] p-3">
            <div className="text-center">
              <p className="text-2xl font-semibold text-[hsl(var(--vitalia-fg,220_25%_15%))]">
                {data.averageScore.toFixed(1)}
              </p>
              <p className="text-xs text-[hsl(var(--vitalia-muted,220_10%_55%))]">
                {FIDELIZACION_COPY.kpis.npsAverage.label}
              </p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-semibold text-[hsl(var(--vitalia-fg,220_25%_15%))]">
                {data.totalResponses}
              </p>
              <p className="text-xs text-[hsl(var(--vitalia-muted,220_10%_55%))]">
                Respuestas
              </p>
            </div>
          </div>

          {/* Rows */}
          <ul aria-label="Respuestas de NPS">
            {data.rows.map((row) => (
              <NPSRowCompact key={row.id} row={row} />
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
