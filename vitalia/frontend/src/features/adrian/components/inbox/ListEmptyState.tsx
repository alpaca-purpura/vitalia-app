// cap: adrian.inbox
// story-origin: TBD
/**
 * ListEmptyState.tsx — 4 empty state variants for the conversation list.
 *
 * Variants per 01-spec-extract.md § 8:
 *   noConversations   — list is truly empty (no conversations yet)
 *   noHelpNeeded      — filtered by helpNeeded, none match
 *   noMediaUnread     — filtered by unreadMedia, none match
 *   noResultsFilter   — active filters return zero results (with CTA to clear)
 *
 * All copy from INBOX_COPY SSoT (no hardcoded strings).
 * Server Component — no state/effects needed.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { INBOX_COPY } from "../../lib/copy";

/** Empty state variant key */
export type ListEmptyStateVariant =
  | "noConversations"
  | "noHelpNeeded"
  | "noMediaUnread"
  | "noResultsFilter";

interface ListEmptyStateProps {
  variant: ListEmptyStateVariant;
  /** Callback for "Limpiar filtros" CTA — only shown for noResultsFilter */
  onClearFilters?: () => void;
  className?: string;
}

/** Icon per variant — accessible emoji with aria-hidden */
function EmptyIcon({ variant }: { variant: ListEmptyStateVariant }) {
  const icons: Record<ListEmptyStateVariant, string> = {
    noConversations: "💬",
    noHelpNeeded: "✅",
    noMediaUnread: "🎧",
    noResultsFilter: "🔍",
  };
  return (
    <span aria-hidden="true" className="text-3xl">
      {icons[variant]}
    </span>
  );
}

/** Copy per variant from INBOX_COPY SSoT */
function getCopy(variant: ListEmptyStateVariant) {
  return INBOX_COPY.empty[variant];
}

/**
 * ListEmptyState — renders one of 4 empty state layouts for the conversation list.
 * Handles the "no results" variant with an optional clear-filters CTA.
 */
export function ListEmptyState({
  variant,
  onClearFilters,
  className,
}: ListEmptyStateProps) {
  const copy = getCopy(variant);

  return (
    <div
      role="status"
      aria-live="polite"
      data-testid="list-empty-state"
      className={cn(
        "flex flex-col items-center justify-center gap-3 px-6 py-10 text-center",
        className,
      )}
    >
      <EmptyIcon variant={variant} />

      <div className="flex flex-col gap-1">
        <p className="text-sm font-semibold vt-text-foreground">
          {copy.heading}
        </p>
        <p className="text-xs leading-relaxed vt-text-muted">{copy.body}</p>
      </div>

      {variant === "noResultsFilter" && onClearFilters && (
        <button
          type="button"
          onClick={onClearFilters}
          className={cn(
            "mt-1 rounded-md px-4 py-1.5 text-xs font-medium",
            "vt-bg-primary vt-text-primary-foreground",
            "hover:opacity-90 focus-visible:outline focus-visible:outline-2",
            "focus-visible:outline-offset-2 focus-visible:vt-outline-primary",
            "transition-opacity",
          )}
        >
          {INBOX_COPY.empty.noResultsFilter.cta}
        </button>
      )}
    </div>
  );
}
