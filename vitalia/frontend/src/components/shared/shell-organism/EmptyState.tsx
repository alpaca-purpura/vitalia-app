// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s10-TBD
/**
 * EmptyState — molécula placeholder genérico.
 * F1-S10 vitalia-fase1-empty-states — T-1
 *
 * Renders: emoji icon 5xl opacity-50 + h3 title + description max-w-md + optional CTA button.
 * Used by 16 generic sub-tab placeholders + SubTabContent fallback.
 *
 * Server Component — no state, no effects.
 * Named export (NO default) per FSD-Lite enforce.
 * No hex colors — semantic tokens only.
 *
 * spec_anchor: 03-arch.md § 3.2 #1
 * downstream-regression-na: brand-local shell-organism; no cross-brand consumers
 */

import { cn } from "@/lib/utils";

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
