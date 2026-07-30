// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * MarketingActivityFooter — activity/sync status footer row.
 *
 * Template per 02-design-ui.md:
 *   "Lucas analizó {leads_analyzed} leads · sistema sync canales c/4h · última sync {last_sync}"
 *
 * @see 02-design-ui-mockup.html activity footer section
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { cn } from "@/lib/cn";
import { MARKETING_COPY } from "../copy";

export type MarketingActivityFooterProps = {
  /** Count of leads analyzed by Lucas in this period */
  leadsAnalyzed?: number | null;
  /** ISO 8601 string of last sync time */
  lastSyncAt?: string | null;
  isLoading?: boolean;
  className?: string;
};

function formatLastSync(lastSyncAt: string | null | undefined): string {
  if (!lastSyncAt) return MARKETING_COPY.bowtie.neverSynced;
  try {
    const date = new Date(lastSyncAt);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMin = Math.floor(diffMs / 60_000);
    if (diffMin < 1) return "hace un momento";
    if (diffMin < 60) return `${diffMin} min atrás`;
    const diffH = Math.floor(diffMin / 60);
    if (diffH < 24) return `${diffH}h atrás`;
    const diffD = Math.floor(diffH / 24);
    return `${diffD}d atrás`;
  } catch {
    return MARKETING_COPY.bowtie.neverSynced;
  }
}

export function MarketingActivityFooter({
  leadsAnalyzed,
  lastSyncAt,
  isLoading = false,
  className,
}: MarketingActivityFooterProps) {
  const lastSyncLabel = formatLastSync(lastSyncAt);
  const leadsCount = leadsAnalyzed ?? "—";

  return (
    <footer
      className={cn(
        "text-center text-[11px] vt-text-muted italic py-2 px-4",
        className,
      )}
      aria-live="polite"
      aria-busy={isLoading}
    >
      {isLoading ? (
        <span>{MARKETING_COPY.ui.loading}</span>
      ) : (
        <span>
          <strong className="font-semibold not-italic vt-text-azul-marino">
            Lucas
          </strong>{" "}
          analizó {leadsCount} leads · sistema sync canales c/4h · última sync{" "}
          {lastSyncLabel}
        </span>
      )}
    </footer>
  );
}

MarketingActivityFooter.displayName = "MarketingActivityFooter";
