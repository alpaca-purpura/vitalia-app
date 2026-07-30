// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * ChannelBreakdownRow — per-provider row in AttractionStage channel breakdown.
 * Renders sync state badge + last metrics timestamp + retry button on error.
 * On click → opens ChannelDetailSidebar.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { forwardRef, useState } from "react";
import { cn } from "@/lib/cn";
import { useChannelDetail } from "../api/use-channel-detail";
import { useSyncChannel } from "../api/use-sync-channel";
import { ConnectionBadge } from "./ConnectionBadge";
import { ChannelDetailSidebar } from "./ChannelDetailSidebar";
import { MARKETING_COPY } from "../copy";
import type { ProviderSlug } from "../types/channel";

export type ChannelBreakdownRowProps = {
  provider: ProviderSlug;
  className?: string;
};

/**
 * ChannelBreakdownRow — renders one provider row in the channel breakdown table.
 * Shows connection badge, last success timestamp, and retry button when in error state.
 * Click row → opens ChannelDetailSidebar.
 */
export const ChannelBreakdownRow = forwardRef<
  HTMLDivElement,
  ChannelBreakdownRowProps
>(({ provider, className }, ref) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { data, isLoading } = useChannelDetail({ provider });
  const { mutate: syncChannel, isPending: isSyncing } = useSyncChannel();

  const providerName = MARKETING_COPY.channels.providers[provider];
  const channelData = data?.[0];
  const syncState = channelData?.syncState;
  const status = syncState?.status ?? "disconnected";
  const isError = status === "error" || status === "disconnected";

  if (isLoading) {
    return (
      <div
        ref={ref}
        className={cn("px-4 py-3 flex items-center gap-3", className)}
        aria-busy={true}
      >
        <div
          role="status"
          aria-label={MARKETING_COPY.ui.loading}
          className="animate-pulse flex items-center gap-3 w-full"
        >
          <div className="h-4 w-24 vt-bg-surface-alt rounded" />
          <div className="h-4 w-16 vt-bg-surface-alt rounded ml-auto" />
        </div>
      </div>
    );
  }

  return (
    <>
      <div
        ref={ref}
        data-testid={`channel-row-${provider}`}
        role="button"
        tabIndex={0}
        onClick={() => setSidebarOpen(true)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setSidebarOpen(true);
          }
        }}
        className={cn(
          "px-4 py-3 flex items-center gap-3 cursor-pointer",
          "hover:vt-bg-surface-alt transition-colors",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-current",
          className,
        )}
        aria-label={`Ver detalles de ${providerName}`}
      >
        {/* Provider name */}
        <span className="text-sm font-medium vt-text flex-1 truncate">
          {providerName}
        </span>

        {/* Last success timestamp — shown even in error state (last known data) */}
        {syncState?.lastSuccessAt && (
          <span
            data-testid="last-success-timestamp"
            className="text-xs vt-text-muted tabular-nums hidden sm:inline"
          >
            {new Date(syncState.lastSuccessAt).toLocaleDateString("es-419", {
              day: "2-digit",
              month: "short",
              hour: "2-digit",
              minute: "2-digit",
            })}
          </span>
        )}

        {/* Connection badge */}
        <ConnectionBadge status={status} />

        {/* Retry button — only shown in error/disconnected state */}
        {isError && (
          <button
            data-testid="retry-sync-btn"
            onClick={(e) => {
              e.stopPropagation(); // prevent row click from opening sidebar
              syncChannel({ provider });
            }}
            disabled={isSyncing}
            aria-label={`${MARKETING_COPY.ui.retry} ${providerName}`}
            className={cn(
              "rounded-md px-2 py-1 text-xs font-medium",
              "vt-bg-surface-alt hover:vt-bg-surface vt-border border",
              "vt-text-muted hover:vt-text transition-colors",
              "disabled:opacity-50 disabled:cursor-not-allowed",
            )}
          >
            {isSyncing
              ? MARKETING_COPY.channels.syncingLabel
              : MARKETING_COPY.ui.retry}
          </button>
        )}

        {/* Chevron icon */}
        <svg
          className="h-4 w-4 vt-text-muted flex-shrink-0"
          viewBox="0 0 16 16"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M6.22 4.22a.75.75 0 0 1 1.06 0l3.25 3.25a.75.75 0 0 1 0 1.06l-3.25 3.25a.75.75 0 0 1-1.06-1.06L9.19 8 6.22 5.03a.75.75 0 0 1 0-1.06Z"
            clipRule="evenodd"
          />
        </svg>
      </div>

      {/* Detail sidebar — opened on row click */}
      <ChannelDetailSidebar
        open={sidebarOpen}
        provider={provider}
        onClose={() => setSidebarOpen(false)}
      />
    </>
  );
});
ChannelBreakdownRow.displayName = "ChannelBreakdownRow";
