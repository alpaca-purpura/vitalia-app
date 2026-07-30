// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * MaintenanceTab — maintenance re-engagement pattern list.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { FIDELIZACION_COPY } from "../../copy";
import { useReEngagementPatterns } from "../../api/use-re-engagement-patterns";
import {
  ReEngagementCard,
  type ReEngagementCardHandlers,
} from "../ReEngagementCard";
import type { FidelizacionPeriod, UrgencyFilter } from "../../types/url-state";
import type { UrgencyLevel } from "../../types/re-engagement";

interface MaintenanceTabProps extends ReEngagementCardHandlers {
  period: FidelizacionPeriod;
  vertical?: string | null;
  doctorId?: string | null;
  urgency?: UrgencyFilter[];
}

export function MaintenanceTab({
  period,
  vertical,
  doctorId,
  urgency,
  ...handlers
}: MaintenanceTabProps) {
  const { data, isPending, isError } = useReEngagementPatterns({
    pattern: "maintenance",
    period,
    vertical,
    doctorId,
    urgency: urgency as UrgencyLevel[] | undefined,
  });

  const rows = data?.rows ?? [];

  return (
    <section
      id="panel-maintenance"
      role="tabpanel"
      aria-labelledby="tab-maintenance"
      className="space-y-3 p-4"
    >
      {isPending && (
        <div aria-busy="true" className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="h-24 animate-pulse rounded-md bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))]"
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
      {!isPending && !isError && rows.length === 0 && (
        <div className="py-4 text-center text-sm text-[hsl(var(--vitalia-muted,220_10%_55%))]">
          {FIDELIZACION_COPY.empty.maintenance}
        </div>
      )}
      {!isPending &&
        !isError &&
        rows.length > 0 &&
        rows.map((row) => (
          <ReEngagementCard
            key={row.reEngagementEventId}
            row={row}
            {...handlers}
          />
        ))}
    </section>
  );
}
