// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * ReferralsWidget — 3 KPI hero cards + top 5 referrer leaderboard.
 * HIPAA-lite: leaderboard shows ONLY referrerPatientIdHash — NEVER patient.name.
 * Consumes useReferrals (dual filter tenant+clinic via hook).
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/cn";
import { useReferrals } from "../api/use-referrals";
import { MARKETING_COPY } from "../copy";
import { useTenantLocale } from "@/hooks/useTenantLocale";

export type ReferralsWidgetProps = {
  period?: "7d" | "30d" | "90d";
  className?: string;
};

function formatPct(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

function formatMoney(cents: number | null, currency: string): string {
  if (cents === null) return "—";
  const amount = cents / 100;
  try {
    return new Intl.NumberFormat("es-419", {
      style: "currency",
      currency,
      minimumFractionDigits: 0,
    }).format(amount);
  } catch {
    return `${currency} ${amount.toLocaleString()}`;
  }
}

/**
 * KPI hero card — displays a single metric with label + value
 */
function KpiHeroCard({
  label,
  value,
  className,
}: {
  label: string;
  value: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "rounded-lg vt-bg-surface-alt border vt-border-soft p-3 flex flex-col gap-1",
        className,
      )}
    >
      <span className="text-xs vt-text-muted">{label}</span>
      <span className="text-lg font-semibold vt-text tabular-nums">
        {value}
      </span>
    </div>
  );
}

/**
 * ReferralsWidget — HIPAA-compliant referrals leaderboard + KPI heroes
 */
export const ReferralsWidget = forwardRef<HTMLDivElement, ReferralsWidgetProps>(
  ({ period = "30d", className }, ref) => {
    const { data, isLoading, isError } = useReferrals({ period });
    const locale = useTenantLocale();

    if (isLoading) {
      return (
        <div
          ref={ref}
          role="status"
          aria-label={MARKETING_COPY.referrals.loadingMessage}
          aria-busy={true}
          className={cn(
            "rounded-lg vt-bg-surface vt-border border p-4",
            className,
          )}
        >
          <div className="animate-pulse space-y-3">
            <div className="h-4 vt-bg-surface-alt rounded w-32" />
            <div className="grid grid-cols-3 gap-3">
              <div className="h-16 vt-bg-surface-alt rounded" />
              <div className="h-16 vt-bg-surface-alt rounded" />
              <div className="h-16 vt-bg-surface-alt rounded" />
            </div>
            <div className="h-3 vt-bg-surface-alt rounded w-full" />
            <div className="h-3 vt-bg-surface-alt rounded w-full" />
          </div>
        </div>
      );
    }

    if (isError) {
      return (
        <div
          ref={ref}
          role="alert"
          className={cn(
            "rounded-lg vt-bg-surface vt-border border p-4",
            className,
          )}
        >
          <p className="text-sm vt-text-danger">
            {MARKETING_COPY.referrals.errorMessage}
          </p>
        </div>
      );
    }

    if (!data || data.referralsCount === 0) {
      return (
        <div
          ref={ref}
          className={cn(
            "rounded-lg vt-bg-surface vt-border border p-4",
            className,
          )}
        >
          <p className="text-sm vt-text-muted italic">
            {MARKETING_COPY.referrals.emptyMessage}
          </p>
        </div>
      );
    }

    const currency = data.currency ?? locale.currency;

    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg vt-bg-surface vt-border border overflow-hidden",
          className,
        )}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b vt-border-soft">
          <h3 className="text-sm font-semibold vt-text">
            {MARKETING_COPY.referrals.title}
          </h3>
          <p className="text-xs vt-text-muted mt-0.5">
            {MARKETING_COPY.referrals.subtitle}
          </p>
        </div>

        <div className="p-4 space-y-4">
          {/* 3 KPI hero cards */}
          <div className="grid grid-cols-3 gap-3">
            <KpiHeroCard
              label={MARKETING_COPY.referrals.totalReferrals}
              value={String(data.referralsCount)}
            />
            <KpiHeroCard
              label={MARKETING_COPY.referrals.convRateLabel}
              value={formatPct(data.convRate)}
            />
            <KpiHeroCard
              label={MARKETING_COPY.referrals.avgLtvLabel}
              value={formatMoney(data.avgLtvPerReferrerCents, currency)}
            />
          </div>

          {/* Top referrers leaderboard */}
          {data.topReferrers.length > 0 && (
            <div>
              <h4 className="text-xs font-semibold vt-text mb-2">
                {MARKETING_COPY.referrals.topReferrersTitle}
              </h4>
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b vt-border-soft">
                    <th
                      scope="col"
                      className="text-left py-1.5 pr-3 font-medium vt-text-muted"
                    >
                      {/* HIPAA: anonymized ID label per phi_fields.py */}
                      {MARKETING_COPY.referrals.referrerLabel}
                    </th>
                    <th
                      scope="col"
                      className="text-right py-1.5 pr-3 font-medium vt-text-muted"
                    >
                      {MARKETING_COPY.referrals.referralsCountLabel}
                    </th>
                    <th
                      scope="col"
                      className="text-right py-1.5 font-medium vt-text-muted"
                    >
                      {MARKETING_COPY.referrals.totalValueLabel}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {data.topReferrers.slice(0, 5).map((referrer, index) => (
                    <tr
                      key={referrer.referrerPatientIdHash}
                      className="border-b vt-border-soft last:border-b-0"
                    >
                      <td className="py-1.5 pr-3 font-mono text-xs vt-text">
                        {/* HIPAA: hash only, NEVER patient.name per phi_fields.py */}
                        <span aria-label={`Referidor ${index + 1}`}>
                          {referrer.referrerPatientIdHash}
                        </span>
                      </td>
                      <td className="py-1.5 pr-3 text-right tabular-nums vt-text">
                        {referrer.referralsCount}
                      </td>
                      <td className="py-1.5 text-right tabular-nums vt-text">
                        {formatMoney(referrer.totalValueCents, currency)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    );
  },
);
ReferralsWidget.displayName = "ReferralsWidget";
