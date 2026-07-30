// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * RibbonTab — brand-agnostic ribbon tab (T-K2 port of vitalia RibbonTab).
 *
 * The per-agent soft-bg class (was `agentBgSoftClass(slug)` JIT-static literal)
 * is brand-coupled (brand color tokens), so the kit takes a `getAgentClasses`
 * injected fn and reads `.softBg`. The agent descriptor comes from the injected
 * catalog (lookup by slug). All visual contract (D17.1-D18 cement) preserved.
 *
 * data-testid preserved EXACT (vitalia e2e): ribbon-tab-{slug},
 * avatar-fallback-{slug}.
 */

import { forwardRef } from "react";
import { Avatar, AvatarImage, AvatarFallback } from "../../avatar";
import { cn } from "@luana/format/utils";
import type { GetAgentClasses, ShellAgentDescriptor } from "./types";

export interface RibbonTabProps {
  descriptor: ShellAgentDescriptor;
  getAgentClasses: GetAgentClasses;
  active: boolean;
  tabIndex: 0 | -1;
  onClick: () => void;
  onFocus: () => void;
}

export const RibbonTab = forwardRef<HTMLButtonElement, RibbonTabProps>(
  function RibbonTab({ descriptor, getAgentClasses, active, tabIndex, onClick, onFocus }, ref) {
    const slug = descriptor.slug;
    const softBg = getAgentClasses(slug).softBg;

    return (
      <button
        ref={ref}
        type="button"
        role="tab"
        aria-selected={active}
        tabIndex={tabIndex}
        data-testid={`ribbon-tab-${slug}`}
        data-active={active ? "true" : "false"}
        onClick={onClick}
        onFocus={onFocus}
        className={cn(
          // base layout — Q14: shrink-0 sin min-w (tabs orgánicos)
          "flex shrink-0 items-center gap-2 rounded-md px-4 text-sm transition-colors",
          // focus ring
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
          // active vs inactive
          // Q16 cement: active:hover repite el soft-bg para preservar tint
          active
            ? cn(softBg, "font-semibold text-foreground", `hover:${softBg}`)
            : "font-medium text-muted-foreground hover:bg-muted hover:text-foreground",
        )}
      >
        <Avatar className="size-7 shrink-0" aria-hidden="true">
          {descriptor.thumbnail ? <AvatarImage src={descriptor.thumbnail} alt="" /> : null}
          <AvatarFallback
            className={cn(softBg, "text-foreground")}
            data-testid={`avatar-fallback-${slug}`}
          >
            {descriptor.initial}
          </AvatarFallback>
        </Avatar>
        {/* Q15 cement: whitespace-nowrap en ambos spans garantiza ribbon h-14 uniforme */}
        {/* A11y cement: sub-label sólido cuando active para WCAG AA sobre bg-agent-*-soft.
            T-V2 fix-loop: /60 daba 4.25 sobre mateo-soft DARK (#534a09) → /75 (AA ambos temas). */}
        <span className="flex flex-col items-start leading-tight whitespace-nowrap">
          <span className="whitespace-nowrap">{descriptor.tabLabel}</span>
          <span
            className={cn(
              "whitespace-nowrap text-[10px]",
              active ? "text-foreground/75" : "text-muted-foreground",
            )}
          >
            {descriptor.name}
          </span>
        </span>
      </button>
    );
  },
);
