// cap: sales_agent.inbox-handler-mode-occ
// story-origin: vitalia-fase1-s10-TBD
/**
 * CampaignTag — pill clickable molécula inbox.
 * F1-S10 vitalia-fase1-empty-states — T-5
 *
 * Renders: pill "📣 {campaignName}" (truncate >30 chars with tooltip full name).
 * Click → navigates to /{tenantId}/lucas/lanzar?campaign={campaignId}.
 * F1: navigation DISABLED (no router.push — visual only, per spec F1 scope).
 * F2: enable via prop `href` or `onNavigate` callback wiring Link.
 *
 * Mockup parity: adrian-inbox-placeholder.html .campaign-tag styles
 *   bg-agent-lisa-soft / text-agent-lisa / border-agent-lisa
 *
 * Client Component — uses title tooltip, NO router in F1 (purely presentational).
 * Named export (NO default) per FSD-Lite enforce.
 * No hex colors — Tailwind semantic tokens only.
 *
 * spec_anchor: 03-arch.md § 3.3 + 06-tickets.yaml T-5
 * downstream-regression-na: brand-local vitalia inbox; no cross-brand consumers
 */

import { cn } from "@/lib/utils";

/** Maximum visible characters before truncation */
const MAX_DISPLAY_CHARS = 30;

export interface CampaignTagProps {
  campaignId: string;
  campaignName: string;
  /** Display variant — 'list' (compact, badges row) | 'detail' (sidebar, slightly larger) */
  variant?: "list" | "detail";
  className?: string;
}

/**
 * CampaignTag — clickable pill with campaign name.
 * F1 disabled navigation; F2 wire router.push.
 */
export function CampaignTag({
  campaignId: _campaignId,
  campaignName,
  variant = "list",
  className,
}: CampaignTagProps) {
  const displayName =
    campaignName.length > MAX_DISPLAY_CHARS
      ? `${campaignName.slice(0, MAX_DISPLAY_CHARS)}…`
      : campaignName;

  const isTruncated = campaignName.length > MAX_DISPLAY_CHARS;

  return (
    <span
      role="button"
      tabIndex={0}
      aria-label={`Campaña: ${campaignName}`}
      title={isTruncated ? campaignName : undefined}
      className={cn(
        // Base pill styles — mockup parity
        "inline-flex cursor-pointer select-none items-center rounded-full border font-medium",
        "bg-agent-lisa-soft text-agent-lisa border-agent-lisa",
        "hover:opacity-85 transition-opacity",
        // Variant sizing
        variant === "list" ? "px-2 py-0.5 text-[10px]" : "px-2.5 py-1 text-xs",
        className,
      )}
      // F1: no onClick — decorative navigation placeholder
      // F2-S3: onClick={() => router.push(`/${tenantId}/lucas/lanzar?campaign=${campaignId}`)}
      onKeyDown={(e) => {
        // F1: noop. F2: trigger navigation on Enter/Space.
        void e;
      }}
    >
      {/* Decorative icon */}
      <span aria-hidden="true" className="mr-1">
        📣
      </span>
      {displayName}
    </span>
  );
}
