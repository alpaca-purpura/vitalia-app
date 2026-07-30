// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AppointmentDrawerNotasSection.tsx — "Notas" accordion section for AppointmentDrawer.
 * T-14 vitalia-fase2-valeria-agenda
 *
 * Renders:
 *   - Staff notes textarea (internal-only, NO clinical PHI per HIPAA-lite)
 *   - Last activity timestamp + actor label
 *
 * Notes are internal staff notes only — no clinical diagnoses, treatment plans,
 * or patient health data. PHI constraint: DO NOT use this for medical records.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.6 + 06-tickets.yaml T-14
 */

import { Clock } from "lucide-react";
import { Textarea } from "@/components/ui/textarea";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { formatTenantDate } from "@/lib/format/formatTenantDate";
import type { Appointment } from "../../types/agenda.types";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AppointmentDrawerNotasSectionProps {
  /** Full appointment detail from useAppointmentDetail. */
  appointment: Appointment;
  /** Callback when notes textarea blurs with changed content. */
  onNotesChange?: (notes: string) => void;
  /** Whether notes save mutation is in flight. */
  isSavingNotes?: boolean;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Formats ISO 8601 to relative time string (e.g., "Hace 5 min", "Hace 2 h").
 * Falls back to formatTenantDate for older entries (F2 master-data fix).
 */
function formatRelativeTime(isoString: string, timezone: string, locale: string): string {
  const date = new Date(isoString);
  const now = Date.now();
  const diffMs = now - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHours = Math.floor(diffMin / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMin < 1) return "Ahora mismo";
  if (diffMin < 60) return `Hace ${diffMin} min`;
  if (diffHours < 24) return `Hace ${diffHours} h`;
  if (diffDays < 7) return `Hace ${diffDays} días`;

  return formatTenantDate(isoString, timezone, locale);
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Notas section — staff internal notes textarea + last activity indicator.
 *
 * HIPAA-lite: this field is for operational notes only (e.g., "paciente llega tarde").
 * Clinical information belongs in the patient record — not here.
 */
export function AppointmentDrawerNotasSection({
  appointment,
  onNotesChange,
  isSavingNotes = false,
}: AppointmentDrawerNotasSectionProps) {
  const { timezone, locale } = useTenantLocale();

  return (
    <div
      className="flex flex-col gap-4"
      data-testid="notas-section"
    >
      {/* Staff notes — internal only, NO PHI */}
      <div className="flex flex-col gap-1.5">
        <label
          htmlFor="notes-internal"
          className="text-xs font-medium text-muted-foreground"
        >
          Notas internas del personal
          <span className="ml-1 font-normal">(solo personal clínico)</span>
        </label>
        <Textarea
          id="notes-internal"
          defaultValue={appointment.notesInternal ?? ""}
          onBlur={(e) => {
            if (onNotesChange && e.target.value !== (appointment.notesInternal ?? "")) {
              onNotesChange(e.target.value);
            }
          }}
          placeholder="Ej.: Paciente llegará 10 minutos tarde, avisar al Dr. Mendoza."
          className="resize-none text-sm min-h-[80px]"
          disabled={isSavingNotes}
          aria-busy={isSavingNotes}
          aria-label="Notas internas del personal para este turno"
          maxLength={500}
        />
        <p className="text-xs text-muted-foreground">
          Máx. 500 caracteres — NO incluir diagnósticos ni datos clínicos aquí.
        </p>
      </div>

      {/* Last activity */}
      {appointment.lastActivityAt && (
        <div
          className="flex items-center gap-2 text-xs text-muted-foreground"
          aria-label="Última actividad"
        >
          <Clock
            className="h-3.5 w-3.5 shrink-0"
            aria-hidden="true"
          />
          <span>
            Última actividad: {formatRelativeTime(appointment.lastActivityAt, timezone, locale)}
            {appointment.lastActivityByLabel && (
              <> por {appointment.lastActivityByLabel}</>
            )}
          </span>
        </div>
      )}

      {!appointment.lastActivityAt && !appointment.notesInternal && (
        <p className="text-sm text-muted-foreground text-center py-1">
          Sin actividad registrada
        </p>
      )}
    </div>
  );
}
