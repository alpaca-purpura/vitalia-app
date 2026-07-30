// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * AttributionMatrixWidget — 4 origins × KPI columns heatmap table with conversion rate coloring.
 * Consumes useAttributionMatrix (HIPAA-lite: dual filter tenant+clinic, no PHI).
 * A11y: semantic <table> with column headers + aria-label per data cell.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { forwardRef } from "react";
import { cn } from "@/lib/cn";
import { useAttributionMatrix } from "../api/use-attribution-matrix";
import { MARKETING_COPY } from "../copy";
import type { AttributionOriginRow } from "../types/attribution";

export type AttributionMatrixWidgetProps = {
  period?: "7d" | "30d" | "90d";
  className?: string;
};

/** Returns Tailwind utility class based on conversion rate 0–1 range */
function convRateColorClass(rate: number): string {
  if (rate >= 0.4) return "vt-text-success font-semibold";
  if (rate >= 0.2) return "vt-text-warning";
  return "vt-text-danger";
}

type KpiColumn = {
  key: keyof Omit<AttributionOriginRow, "origin" | "valueCents">;
  label: string;
  isConvRate: boolean;
  denominator?: keyof Omit<AttributionOriginRow, "origin" | "valueCents">;
};

const KPI_COLUMNS: KpiColumn[] = [
  {
    key: "leads",
    label: MARKETING_COPY.attribution.leadsLabel,
    isConvRate: false,
  },
  {
    key: "qualified",
    label: MARKETING_COPY.attribution.qualifiedLabel,
    isConvRate: true,
    denominator: "leads",
  },
  {
    key: "convListo",
    label: MARKETING_COPY.attribution.convListoLabel,
    isConvRate: true,
    denominator: "qualified",
  },
  {
    key: "reservations",
    label: MARKETING_COPY.attribution.reservationsLabel,
    isConvRate: true,
    denominator: "convListo",
  },
  {
    key: "adoption",
    label: MARKETING_COPY.attribution.adoptionLabel,
    isConvRate: true,
    denominator: "reservations",
  },
];

function getRate(row: AttributionOriginRow, col: KpiColumn): number {
  if (!col.isConvRate || !col.denominator) return 0;
  const num = row[col.key] as number;
  const den = row[col.denominator] as number;
  if (!den) return 0;
  return num / den;
}

function formatPct(rate: number): string {
  return `${Math.round(rate * 100)}%`;
}

type RowData = {
  label: string;
  row: AttributionOriginRow;
  isTotal: boolean;
};

/**
 * AttributionMatrixWidget — semantic table heatmap
 */
export const AttributionMatrixWidget = forwardRef<
  HTMLDivElement,
  AttributionMatrixWidgetProps
>(({ period = "30d", className }, ref) => {
  const { data, isLoading, isError } = useAttributionMatrix({ period });

  if (isLoading) {
    return (
      <div
        ref={ref}
        role="status"
        aria-label={MARKETING_COPY.attribution.loadingMessage}
        aria-busy={true}
        className={cn(
          "rounded-lg vt-bg-surface vt-border border p-4",
          className,
        )}
      >
        <div className="animate-pulse space-y-3">
          <div className="h-4 vt-bg-surface-alt rounded w-48" />
          <div className="h-3 vt-bg-surface-alt rounded w-full" />
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
          {MARKETING_COPY.attribution.errorMessage}
        </p>
      </div>
    );
  }

  if (!data) {
    return (
      <div
        ref={ref}
        className={cn(
          "rounded-lg vt-bg-surface vt-border border p-4",
          className,
        )}
      >
        <p className="text-sm vt-text-muted italic">
          {MARKETING_COPY.attribution.emptyMessage}
        </p>
      </div>
    );
  }

  const originLabelMap = MARKETING_COPY.attribution.origins;
  const rows: RowData[] = [
    ...data.origins.map((row) => ({
      label:
        originLabelMap[row.origin as keyof typeof originLabelMap] ?? row.origin,
      row,
      isTotal: false,
    })),
    {
      label: originLabelMap.total,
      row: data.totals,
      isTotal: true,
    },
  ];

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
          {MARKETING_COPY.attribution.title}
        </h3>
        <p className="text-xs vt-text-muted mt-0.5">
          {MARKETING_COPY.attribution.subtitle}
        </p>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="vt-bg-surface-alt border-b vt-border-soft">
              <th
                scope="col"
                className="px-4 py-2 text-left font-medium vt-text-muted"
              >
                {MARKETING_COPY.attribution.originLabel}
              </th>
              {KPI_COLUMNS.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className="px-3 py-2 text-right font-medium vt-text-muted whitespace-nowrap"
                >
                  {col.label}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map(({ label, row, isTotal }) => (
              <tr
                key={row.origin}
                className={cn(
                  "border-b vt-border-soft last:border-b-0 hover:vt-bg-surface-alt transition-colors",
                  isTotal && "vt-bg-surface-alt font-medium",
                )}
              >
                <td className="px-4 py-2 vt-text whitespace-nowrap">{label}</td>
                {KPI_COLUMNS.map((col) => {
                  const rawValue = row[col.key] as number;
                  const rate = getRate(row, col);
                  const colorClass = col.isConvRate
                    ? convRateColorClass(rate)
                    : "vt-text";
                  const displayValue = col.isConvRate
                    ? `${rawValue} (${formatPct(rate)})`
                    : String(rawValue);
                  const ariaLabel = `${label}, ${col.label}: ${displayValue}`;

                  return (
                    <td
                      key={col.key}
                      className={cn(
                        "px-3 py-2 text-right tabular-nums",
                        colorClass,
                      )}
                      aria-label={ariaLabel}
                    >
                      {displayValue}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Top insight from Lucas */}
      {data.topInsightText && (
        <div className="px-4 py-3 border-t vt-border-soft vt-bg-surface-alt">
          <p className="text-xs vt-text-muted">
            <span className="font-semibold vt-text">Lucas: </span>
            {data.topInsightText}
          </p>
        </div>
      )}
    </div>
  );
});
AttributionMatrixWidget.displayName = "AttributionMatrixWidget";
