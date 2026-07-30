// cap: platform.lift-shell-chrome-ui-kit
/**
 * EmptyStateInline — inline empty state atom (search no results / SC-13).
 * T-K2 port of vitalia EmptyStateInline (F1-S5 T-3) — zero brand logic.
 *
 * Server Component — purely presentational: icon circle (bg-muted + Search) +
 * heading + description. data-testid 'history-empty-state' is generic (no brand
 * token) — preserved verbatim.
 */

import { Search } from "lucide-react";

export interface EmptyStateInlineProps {
  /** Heading, e.g. 'Sin resultados'. */
  heading: string;
  /** Description, e.g. 'Intenta con otra palabra'. */
  description: string;
}

/** EmptyStateInline — empty state with icon, heading, description. */
export function EmptyStateInline({ heading, description }: EmptyStateInlineProps) {
  return (
    <div
      data-testid="history-empty-state"
      className="flex flex-col items-center justify-center gap-3 px-4 py-8 text-center"
      role="status"
      aria-live="polite"
    >
      <div
        className="flex h-12 w-12 items-center justify-center rounded-full bg-muted"
        aria-hidden="true"
      >
        <Search className="size-5 text-muted-foreground" aria-hidden="true" />
      </div>
      <h3 className="text-sm font-medium text-foreground">{heading}</h3>
      <p className="text-xs text-muted-foreground">{description}</p>
    </div>
  );
}
