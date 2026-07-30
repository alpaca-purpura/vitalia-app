// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * TogglePill — wrapper Shadcn Tabs styled as pill toggle.
 * T-K2 port of vitalia TogglePill (F1-S10).
 *
 * Wraps Shadcn <Tabs> / <TabsList> / <TabsTrigger> with pill styling.
 * Brand-agnostic: no brand imports.
 *
 * Client Component — Radix Tabs uses internal React state for active tab.
 * Named export (NO default) per FSD-Lite enforce.
 * Reuses Shadcn Tabs primitives from the kit.
 */

import { type ReactNode } from "react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "../../tabs";
import { cn } from "@luana/format/utils";

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
  /** Tab panel content as children (e.g. <TabsContent value="...">). */
  children?: ReactNode;
  /** data-testid attribute on the root Tabs element */
  "data-testid"?: string;
  className?: string;
}

/**
 * TogglePill — pill-style tab switcher wrapping Shadcn Tabs primitives.
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
