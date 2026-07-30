// cap: platform.lift-shell-chrome-ui-kit
/**
 * EmptyState — generic placeholder (T-K2 port, brand-agnostic).
 *
 * VERBATIM port of vitalia EmptyState. Already brand-agnostic (semantic tokens
 * only, copy passed by prop); only the cn import is re-pointed. Distinct from
 * EmptyStateInline (the history-search empty leaf).
 *
 * Server Component — no state, no effects.
 * No hex colors — semantic tokens only.
 */

import { cn } from "@luana/format/utils";

export interface EmptyStateProps {
  /** Emoji icon displayed at 5xl size with reduced opacity. */
  icon: string;
  /** Heading text — Spanish neutro LatAm, no voseo. */
  title: string;
  /** Description text — max-w-md centered. */
  description: string;
  /** Optional CTA button label. */
  ctaLabel?: string;
  /** Optional CTA click handler. Required if ctaLabel is provided. */
  onCtaClick?: () => void;
  className?: string;
}

/**
 * EmptyState — centered icon + heading + description + optional CTA.
 * Server Component.
 */
export function EmptyState({
  icon,
  title,
  description,
  ctaLabel,
  onCtaClick,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-4 py-16 text-center",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      {/* Emoji icon — aria-hidden (decorative, title is accessible name) */}
      <span
        data-testid="empty-state-icon"
        aria-hidden="true"
        className="text-5xl opacity-50 select-none"
      >
        {icon}
      </span>

      {/* Heading h3 */}
      <h3 className="text-base font-semibold text-foreground">{title}</h3>

      {/* Description */}
      <p className="max-w-md text-sm text-muted-foreground">{description}</p>

      {/* Optional CTA */}
      {ctaLabel && onCtaClick && (
        <button
          type="button"
          onClick={onCtaClick}
          className="mt-2 rounded-md border border-border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-muted transition-colors"
        >
          {ctaLabel}
        </button>
      )}
    </div>
  );
}
