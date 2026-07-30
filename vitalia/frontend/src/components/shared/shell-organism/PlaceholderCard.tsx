// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s10-TBD
/**
 * PlaceholderCard — molécula card de placeholder con status.
 * F1-S10 vitalia-fase1-empty-states — T-1
 *
 * Renders a Card with: emoji/icon + h3 heading + description text + StatusDot.
 * Used in LisaServiciosPlaceholder (5 service cards), CamilaVozPlaceholder (3 stat cards).
 *
 * Server Component — purely presentational, no state.
 * Named export (NO default) per FSD-Lite enforce.
 * Reuses Shadcn Card primitive from components/ui/card.tsx.
 *
 * spec_anchor: 03-arch.md § 3.2 #2
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */

import { cn } from "@/lib/utils";
import { StatusDot, type StatusDotVariant } from "@luana/ui-kit";

export interface PlaceholderCardProps {
  /** Emoji icon displayed at 2xl size. */
  icon: string;
  /** Card heading text — Spanish neutro LatAm. */
  title: string;
  /** Card description or stat text. */
  description: string;
  /** Status dot variant — defaults to 'green'. */
  status?: StatusDotVariant;
  /** Optional count/badge value displayed inline. */
  count?: number | string;
  className?: string;
}

/**
 * PlaceholderCard — Card with icon, heading, description and status dot.
 * Server Component.
 */
export function PlaceholderCard({
  icon,
  title,
  description,
  status = "green",
  count,
  className,
}: PlaceholderCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card p-4 flex flex-col gap-2",
        className,
      )}
      data-testid="placeholder-card"
    >
      {/* Card header: icon + status dot + optional count */}
      <div className="flex items-start justify-between gap-2">
        <span aria-hidden="true" className="text-2xl select-none leading-none">
          {icon}
        </span>
        <div className="flex items-center gap-1.5">
          {count !== undefined && (
            <span className="text-xs font-semibold text-muted-foreground tabular-nums">
              {count}
            </span>
          )}
          <StatusDot variant={status} />
        </div>
      </div>

      {/* Card heading */}
      <h3 className="text-sm font-semibold text-foreground leading-snug">
        {title}
      </h3>

      {/* Card description */}
      <p className="text-xs text-muted-foreground leading-relaxed">
        {description}
      </p>
    </div>
  );
}
