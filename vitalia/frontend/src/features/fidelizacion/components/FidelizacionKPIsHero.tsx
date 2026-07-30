// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * FidelizacionKPIsHero — 5 KPI stat cards for fidelización module.
 *
 * Renders aggregated KPIs from summary endpoint.
 * HIPAA-lite: ALL values are aggregate/anonymized — NO PHI.
 * Accessibility: each card has role="status" + aria-label.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { FIDELIZACION_COPY } from "../copy";
import type { FidelizacionSummaryResponse } from "../types/fidelizacion-summary";

interface FidelizacionKPIsHeroProps {
  isPending: boolean;
  data: FidelizacionSummaryResponse | null | undefined;
  className?: string;
}

function KPISkeleton() {
  return (
    <div className="h-20 animate-pulse rounded-lg bg-[hsl(var(--vitalia-bg-soft,220_20%_96%))]" />
  );
}

interface StatCardProps {
  label: string;
  value: string | number;
  trend?: number;
  ariaLabel: string;
  className?: string;
}

function StatCard({
  label,
  value,
  trend,
  ariaLabel,
  className,
}: StatCardProps) {
  const copy = FIDELIZACION_COPY.kpis.trend;
  const trendIcon =
    trend === undefined
      ? null
      : trend > 0
        ? copy.up
        : trend < 0
          ? copy.down
          : copy.neutral;
  const trendClass =
    trend === undefined
      ? ""
      : trend > 0
        ? "text-[hsl(var(--vitalia-success,145_55%_40%))]"
        : trend < 0
          ? "text-[hsl(var(--vitalia-danger,0_75%_45%))]"
          : "text-[hsl(var(--vitalia-muted,220_10%_55%))]";

  return (
    <article
      role="status"
      aria-label={ariaLabel}
      className={cn(
        "flex flex-col gap-1 rounded-lg border border-[hsl(var(--vitalia-border,220_13%_91%))] bg-white p-4",
        className,
      )}
    >
      <span className="text-xs font-medium text-[hsl(var(--vitalia-muted,220_10%_55%))] uppercase tracking-wide">
        {label}
      </span>
      <span className="text-2xl font-semibold text-[hsl(var(--vitalia-fg,220_25%_15%))]">
        {value}
      </span>
      {trendIcon !== null && trend !== undefined && (
        <span
          className={cn("text-xs font-medium", trendClass)}
          aria-hidden="true"
        >
          {trendIcon} {Math.abs(trend)}
          <span className="ml-1 text-[hsl(var(--vitalia-muted,220_10%_55%))]">
            {copy.vsLastPeriod}
          </span>
        </span>
      )}
    </article>
  );
}

/**
 * Hero section with 5 aggregate KPI cards.
 * All values are clinic-level aggregates — no per-patient PHI.
 */
export function FidelizacionKPIsHero({
  isPending,
  data,
  className,
}: FidelizacionKPIsHeroProps) {
  const copy = FIDELIZACION_COPY.kpis;

  if (isPending) {
    return (
      <section
        aria-label={FIDELIZACION_COPY.accessibility.kpisRegion}
        aria-busy="true"
        className={cn(
          "grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5",
          className,
        )}
      >
        {Array.from({ length: 5 }).map((_, i) => (
          <KPISkeleton key={i} />
        ))}
      </section>
    );
  }

  return (
    <section
      aria-label={FIDELIZACION_COPY.accessibility.kpisRegion}
      className={cn(
        "grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5",
        className,
      )}
    >
      <StatCard
        label={copy.patientsInFollowup.label}
        value={data?.patientsInFollowup ?? 0}
        trend={data?.trendVsPreviousPeriod.patientsInFollowup}
        ariaLabel={copy.patientsInFollowup.ariaLabel(
          data?.patientsInFollowup ?? 0,
        )}
      />
      <StatCard
        label={copy.nearAbandonment.label}
        value={data?.nearAbandonment ?? 0}
        trend={data?.trendVsPreviousPeriod.nearAbandonment}
        ariaLabel={copy.nearAbandonment.ariaLabel(data?.nearAbandonment ?? 0)}
      />
      <StatCard
        label={copy.returnRate.label}
        value={`${Math.round((data?.returnRate ?? 0) * 100)}%`}
        trend={
          data?.trendVsPreviousPeriod.returnRate !== undefined
            ? Math.round(data.trendVsPreviousPeriod.returnRate * 100)
            : undefined
        }
        ariaLabel={copy.returnRate.ariaLabel(data?.returnRate ?? 0)}
      />
      <StatCard
        label={copy.reEngaged.label}
        value={data?.reEngagedThisPeriod ?? 0}
        trend={data?.trendVsPreviousPeriod.reEngagedThisPeriod}
        ariaLabel={copy.reEngaged.ariaLabel(data?.reEngagedThisPeriod ?? 0)}
      />
      <StatCard
        label={copy.npsAverage.label}
        value={
          data?.npsAverage !== undefined ? data.npsAverage.toFixed(1) : "—"
        }
        trend={data?.trendVsPreviousPeriod.npsAverage}
        ariaLabel={copy.npsAverage.ariaLabel(data?.npsAverage ?? 0)}
      />
    </section>
  );
}
