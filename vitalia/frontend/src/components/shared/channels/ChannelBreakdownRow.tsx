// cap: marketing.attribution-matrix-4-origins
// story-origin: TBD
/**
 * ChannelBreakdownRow — single channel performance row widget.
 *
 * Scaffold stub. Full implementation (with real analytics data hooks)
 * arrives in growth-studio story (Slice 2+).
 *
 * Per design-system.md: no hsl literals in TSX. All colors via vt-* classes.
 */

import { cn } from "@/lib/cn";

export interface ChannelBreakdownRowProps {
  /** Channel slug (e.g. "instagram-organic", "google-ads") */
  channelSlug: string;
  /** Channel display name */
  channelName: string;
  /** Primary metric value */
  primaryValue: number;
  /** Primary metric label (e.g. "impresiones", "clics") */
  primaryLabel: string;
  /** Secondary metric value (optional) */
  secondaryValue?: number;
  /** Secondary metric label */
  secondaryLabel?: string;
  /** Change percentage vs previous period (e.g. +12.5 or -3.2) */
  changePct?: number;
  /** Whether this row is loading */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Single channel row in a breakdown table.
 * Shows channel name + primary metric + optional secondary metric + change indicator.
 */
export function ChannelBreakdownRow({
  channelSlug,
  channelName,
  primaryValue,
  primaryLabel,
  secondaryValue,
  secondaryLabel,
  changePct,
  isLoading = false,
  className,
}: ChannelBreakdownRowProps) {
  const isPositive = changePct !== undefined && changePct >= 0;
  const isNegative = changePct !== undefined && changePct < 0;

  return (
    <div
      className={cn(
        "flex items-center gap-3 py-3 px-4",
        "border-b vt-border-soft last:border-b-0",
        className,
      )}
      aria-label={`Canal: ${channelName}`}
      aria-busy={isLoading}
      data-channel-slug={channelSlug}
    >
      {/* Channel name */}
      <span className="flex-1 text-sm font-medium vt-text truncate">
        {channelName}
      </span>

      {/* Primary metric */}
      <div className="text-right min-w-[80px]">
        <span className="text-sm font-semibold vt-text tabular-nums">
          {isLoading ? "—" : primaryValue.toLocaleString("es-419")}
        </span>
        <span className="block text-xs vt-text-faint">{primaryLabel}</span>
      </div>

      {/* Secondary metric */}
      {secondaryLabel && (
        <div className="text-right min-w-[70px]">
          <span className="text-sm vt-text-muted tabular-nums">
            {isLoading ? "—" : (secondaryValue ?? 0).toLocaleString("es-419")}
          </span>
          <span className="block text-xs vt-text-faint">{secondaryLabel}</span>
        </div>
      )}

      {/* Change indicator */}
      {changePct !== undefined && (
        <span
          className={cn(
            "text-xs font-medium min-w-[52px] text-right tabular-nums",
            isPositive && "vt-text-success",
            isNegative && "vt-text-danger",
            !isPositive && !isNegative && "vt-text-muted",
          )}
          aria-label={`Cambio: ${isPositive ? "+" : ""}${changePct.toFixed(1)}%`}
        >
          {isPositive && "+"}
          {changePct.toFixed(1)}%
        </span>
      )}
    </div>
  );
}
