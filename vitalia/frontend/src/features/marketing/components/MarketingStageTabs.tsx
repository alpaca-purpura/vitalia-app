// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * MarketingStageTabs — 5 horizontal tab selectors for bowtie stages.
 *
 * Active tab: cian gradient bg + cian bottom border + azul-marino text (per mockup tab-active class).
 * Inactive: muted text, hover bg-muted.
 * Count badge: active=cian fill white, inactive=muted bg.
 * Per SC-MK-03: tab changes use nuqs replace (intra-route, no browser history entry).
 *
 * @see 02-design-ui-mockup.html .tab-active style
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { cn } from "@/lib/cn";
import type { BowtieStage } from "../types/bowtie";
import type { RecommendationStage } from "../types/lucas-recommendation";

export type MarketingStageTabsProps = {
  stages: BowtieStage[];
  activeTab: RecommendationStage;
  onTabChange: (slug: RecommendationStage) => void;
  className?: string;
};

export function MarketingStageTabs({
  stages,
  activeTab,
  onTabChange,
  className,
}: MarketingStageTabsProps) {
  return (
    <nav
      role="tablist"
      aria-label="Etapas del embudo"
      className={cn(
        "flex items-center gap-1 overflow-x-auto vt-bg-surface border-b vt-border px-4",
        className,
      )}
    >
      {stages.map((stage) => {
        const isActive = stage.slug === activeTab;
        return (
          <button
            key={stage.slug}
            role="tab"
            aria-selected={isActive}
            aria-controls={`stage-panel-${stage.slug}`}
            id={`stage-tab-${stage.slug}`}
            data-active={isActive ? "true" : "false"}
            onClick={() => onTabChange(stage.slug as RecommendationStage)}
            className={cn(
              "px-4 py-3 text-xs flex items-center gap-2 whitespace-nowrap transition-colors focus-visible:outline-none focus-visible:ring-2 vt-ring-cian focus-visible:ring-offset-1",
              // Active: cian gradient bg + cian bottom border + azul-marino text + bold
              isActive &&
                "vt-bg-tab-active vt-border-b-cian vt-text-azul-marino-bold",
              // Inactive
              !isActive && "vt-text-muted hover:vt-bg-muted",
            )}
          >
            <span>{stage.label}</span>
            <span
              className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold",
                isActive ? "vt-bg-cian vt-text-white" : "vt-bg-muted vt-text",
              )}
              aria-label={`${stage.count} en ${stage.label}`}
            >
              {stage.count}
            </span>
          </button>
        );
      })}
    </nav>
  );
}

MarketingStageTabs.displayName = "MarketingStageTabs";
