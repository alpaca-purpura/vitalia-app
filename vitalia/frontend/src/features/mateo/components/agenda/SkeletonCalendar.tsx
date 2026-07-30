// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
/**
 * SkeletonCalendar.tsx — Loading skeleton placeholder for calendar views.
 * T-13 vitalia-fase2-valeria-agenda · F2-S1
 *
 * Shown while agenda data is loading (isLoading=true).
 * Renders a skeleton grid that approximates the WeekCalendar layout.
 *
 * Spanish neutro LatAm — sin voseo.
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.5 + 06-tickets.yaml T-13
 */

import { cn } from "@/lib/cn";
import { Skeleton } from "@/components/ui/skeleton";

// ── Props ─────────────────────────────────────────────────────────────────────

export interface SkeletonCalendarProps {
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Loading skeleton for calendar views.
 *
 * Mimics WeekCalendar layout (7 columns, 3 slots each) while data loads.
 * Uses aria-busy + sr-only text for accessibility.
 */
export function SkeletonCalendar({ className }: SkeletonCalendarProps) {
  return (
    <div
      className={cn("w-full overflow-hidden rounded-lg border bg-card", className)}
      data-testid="skeleton-calendar"
      aria-busy="true"
      aria-label="Cargando agenda…"
      role="status"
    >
      <span className="sr-only">Cargando agenda…</span>

      {/* Day header row */}
      <div className="grid grid-cols-7 border-b">
        {Array.from({ length: 7 }, (_, i) => (
          <div key={i} className="flex flex-col items-center gap-1 px-2 py-3 border-r last:border-r-0">
            <Skeleton className="h-3 w-8 rounded" />
            <Skeleton className="h-5 w-6 rounded" />
          </div>
        ))}
      </div>

      {/* Slot rows */}
      <div className="grid grid-cols-7">
        {Array.from({ length: 7 }, (_, col) => (
          <div key={col} className="flex flex-col gap-1.5 p-1.5 border-r last:border-r-0 min-h-[200px]">
            {Array.from({ length: 3 }, (_, row) => (
              <div
                key={row}
                className="rounded-md border-l-[3px] border-l-muted bg-muted/40 p-2"
              >
                <Skeleton className="mb-1 h-3 w-3/4 rounded" />
                <Skeleton className="h-3 w-1/2 rounded" />
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
