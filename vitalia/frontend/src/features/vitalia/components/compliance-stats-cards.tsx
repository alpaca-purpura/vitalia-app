// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * ComplianceStatsCards — HIPAA-lite metrics cards for /medical-compliance page.
 *
 * Vitalia-specific: HIPAA-lite metrics aggregation, medical-vertical specific.
 * Justification: spec § 6.3.5 anti-duplication.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { cn } from "@/lib/cn";
import { MICROCOPY_COMPLIANCE } from "@/features/vitalia/config/microcopy";
import type {
  ComplianceSeverity,
  ComplianceEventItem,
} from "@/features/vitalia/types/compliance.types";

export interface ComplianceStatsCardsProps {
  events: ComplianceEventItem[];
  isLoading?: boolean;
  className?: string;
}

interface StatCard {
  label: string;
  value: number;
  variant: "neutral" | "warning" | "danger";
}

function countBySeverity(
  events: ComplianceEventItem[],
  severity: ComplianceSeverity,
): number {
  return events.filter((e) => e.severity === severity).length;
}

function StatCardItem({
  label,
  value,
  variant,
  isLoading,
}: StatCard & { isLoading?: boolean }) {
  const variantClasses: Record<StatCard["variant"], string> = {
    neutral: "border-gray-200 bg-white",
    warning: "border-yellow-200 bg-yellow-50",
    danger: "border-red-200 bg-red-50",
  };
  const valueClasses: Record<StatCard["variant"], string> = {
    neutral: "text-gray-900",
    warning: "text-yellow-700",
    danger: "text-red-700",
  };

  return (
    <div
      className={cn(
        "rounded-lg border p-4 flex flex-col gap-1",
        variantClasses[variant],
      )}
      role="status"
      aria-label={`${label}: ${isLoading ? "Cargando" : value}`}
      aria-busy={isLoading}
    >
      <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">
        {label}
      </span>
      {isLoading ? (
        <div
          className="h-8 w-16 rounded bg-gray-200 animate-pulse"
          aria-hidden="true"
        />
      ) : (
        <span className={cn("text-3xl font-bold", valueClasses[variant])}>
          {value}
        </span>
      )}
    </div>
  );
}

export function ComplianceStatsCards({
  events,
  isLoading = false,
  className,
}: ComplianceStatsCardsProps) {
  const totalEvents = events.length;
  const criticalEvents = countBySeverity(events, "high");
  const blockedEvents = events.filter((e) =>
    ["prompt_injection_blocked", "cross_tenant_blocked"].some((t) =>
      e.event_type.includes(t),
    ),
  ).length;

  const stats: StatCard[] = [
    {
      label: MICROCOPY_COMPLIANCE.stats.totalEvents,
      value: totalEvents,
      variant: "neutral",
    },
    {
      label: MICROCOPY_COMPLIANCE.stats.critical,
      value: criticalEvents,
      variant: criticalEvents > 0 ? "danger" : "neutral",
    },
    {
      label: MICROCOPY_COMPLIANCE.stats.blocked,
      value: blockedEvents,
      variant: blockedEvents > 0 ? "warning" : "neutral",
    },
  ];

  return (
    <section
      className={cn("space-y-4", className)}
      aria-label={MICROCOPY_COMPLIANCE.title}
    >
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">
            {MICROCOPY_COMPLIANCE.title}
          </h2>
          <p className="text-sm text-gray-500">
            {MICROCOPY_COMPLIANCE.subtitle}
          </p>
        </div>
      </div>

      {/* Stats grid */}
      <div
        className="grid grid-cols-3 gap-4"
        role="region"
        aria-label="Estadísticas de cumplimiento"
      >
        {stats.map((stat) => (
          <StatCardItem key={stat.label} {...stat} isLoading={isLoading} />
        ))}
      </div>

      {/* Event type breakdown */}
      {!isLoading && events.length > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-2">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">
            Tipos de evento
          </h3>
          {Object.entries(MICROCOPY_COMPLIANCE.eventTypes).map(
            ([key, label]) => {
              const count = events.filter(
                (e) => e.event_type === key || e.event_type.includes(key),
              ).length;
              const pct =
                totalEvents > 0 ? Math.round((count / totalEvents) * 100) : 0;
              return (
                <div key={key} className="flex items-center gap-2">
                  <span className="text-xs text-gray-600 flex-1 truncate">
                    {label}
                  </span>
                  <span className="text-xs font-medium text-gray-900 w-8 text-right">
                    {count}
                  </span>
                  <div
                    className="w-24 h-1.5 bg-gray-100 rounded-full overflow-hidden"
                    aria-hidden="true"
                  >
                    <div
                      className="h-full bg-blue-500 rounded-full transition-all"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            },
          )}
        </div>
      )}

      {!isLoading && events.length === 0 && (
        <div className="rounded-lg border border-dashed border-gray-200 p-8 text-center">
          <p className="text-sm text-gray-500">
            Sin eventos de cumplimiento registrados.
          </p>
        </div>
      )}
    </section>
  );
}
