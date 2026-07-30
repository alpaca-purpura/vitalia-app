// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * FidelizacionTabsBar — 5 tabs navigation for fidelización patterns.
 *
 * Tab values match FidelizacionTab type: multisession | followup | maintenance | absence | nps.
 * Accessibility: ARIA tab role, keyboard nav, aria-selected.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { FIDELIZACION_COPY } from "../copy";
import type { FidelizacionTab } from "../types/url-state";

interface FidelizacionTabsBarProps {
  activeTab: FidelizacionTab;
  onTabChange: (tab: FidelizacionTab) => void;
  className?: string;
}

const TABS: { id: FidelizacionTab; label: string }[] = [
  { id: "multisession", label: FIDELIZACION_COPY.tabs.multisession },
  { id: "followup", label: FIDELIZACION_COPY.tabs.followup },
  { id: "maintenance", label: FIDELIZACION_COPY.tabs.maintenance },
  { id: "absence", label: FIDELIZACION_COPY.tabs.absence },
  { id: "nps", label: FIDELIZACION_COPY.tabs.nps },
];

/**
 * Horizontal tabs bar for switching between re-engagement pattern views.
 */
export function FidelizacionTabsBar({
  activeTab,
  onTabChange,
  className,
}: FidelizacionTabsBarProps) {
  return (
    <nav
      role="tablist"
      aria-label={FIDELIZACION_COPY.accessibility.tabsNav}
      className={cn(
        "flex border-b border-[hsl(var(--vitalia-border,220_13%_91%))]",
        className,
      )}
    >
      {TABS.map((tab) => {
        const isActive = tab.id === activeTab;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-controls={`panel-${tab.id}`}
            id={`tab-${tab.id}`}
            onClick={() => onTabChange(tab.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onTabChange(tab.id);
              }
            }}
            className={cn(
              "px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px",
              isActive
                ? "border-[hsl(var(--vitalia-primary,210_90%_50%))] text-[hsl(var(--vitalia-primary,210_90%_50%))]"
                : "border-transparent text-[hsl(var(--vitalia-muted,220_10%_55%))] hover:text-[hsl(var(--vitalia-fg,220_25%_15%))]",
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </nav>
  );
}
