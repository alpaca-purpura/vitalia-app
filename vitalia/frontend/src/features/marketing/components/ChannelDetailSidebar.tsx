// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * ChannelDetailSidebar — slide-in panel with 3 sections:
 *   1. KPIs principales (from syncState)
 *   2. Top 3 campañas (from metrics)
 *   3. Lucas recommendations (channel-scoped)
 * External cross-link to Ads Manager: target=_blank rel="noopener noreferrer" (security)
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/cn";
import { useChannelDetail } from "../api/use-channel-detail";
import { LucasStageRecommendationsCard } from "./LucasStageRecommendationsCard";
import { MARKETING_COPY } from "../copy";
import type { ProviderSlug, ChannelMetricRow } from "../types/channel";

const PROVIDER_MANAGER_URLS: Record<ProviderSlug, string> = {
  meta_ads: "https://business.facebook.com/adsmanager",
  google_ads: "https://ads.google.com",
};

export type ChannelDetailSidebarProps = {
  open: boolean;
  provider: ProviderSlug;
  onClose: () => void;
  className?: string;
};

/**
 * ChannelDetailSidebar — detailed channel info panel.
 * Not rendered when open=false (conditional render, not hidden).
 */
export const ChannelDetailSidebar = forwardRef<
  HTMLDivElement,
  ChannelDetailSidebarProps
>(({ open, provider, onClose, className }, ref) => {
  const { data, isLoading } = useChannelDetail({ provider });

  if (!open) return null;

  const channelData = data?.[0];
  const providerName = MARKETING_COPY.channels.providers[provider];
  const managerUrl = PROVIDER_MANAGER_URLS[provider];
  const top3Campaigns = (channelData?.metrics ?? []).slice(0, 3);

  return (
    <div
      ref={ref}
      role="dialog"
      aria-modal="true"
      aria-label={providerName}
      aria-busy={isLoading}
      className={cn(
        "fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col",
        "vt-bg-surface vt-border border-l shadow-xl",
        className,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b vt-border-soft px-5 py-4">
        <div className="flex flex-col gap-0.5">
          <h2
            data-testid="sidebar-provider-title"
            className="text-base font-semibold vt-text"
          >
            {providerName}
          </h2>
          <a
            data-testid="external-manager-link"
            href={managerUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-xs vt-text-muted hover:underline"
          >
            Ir al Administrador de anuncios ↗
          </a>
        </div>
        <button
          data-testid="sidebar-close-btn"
          onClick={onClose}
          aria-label={MARKETING_COPY.ui.close}
          className="rounded-md p-1.5 vt-text-muted hover:vt-bg-surface-alt transition-colors"
        >
          <svg
            className="h-4 w-4"
            viewBox="0 0 16 16"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M3.72 3.72a.75.75 0 0 1 1.06 0L8 6.94l3.22-3.22a.75.75 0 1 1 1.06 1.06L9.06 8l3.22 3.22a.75.75 0 1 1-1.06 1.06L8 9.06l-3.22 3.22a.75.75 0 0 1-1.06-1.06L6.94 8 3.72 4.78a.75.75 0 0 1 0-1.06Z" />
          </svg>
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-5">
        {isLoading ? (
          <div
            role="status"
            aria-label={MARKETING_COPY.ui.loading}
            className="animate-pulse space-y-3"
          >
            <div className="h-20 vt-bg-surface-alt rounded-lg" />
            <div className="h-32 vt-bg-surface-alt rounded-lg" />
            <div className="h-24 vt-bg-surface-alt rounded-lg" />
          </div>
        ) : (
          <>
            {/* Section 1: KPIs from syncState */}
            {channelData?.syncState && (
              <section aria-labelledby="sidebar-kpis-heading">
                <h3
                  id="sidebar-kpis-heading"
                  className="text-xs font-semibold vt-text-muted uppercase tracking-wide mb-2"
                >
                  Estado de sincronización
                </h3>
                <div className="grid grid-cols-2 gap-2">
                  {channelData.syncState.lastSuccessAt && (
                    <div className="rounded-md vt-bg-surface-alt p-2.5 flex flex-col gap-0.5">
                      <span className="text-xs vt-text-muted">
                        {MARKETING_COPY.channels.lastSuccessLabel}
                      </span>
                      <span className="text-xs font-medium vt-text tabular-nums">
                        {new Date(
                          channelData.syncState.lastSuccessAt,
                        ).toLocaleDateString("es-419", {
                          day: "2-digit",
                          month: "short",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                  )}
                  {channelData.syncState.accountId && (
                    <div className="rounded-md vt-bg-surface-alt p-2.5 flex flex-col gap-0.5">
                      <span className="text-xs vt-text-muted">Cuenta</span>
                      <span className="text-xs font-mono vt-text">
                        {channelData.syncState.accountId}
                      </span>
                    </div>
                  )}
                </div>
                {channelData.syncState.lastError && (
                  <div className="mt-2 rounded-md border border-current/20 vt-text-danger px-3 py-2 text-xs">
                    {channelData.syncState.lastError}
                  </div>
                )}
              </section>
            )}

            {/* Section 2: Top 3 campañas */}
            <section aria-labelledby="sidebar-campaigns-heading">
              <h3
                id="sidebar-campaigns-heading"
                className="text-xs font-semibold vt-text-muted uppercase tracking-wide mb-2"
              >
                Principales campañas
              </h3>
              {top3Campaigns.length === 0 ? (
                <p
                  data-testid="no-campaigns-message"
                  className="text-xs vt-text-muted italic"
                >
                  {MARKETING_COPY.channels.noMetrics}
                </p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {top3Campaigns.map((campaign: ChannelMetricRow) => (
                    <li
                      key={
                        campaign.campaignId ??
                        campaign.campaignName ??
                        campaign.metricDate
                      }
                      className="rounded-md vt-bg-surface-alt px-3 py-2.5"
                    >
                      <div className="text-xs font-medium vt-text truncate">
                        {campaign.campaignName ?? "—"}
                      </div>
                      <div className="mt-1 flex gap-3 text-xs vt-text-muted tabular-nums">
                        {campaign.impressions !== null && (
                          <span>
                            {campaign.impressions.toLocaleString("es-419")}{" "}
                            impresiones
                          </span>
                        )}
                        {campaign.clicks !== null && (
                          <span>
                            {campaign.clicks.toLocaleString("es-419")} clics
                          </span>
                        )}
                        {campaign.conversions !== null && (
                          <span>{campaign.conversions} conv.</span>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {/* Section 3: Lucas recommendations — channel-scoped */}
            <section aria-labelledby="sidebar-lucas-heading">
              <h3
                id="sidebar-lucas-heading"
                className="text-xs font-semibold vt-text-muted uppercase tracking-wide mb-2"
              >
                Recomendaciones
              </h3>
              <LucasStageRecommendationsCard stage="attraction" />
            </section>
          </>
        )}
      </div>
    </div>
  );
});
ChannelDetailSidebar.displayName = "ChannelDetailSidebar";
