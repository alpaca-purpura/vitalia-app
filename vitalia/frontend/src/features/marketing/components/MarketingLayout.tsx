// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * MarketingLayout — orchestrates the marketing page layout.
 *
 * Structure per 02-design-ui.md:
 *   1. Bowtie SVG — sticky top (position sticky, top-0, z-10, border-b)
 *   2. Stage tabs — horizontal 5-tab nav (nuqs URL state)
 *   3. StageDispatcher — stage-specific content (flex-1 overflow-auto)
 *   4. MarketingActivityFooter — activity/sync info
 *
 * Client Component: requires nuqs useQueryState for tab URL state management.
 * Data: useBowtieSummary (T-mk-fe-1 hook).
 *
 * SC-MK-03: bowtie is sticky top so it stays visible when scrolling stage content.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { useQueryState } from "nuqs";
import { cn } from "@/lib/cn";
import { useBowtieSummary } from "../api/use-bowtie-summary";
import { marketingParsers } from "../types/url-state";
import type { RecommendationStage } from "../types/lucas-recommendation";
import { MarketingBowtieSVG } from "./MarketingBowtieSVG";
import { MarketingStageTabs } from "./MarketingStageTabs";
import { StageDispatcher } from "./StageDispatcher";
import { MarketingActivityFooter } from "./MarketingActivityFooter";
import { MARKETING_COPY } from "../copy";

export type MarketingLayoutProps = {
  className?: string;
};

export function MarketingLayout({ className }: MarketingLayoutProps) {
  const [activeTab, setActiveTab] = useQueryState("tab", marketingParsers.tab);
  const [period] = useQueryState("period", marketingParsers.period);

  const { data, isLoading, isError } = useBowtieSummary({
    period: period ?? "30d",
  });

  const stages = data?.stages ?? [];
  const lastSyncAt = data?.lastSyncAt ?? null;
  // Total leads in current stage = stage count for active tab
  const activeStage = stages.find((s) => s.slug === activeTab);
  const leadsAnalyzed = activeStage?.count ?? null;

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Bowtie SVG — sticky top (SC-MK-03: visible while scrolling stage content) */}
      <div
        data-testid="bowtie-sticky-container"
        className="sticky top-0 z-10 vt-bg-surface border-b vt-border px-4 py-4"
      >
        {isError ? (
          <p className="text-xs vt-text-danger text-center py-4" role="alert">
            {MARKETING_COPY.bowtie.errorMessage}
          </p>
        ) : (
          <MarketingBowtieSVG stages={stages} isLoading={isLoading} />
        )}
      </div>

      {/* Stage tabs — horizontal nav */}
      <MarketingStageTabs
        stages={stages}
        activeTab={(activeTab as RecommendationStage) ?? "attraction"}
        onTabChange={(slug) => {
          void setActiveTab(slug);
        }}
      />

      {/* Stage content — flex-1 overflow-auto */}
      <StageDispatcher
        activeTab={(activeTab as RecommendationStage) ?? "attraction"}
        className="flex-1"
      />

      {/* Activity footer */}
      <MarketingActivityFooter
        leadsAnalyzed={leadsAnalyzed}
        lastSyncAt={lastSyncAt}
        isLoading={isLoading}
      />
    </div>
  );
}

MarketingLayout.displayName = "MarketingLayout";
