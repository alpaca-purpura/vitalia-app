// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * ExpansionStage — expansion funnel stage panel.
 * Renders: Lucas recommendations card + KPI hero cards + ReferralsWidget + NPS placeholder.
 * SC-MK-03: ReferralsWidget MUST appear inline in the expansion stage.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/cn";
import { useStageDetail } from "../api/use-stage-detail";
import { LucasStageRecommendationsCard } from "./LucasStageRecommendationsCard";
import { ReferralsWidget } from "./ReferralsWidget";
import { MARKETING_COPY } from "../copy";

export type ExpansionStageProps = {
  period?: "7d" | "30d" | "90d";
  className?: string;
};

/**
 * ExpansionStage — stage panel rendered by StageDispatcher for `expansion` tab.
 * Includes ReferralsWidget per SC-MK-03 acceptance criteria + NPS placeholder.
 */
export const ExpansionStage = forwardRef<HTMLElement, ExpansionStageProps>(
  ({ period = "30d", className }, ref) => {
    const { data, isLoading } = useStageDetail({ stage: "expansion", period });

    if (isLoading) {
      return (
        <section
          ref={ref}
          role="tabpanel"
          id="stage-panel-expansion"
          aria-labelledby="stage-tab-expansion"
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
        id="stage-panel-expansion"
        aria-labelledby="stage-tab-expansion"
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
        <LucasStageRecommendationsCard stage="expansion" />

        {/* SC-MK-03: Referrals widget inline in expansion stage */}
        <ReferralsWidget period={period} />

        {/* NPS placeholder — future ticket will implement real NPS chart */}
        <div
          data-testid="nps-placeholder"
          data-slot="nps-widget"
          className="rounded-lg vt-bg-surface vt-border border p-4"
          aria-label="NPS"
        >
          <div className="text-xs font-semibold vt-text mb-1">NPS</div>
          <div className="text-xs vt-text-muted italic">
            {MARKETING_COPY.ui.loading}
          </div>
        </div>
      </section>
    );
  },
);
ExpansionStage.displayName = "ExpansionStage";
