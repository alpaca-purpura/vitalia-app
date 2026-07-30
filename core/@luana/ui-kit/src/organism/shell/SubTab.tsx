// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * SubTab — brand-agnostic sub-tab button molecule.
 * T-K2 port of vitalia SubTab (F1-S8).
 *
 * Brand coupling removed: SubTabMeta → ShellSubTabMeta (kit type).
 * Color/active classes injected via getAgentClasses (no brand _agent-tw-classes import).
 * Agent slug context injected by parent SubTabsBar.
 *
 * Active state:
 *   - Normal agents: softBg + accentText + font-semibold
 *   - Config agent: bg-muted + text-foreground + font-semibold (neutral, not agent color)
 *
 * Lucas exception (D18 from vitalia): active → text-foreground NOT accentText.
 *   This is brand-side now — the brand passes the right GetAgentClasses fn that
 *   already handles the exception for its catalog (e.g. agentTextClassSubTab in vitalia).
 *
 * A11y: role="tab" + aria-selected + tabIndex (roving tabindex) + focus-visible ring.
 *
 * Named export (NO default) per FSD-Lite enforce.
 */

import { forwardRef } from "react";
import { cn } from "@luana/format/utils";
import type { GetAgentClasses, ShellSubTabMeta } from "./types";

/** Props for SubTab molecule. */
export interface SubTabProps {
  /** Sub-tab descriptor (id, label, icon) from the brand catalog. */
  subtab: ShellSubTabMeta;
  /** Agent slug — determines active bg/text classes via getAgentClasses. */
  agentSlug: string;
  /** Whether this is the config/platform tab (neutral active color, not agent color). */
  isConfig?: boolean;
  /** Brand fn returning Tailwind class bundles for agent slugs. */
  getAgentClasses: GetAgentClasses;
  /** Whether this sub-tab is currently active (URL-derived in SubTabsBar). */
  active: boolean;
  /**
   * Roving tabindex — 0 for focused tab in group, -1 for others.
   * Managed by parent SubTabsBar keyboard handler.
   */
  tabIndex: 0 | -1;
  /** Click handler — parent SubTabsBar calls router.push. */
  onClick: React.MouseEventHandler<HTMLButtonElement>;
  /** Focus handler — parent SubTabsBar uses to sync focusedIdx. */
  onFocus: React.FocusEventHandler<HTMLButtonElement>;
  /** data-testid override. */
  "data-testid"?: string;
}

/**
 * SubTab — renders a single tab button in the horizontal sub-tabs bar.
 * Composed into SubTabsBar organism which provides roving tabindex management.
 *
 * Q4 cement (from vitalia): whitespace-nowrap HARD — label NO wrap.
 */
export const SubTab = forwardRef<HTMLButtonElement, SubTabProps>(
  function SubTab(
    { subtab, agentSlug, isConfig = false, getAgentClasses, active, tabIndex, onClick, onFocus, "data-testid": testId },
    ref
  ) {
    const classes = getAgentClasses(agentSlug);

    return (
      <button
        ref={ref}
        type="button"
        role="tab"
        aria-selected={active}
        tabIndex={tabIndex}
        data-testid={testId ?? `sub-tab-${subtab.id}`}
        data-active={active ? "true" : "false"}
        data-agent={agentSlug}
        onClick={onClick}
        onFocus={onFocus}
        className={cn(
          // Base layout — Q4 cement: whitespace-nowrap HARD
          "flex shrink-0 items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-all whitespace-nowrap",
          // Focus ring — focus-visible only (keyboard nav, no mouse ring)
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
          // Active vs inactive states
          active
            ? isConfig
              ? "bg-muted text-foreground font-semibold"
              : cn(classes.softBg, classes.accentText, "font-semibold")
            : "text-muted-foreground font-medium hover:bg-muted hover:text-foreground",
        )}
      >
        {/* Emoji icon — aria-hidden (decorative) */}
        <span aria-hidden="true">{subtab.icon}</span>
        {/* Visible label */}
        <span>{subtab.label}</span>
      </button>
    );
  }
);
