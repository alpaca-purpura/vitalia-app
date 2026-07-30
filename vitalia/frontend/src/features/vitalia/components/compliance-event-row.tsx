// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * ComplianceEventRow — single row in the compliance audit log table.
 *
 * Exports getSeverityBadgeVariant as a named utility for testability.
 * Vitalia-specific: HIPAA-lite severity badges + event type display.
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { cn } from "@/lib/cn";
import { MICROCOPY_COMPLIANCE } from "@/features/vitalia/config/microcopy";
import type {
  ComplianceEventItem,
  ComplianceSeverity,
} from "@/features/vitalia/types/compliance.types";

export type SeverityBadgeVariant = "danger" | "warning" | "neutral";

export function getSeverityBadgeVariant(
  severity: ComplianceSeverity,
): SeverityBadgeVariant {
  switch (severity) {
    case "high":
      return "danger";
    case "medium":
      return "warning";
    case "info":
    default:
      return "neutral";
  }
}

function formatDateTime(iso: string): string {
  const d = new Date(iso);
  const year = d.getUTCFullYear();
  const month = String(d.getUTCMonth() + 1).padStart(2, "0");
  const day = String(d.getUTCDate()).padStart(2, "0");
  const hours = String(d.getUTCHours()).padStart(2, "0");
  const minutes = String(d.getUTCMinutes()).padStart(2, "0");
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

export interface ComplianceEventRowProps {
  event: ComplianceEventItem;
}

const SEVERITY_CLASSES: Record<SeverityBadgeVariant, string> = {
  danger: "bg-red-100 text-red-700 border border-red-200",
  warning: "bg-yellow-100 text-yellow-700 border border-yellow-200",
  neutral: "bg-gray-100 text-gray-600 border border-gray-200",
};

const SEVERITY_LABELS: Record<ComplianceSeverity, string> = {
  high: "Alto",
  medium: "Medio",
  info: "Info",
};

export function ComplianceEventRow({ event }: ComplianceEventRowProps) {
  const variant = getSeverityBadgeVariant(event.severity);
  const eventLabel =
    (MICROCOPY_COMPLIANCE.eventTypes as Record<string, string>)[
      event.event_type
    ] ?? event.event_type;

  return (
    <tr
      className={cn(
        "border-b border-gray-100 hover:bg-gray-50 transition-colors",
        event.severity === "high" && "bg-red-50/40",
      )}
      role="row"
    >
      {/* Date/time */}
      <td className="px-4 py-3 text-xs text-gray-500 whitespace-nowrap font-mono">
        {formatDateTime(event.created_at)}
      </td>

      {/* Event type */}
      <td
        className="px-4 py-3 text-sm text-gray-800 max-w-xs truncate"
        title={eventLabel}
      >
        {eventLabel}
      </td>

      {/* Severity badge */}
      <td className="px-4 py-3">
        <span
          className={cn(
            "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
            SEVERITY_CLASSES[variant],
          )}
          aria-label={`Severidad: ${SEVERITY_LABELS[event.severity]}`}
        >
          {SEVERITY_LABELS[event.severity]}
        </span>
      </td>

      {/* Patient ID (masked) */}
      <td className="px-4 py-3 text-xs text-gray-500 font-mono">
        {event.patient_id ? event.patient_id.slice(0, 8) + "..." : "—"}
      </td>

      {/* Actor type */}
      <td className="px-4 py-3 text-xs text-gray-500 capitalize">
        {event.actor_type ?? "—"}
      </td>
    </tr>
  );
}
