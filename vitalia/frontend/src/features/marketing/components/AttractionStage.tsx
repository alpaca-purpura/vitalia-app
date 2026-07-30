// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * AttractionStage — attraction funnel stage panel.
 * Renders: Lucas recommendations card + KPI hero cards + channel breakdown placeholder.
 * Channel breakdown real implementation: T-mk-fe-5.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/cn";
import { useStageDetail } from "../api/use-stage-detail";
import { LucasStageRecommendationsCard } from "./LucasStageRecommendationsCard";
import { ChannelBreakdownRow } from "./ChannelBreakdownRow";
import { MARKETING_COPY } from "../copy";

export type AttractionStageProps = {
  period?: "7d" | "30d" | "90d";
  className?: string;
};

/**
 * AttractionStage — stage panel rendered by StageDispatcher for `attraction` tab.
 */
export const AttractionStage = forwardRef<HTMLElement, AttractionStageProps>(
  ({ period = "30d", className }, ref) => {
    const { data, isLoading } = useStageDetail({ stage: "attraction", period });

    if (isLoading) {
      return (
        <section
          ref={ref}
          role="tabpanel"
          id="stage-panel-attraction"
          aria-labelledby="stage-tab-attraction"
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
          </div>
        </section>
      );
    }

    return (
      <section
        ref={ref}
        role="tabpanel"
        id="stage-panel-attraction"
        aria-labelledby="stage-tab-attraction"
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
        <LucasStageRecommendationsCard stage="attraction" />

        {/* Channel breakdown — T-mk-fe-5 real implementation */}
        <div
          data-testid="channel-breakdown-placeholder"
          data-slot="channel-breakdown"
          className="rounded-lg vt-bg-surface vt-border border overflow-hidden"
          aria-label={MARKETING_COPY.channels.title}
        >
          <div className="px-4 py-3 border-b vt-border-soft text-xs font-semibold vt-text">
            {MARKETING_COPY.channels.title}
          </div>
          <div className="divide-y vt-divide">
            <ChannelBreakdownRow provider="meta_ads" />
            <ChannelBreakdownRow provider="google_ads" />
          </div>
        </div>
      </section>
    );
  },
);
AttractionStage.displayName = "AttractionStage";
