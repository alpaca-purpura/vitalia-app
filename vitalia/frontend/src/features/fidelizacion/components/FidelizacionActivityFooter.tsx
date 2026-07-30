// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * FidelizacionActivityFooter — sticky bottom activity stream.
 *
 * Shows anonymized recent fidelización events (NO PHI patient names).
 * Auto-refreshes every 30s via React Query refetchInterval.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { FIDELIZACION_COPY } from "../copy";
import { useActivityStream } from "../api/use-activity-stream";
import { formatTenantDate } from "@/lib/format/formatTenantDate";
import { useTenantLocale } from "@/hooks/useTenantLocale";

interface FidelizacionActivityFooterProps {
  className?: string;
}

/**
 * Sticky activity feed footer.
 * Events are anonymized at API level — no RequireRole needed here.
 */
export function FidelizacionActivityFooter({
  className,
}: FidelizacionActivityFooterProps) {
  const { data, isPending } = useActivityStream(10);
  const { timezone } = useTenantLocale();
  const copy = FIDELIZACION_COPY.activity;

  return (
    <footer
      aria-label={copy.streamTitle}
      className={cn(
        "border-t border-[hsl(var(--vitalia-border,220_13%_91%))] bg-white px-4 py-2",
        className,
      )}
    >
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-[hsl(var(--vitalia-muted,220_10%_55%))]">
        {copy.streamTitle}
      </p>
      {isPending ? (
        <div className="flex gap-3 overflow-x-auto">
          {Array.from({ length: 4 }).map((_, i) => (
            <div
              key={i}
              className="h-6 w-40 shrink-0 animate-pulse rounded bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))]"
            />
          ))}
        </div>
      ) : (
        <ul className="flex gap-4 overflow-x-auto text-xs text-[hsl(var(--vitalia-muted,220_10%_55%))]">
          {data?.events.map((event) => (
            <li key={event.id} className="shrink-0 whitespace-nowrap">
              <span className="font-medium text-[hsl(var(--vitalia-fg,220_25%_15%))]">
                {copy[event.eventType]}
              </span>{" "}
              — {formatTenantDate(event.occurredAt, timezone)}{" "}
              <span className="text-[hsl(var(--vitalia-muted,220_10%_55%))]">
                {event.descriptionAnonymized}
              </span>
            </li>
          ))}
          {data?.events.length === 0 && (
            <li className="text-[hsl(var(--vitalia-muted,220_10%_55%))]">
              Sin actividad reciente.
            </li>
          )}
        </ul>
      )}
    </footer>
  );
}
