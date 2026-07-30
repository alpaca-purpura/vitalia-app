// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * CompliancePageClient — HIPAA-lite compliance audit log dashboard.
 *
 * Renders: ComplianceStatsCards + event type breakdown + filter bar +
 * scrollable event table + CSV export CTA.
 *
 * Exports generateCsvBlob as named utility for testability.
 * Vitalia-specific: HIPAA-lite audit log, medical-vertical specific.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { useState, useCallback } from "react";
import { cn } from "@/lib/cn";
import { MICROCOPY_COMPLIANCE } from "@/features/vitalia/config/microcopy";
import { useComplianceEvents } from "@/features/vitalia/api/use-compliance-events";
import { ComplianceStatsCards } from "@/features/vitalia/components/compliance-stats-cards";
import { ComplianceEventRow } from "@/features/vitalia/components/compliance-event-row";
import type {
  ComplianceEventItem,
  ComplianceSeverity,
} from "@/features/vitalia/types/compliance.types";

// ── CSV export utility (exported for testability) ─────────────────────────────

const CSV_HEADERS = [
  "Fecha",
  "Tipo de evento",
  "Severidad",
  "Paciente ID",
  "Actor",
  "Booking ID",
];

function escapeCsv(value: string): string {
  if (value.includes(",") || value.includes('"') || value.includes("\n")) {
    return `"${value.replace(/"/g, '""')}"`;
  }
  return value;
}

export function generateCsvBlob(events: ComplianceEventItem[]): Blob {
  const rows: string[] = [CSV_HEADERS.map(escapeCsv).join(",")];

  for (const evt of events) {
    const row = [
      evt.created_at,
      evt.event_type,
      evt.severity,
      evt.patient_id ?? "",
      evt.actor_type ?? "",
      evt.booking_id ?? "",
    ]
      .map((v) => escapeCsv(String(v)))
      .join(",");
    rows.push(row);
  }

  return new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8;" });
}

// ── Filter types ──────────────────────────────────────────────────────────────

type SeverityFilter = "all" | ComplianceSeverity;
type EventTypeFilter = "all" | string;

// ── Main component ────────────────────────────────────────────────────────────

export interface CompliancePageClientProps {
  className?: string;
}

type ExportState = "idle" | "preparing" | "ready";

export function CompliancePageClient({ className }: CompliancePageClientProps) {
  const [severityFilter, setSeverityFilter] = useState<SeverityFilter>("all");
  const [eventTypeFilter, setEventTypeFilter] =
    useState<EventTypeFilter>("all");
  const [exportState, setExportState] = useState<ExportState>("idle");

  const { data, isLoading, isError } = useComplianceEvents({
    severity: severityFilter !== "all" ? severityFilter : undefined,
    event_type: eventTypeFilter !== "all" ? eventTypeFilter : undefined,
  });

  const events = data?.events ?? [];

  const handleExportCsv = useCallback(() => {
    setExportState("preparing");
    try {
      const blob = generateCsvBlob(events);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `compliance-audit-${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      setExportState("ready");
      setTimeout(() => setExportState("idle"), 3000);
    } catch {
      setExportState("idle");
    }
  }, [events]);

  if (isError) {
    return (
      <div
        className={cn(
          "rounded-lg border border-red-200 bg-red-50 p-6 text-center",
          className,
        )}
        role="alert"
        aria-live="polite"
      >
        <p className="text-sm text-red-700">
          Error al cargar eventos de cumplimiento. Intenta recargar la página.
        </p>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-6", className)}>
      {/* Stats cards */}
      <ComplianceStatsCards events={events} isLoading={isLoading} />

      {/* Filter bar */}
      <div
        className="flex flex-wrap items-center gap-3"
        role="group"
        aria-label="Filtros de cumplimiento"
      >
        {/* Tipo filter */}
        <div className="flex flex-col gap-1">
          <label
            htmlFor="filter-event-type"
            className="text-xs font-medium text-gray-600 uppercase tracking-wide"
          >
            Tipo
          </label>
          <select
            id="filter-event-type"
            value={eventTypeFilter}
            onChange={(e) => setEventTypeFilter(e.target.value)}
            className="rounded-md border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Filtrar por tipo de evento"
          >
            <option value="all">Todos los tipos</option>
            {Object.entries(MICROCOPY_COMPLIANCE.eventTypes).map(
              ([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ),
            )}
          </select>
        </div>

        {/* Severidad filter */}
        <div className="flex flex-col gap-1">
          <label
            htmlFor="filter-severity"
            className="text-xs font-medium text-gray-600 uppercase tracking-wide"
          >
            Severidad
          </label>
          <select
            id="filter-severity"
            value={severityFilter}
            onChange={(e) =>
              setSeverityFilter(e.target.value as SeverityFilter)
            }
            className="rounded-md border border-gray-200 bg-white px-3 py-1.5 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Filtrar por severidad"
          >
            <option value="all">Todas</option>
            <option value="high">Alto</option>
            <option value="medium">Medio</option>
            <option value="info">Info</option>
          </select>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* CSV export CTA */}
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium text-gray-600 uppercase tracking-wide invisible">
            Exportar
          </span>
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={
              isLoading || exportState === "preparing" || events.length === 0
            }
            className={cn(
              "rounded-md border px-4 py-1.5 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500",
              exportState === "ready"
                ? "border-green-300 bg-green-50 text-green-700"
                : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed",
            )}
            aria-busy={exportState === "preparing"}
            aria-label={
              exportState === "preparing"
                ? MICROCOPY_COMPLIANCE.export.preparing
                : exportState === "ready"
                  ? MICROCOPY_COMPLIANCE.export.ready
                  : MICROCOPY_COMPLIANCE.export.cta
            }
          >
            {exportState === "preparing"
              ? MICROCOPY_COMPLIANCE.export.preparing
              : exportState === "ready"
                ? MICROCOPY_COMPLIANCE.export.ready
                : MICROCOPY_COMPLIANCE.export.cta}
          </button>
        </div>
      </div>

      {/* Event table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        {isLoading ? (
          <div
            className="p-8 text-center"
            role="status"
            aria-live="polite"
            aria-busy={true}
          >
            <div
              className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600"
              aria-hidden="true"
            />
            <p className="mt-2 text-sm text-gray-500">Cargando eventos...</p>
          </div>
        ) : events.length === 0 ? (
          <div className="p-8 text-center border-dashed" role="status">
            <p className="text-sm text-gray-500">
              Sin eventos de cumplimiento para los filtros seleccionados.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table
              className="w-full text-left text-sm"
              aria-label={MICROCOPY_COMPLIANCE.subtitle}
            >
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr role="row">
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Fecha
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Tipo
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Severidad
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Paciente
                  </th>
                  <th className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                    Actor
                  </th>
                </tr>
              </thead>
              <tbody role="rowgroup">
                {events.map((event) => (
                  <ComplianceEventRow key={event.id} event={event} />
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Total count */}
      {!isLoading && data && data.total > 0 && (
        <p className="text-xs text-gray-400 text-right">
          {data.total} evento{data.total !== 1 ? "s" : ""} en total
        </p>
      )}
    </div>
  );
}
