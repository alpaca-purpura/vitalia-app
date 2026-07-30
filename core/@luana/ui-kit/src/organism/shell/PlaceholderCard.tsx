// cap: platform.lift-shell-chrome-ui-kit
/**
 * PlaceholderCard — card placeholder with status dot (T-K2 port, brand-agnostic).
 *
 * VERBATIM port of vitalia PlaceholderCard. Already brand-agnostic (semantic
 * tokens, copy by prop); only the cn import + StatusDot relative import change.
 *
 * Server Component — purely presentational, no state.
 */

import { cn } from "@luana/format/utils";
import { StatusDot, type StatusDotVariant } from "./StatusDot";

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
