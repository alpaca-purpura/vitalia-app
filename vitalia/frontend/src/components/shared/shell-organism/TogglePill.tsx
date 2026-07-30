// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s10-TBD
/**
 * TogglePill — wrapper Shadcn Tabs styled as pill toggle.
 * F1-S10 vitalia-fase1-empty-states — T-1
 *
 * Wraps Shadcn <Tabs> / <TabsList> / <TabsTrigger> with pill styling:
 *   rounded-full container + compact trigger pills.
 *
 * Client Component — Radix Tabs uses internal React state for active tab.
 * Named export (NO default) per FSD-Lite enforce.
 * Reuses Shadcn Tabs primitives from components/ui/tabs.tsx.
 *
 * Usage:
 *   <TogglePill items={[{value:'a', label:'A'}, ...]} defaultValue="a">
 *     <TabsContent value="a">…</TabsContent>
 *   </TogglePill>
 *
 * spec_anchor: 03-arch.md § 3.2 #5
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */

"use client";

import { type ReactNode } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";

export interface TogglePillItem {
  /** Unique value identifier for the tab. */
  value: string;
  /** Visible tab label — Spanish neutro LatAm, no voseo. */
  label: string;
}

export interface TogglePillProps {
  /** Tab item definitions */
  items: TogglePillItem[];
  /** Default active tab value */
  defaultValue: string;
  /** Tab panel content. Render as <TabsContent value="…"> children from outside,
   *  or supply children directly and TogglePill wraps them. */
  children?: ReactNode;
  /** data-testid attribute on the root Tabs element */
  "data-testid"?: string;
  className?: string;
}

/**
 * TogglePill — pill-style tab switcher wrapping Shadcn Tabs primitives.
 * Client Component (Radix Tabs manages active state).
 */
export function TogglePill({
  items,
  defaultValue,
  children,
  "data-testid": testId,
  className,
}: TogglePillProps) {
  return (
    <Tabs
      defaultValue={defaultValue}
      data-testid={testId}
      className={cn("w-full", className)}
    >
      {/* Pill-styled tabs list */}
      <TabsList
        className={cn(
          // Override Shadcn default rounded-lg → rounded-full pill
          "h-9 rounded-full border border-border bg-muted p-1 gap-0.5",
          // Don't stretch: fit content
          "w-fit",
        )}
      >
        {items.map((item) => (
          <TabsTrigger
            key={item.value}
            value={item.value}
            className={cn(
              // Pill shape override
              "rounded-full px-3 py-1 text-xs font-medium",
              // Active state uses Shadcn data-[state=active] classes from tabs.tsx
            )}
          >
            {item.label}
          </TabsTrigger>
        ))}
      </TabsList>

      {/* Render children (TabsContent panels) */}
      {children}
    </Tabs>
  );
}

// Re-export TabsContent for convenience when consuming TogglePill
export { TabsContent as TogglePillContent };
