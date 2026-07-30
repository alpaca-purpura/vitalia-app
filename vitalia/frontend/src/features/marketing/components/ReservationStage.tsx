// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * ReservationStage — reservation funnel stage panel.
 * Renders: Lucas recommendations card + KPI hero cards + AttributionMatrixWidget inline.
 * SC-MK-03: Attribution matrix MUST appear inline in the reservation stage.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/cn";
import { useStageDetail } from "../api/use-stage-detail";
import { LucasStageRecommendationsCard } from "./LucasStageRecommendationsCard";
import { AttributionMatrixWidget } from "./AttributionMatrixWidget";
import { MARKETING_COPY } from "../copy";

export type ReservationStageProps = {
  period?: "7d" | "30d" | "90d";
  className?: string;
};

/**
 * ReservationStage — stage panel rendered by StageDispatcher for `reservation` tab.
 * Includes AttributionMatrixWidget per SC-MK-03 acceptance criteria.
 */
export const ReservationStage = forwardRef<HTMLElement, ReservationStageProps>(
  ({ period = "30d", className }, ref) => {
    const { data, isLoading } = useStageDetail({
      stage: "reservation",
      period,
    });

    if (isLoading) {
      return (
        <section
          ref={ref}
          role="tabpanel"
          id="stage-panel-reservation"
          aria-labelledby="stage-tab-reservation"
          aria-busy={true}
          className={cn("flex flex-col gap-4", className)}
        >
          <div
            role="status"
            aria-label={MARKETING_COPY.ui.loading}
            className="animate-pulse space-y-3"
          >
            <div className="grid grid-cols-2 gap-3">
              <div className="h-16 vt-bg-surface-alt rounded-lg" />
              <div className="h-16 vt-bg-surface-alt rounded-lg" />
            </div>
            <div className="h-32 vt-bg-surface-alt rounded-lg" />
            <div className="h-48 vt-bg-surface-alt rounded-lg" />
          </div>
        </section>
      );
    }

    return (
      <section
        ref={ref}
        role="tabpanel"
        id="stage-panel-reservation"
        aria-labelledby="stage-tab-reservation"
        className={cn("flex flex-col gap-4", className)}
      >
        {/* KPI hero cards from stage detail */}
        {data && data.kpis.length > 0 && (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {data.kpis.map((kpi) => (
              <div
                key={kpi.key}
                className="rounded-lg vt-bg-surface vt-border border p-3 flex flex-col gap-1"
              >
                <span className="text-xs vt-text-muted">{kpi.label}</span>
                <span className="text-lg font-semibold vt-text tabular-nums">
                  {kpi.value !== null ? String(kpi.value) : "—"}
                  {kpi.unit === "pct" ? "%" : ""}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Lucas stage recommendations */}
        <LucasStageRecommendationsCard stage="reservation" />

        {/* SC-MK-03: Attribution matrix inline in reservation stage */}
        <AttributionMatrixWidget period={period} />
      </section>
    );
  },
);
ReservationStage.displayName = "ReservationStage";
