// cap: platform.lift-shell-chrome-ui-kit
"use client";

/**
 * ConfigTab — brand-agnostic config tab (T-K2 port of vitalia ConfigTab).
 *
 * The label (was hardcoded "Plataforma") is a prop. Everything else preserved
 * verbatim (D20 size-10, D21 ml-auto, D22 aria-label, Q13 role=tab tablist peer).
 *
 * data-testid preserved EXACT (vitalia e2e): ribbon-config-tab.
 */

import { forwardRef } from "react";
import { Settings } from "lucide-react";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "../../tooltip";
import { cn } from "@luana/format/utils";

export interface ConfigTabProps {
  /** label + aria-label (Spanish neutro; brand passes e.g. "Plataforma"). */
  label: string;
  active: boolean;
  tabIndex: 0 | -1;
  onClick: () => void;
  onFocus: () => void;
}

export const ConfigTab = forwardRef<HTMLButtonElement, ConfigTabProps>(
  function ConfigTab({ label, active, tabIndex, onClick, onFocus }, ref) {
    return (
      <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <button
            ref={ref}
            type="button"
            role="tab"
            aria-label={label}
            aria-selected={active}
            tabIndex={tabIndex}
            data-testid="ribbon-config-tab"
            data-active={active ? "true" : "false"}
            onClick={onClick}
            onFocus={onFocus}
            className={cn(
              "ml-auto inline-flex size-10 shrink-0 items-center justify-center self-center rounded-md transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
              active
                ? "bg-muted text-foreground ring-1 ring-border"
                : "bg-muted text-muted-foreground hover:bg-muted/80 hover:text-foreground",
            )}
          >
            <Settings className="size-5" aria-hidden="true" />
          </button>
        </TooltipTrigger>
        <TooltipContent side="bottom" sideOffset={4}>
          {label}
        </TooltipContent>
      </Tooltip>
      </TooltipProvider>
    );
  },
);
