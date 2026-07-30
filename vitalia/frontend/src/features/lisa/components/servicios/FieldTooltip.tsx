// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
/**
 * FieldTooltip.tsx — Small contextual help tooltip for workspace form fields.
 *
 * Renders an info icon that shows a tooltip on hover/focus (keyboard accessible).
 * Used inline next to field labels to explain medical terminology or Adrián context.
 *
 * Uses Shadcn Tooltip from components/ui (NEVER recreate).
 *
 * spec §FieldTooltip · 03-arch-fe.md §5
 */

import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

interface FieldTooltipProps {
  /** The tooltip text (Spanish neutro LatAm — sin voseo). */
  content: string;
  className?: string;
}

export function FieldTooltip({ content, className }: FieldTooltipProps) {
  return (
    <TooltipProvider delayDuration={200}>
      <Tooltip>
        <TooltipTrigger
          type="button"
          className={cn(
            "inline-flex items-center justify-center rounded-full",
            "h-4 w-4 text-muted-foreground hover:text-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
            "transition-colors",
            className,
          )}
          aria-label={`Ayuda: ${content}`}
        >
          {/* Accessible info icon via SVG (no external icon dependency) */}
          <svg
            width="14"
            height="14"
            viewBox="0 0 14 14"
            fill="none"
            aria-hidden="true"
            xmlns="http://www.w3.org/2000/svg"
          >
            <circle cx="7" cy="7" r="6.5" stroke="currentColor" />
            <path
              d="M7 6.5v4"
              stroke="currentColor"
              strokeWidth="1.25"
              strokeLinecap="round"
            />
            <circle cx="7" cy="4.5" r="0.75" fill="currentColor" />
          </svg>
        </TooltipTrigger>
        <TooltipContent
          side="top"
          className="max-w-xs text-xs leading-snug"
        >
          {content}
        </TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}
