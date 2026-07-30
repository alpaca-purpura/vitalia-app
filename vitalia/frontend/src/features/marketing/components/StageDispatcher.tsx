// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * StageDispatcher — renders the correct stage section component based on active URL tab.
 *
 * Dispatches based on ?tab= nuqs URL param (RecommendationStage).
 * Each stage section: consumes useStageDetail + renders LucasStageRecommendationsCard + KPIs + secondary surfaces.
 *
 * T-mk-fe-3: LucasStageRecommendationsCard (wired in each stage component)
 * T-mk-fe-4: AttractionStage, QualificationStage, ReservationStage (+ AttributionMatrix),
 *             AdoptionStage, ExpansionStage (+ ReferralsWidget + NPS placeholder)
 * T-mk-fe-5: ChannelBreakdownRow (attraction) — stub placeholder rendered by AttractionStage
 *
 * Per 02-design-ui.md:
 *   - AttributionMatrix ONLY on reservation tab
 *   - ReferralsWidget ONLY on expansion tab
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { cn } from "@/lib/cn";
import type { RecommendationStage } from "../types/lucas-recommendation";
import { AttractionStage } from "./AttractionStage";
import { QualificationStage } from "./QualificationStage";
import { ReservationStage } from "./ReservationStage";
import { AdoptionStage } from "./AdoptionStage";
import { ExpansionStage } from "./ExpansionStage";

export type StageDispatcherProps = {
  activeTab: RecommendationStage;
  period?: "7d" | "30d" | "90d";
  className?: string;
};

/**
 * StageDispatcher — routes to the appropriate stage section component.
 */
export function StageDispatcher({
  activeTab,
  period = "30d",
  className,
}: StageDispatcherProps) {
  return (
    <div
      className={cn("flex-1 overflow-auto vt-bg-surface-alt p-4", className)}
    >
      {activeTab === "attraction" && <AttractionStage period={period} />}
      {activeTab === "qualification" && <QualificationStage period={period} />}
      {activeTab === "reservation" && <ReservationStage period={period} />}
      {activeTab === "adoption" && <AdoptionStage period={period} />}
      {activeTab === "expansion" && <ExpansionStage period={period} />}
    </div>
  );
}

StageDispatcher.displayName = "StageDispatcher";
