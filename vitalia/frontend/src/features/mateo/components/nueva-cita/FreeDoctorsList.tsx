// cap: scheduling.mateo-agenda
/**
 * FreeDoctorsList.tsx — Time-filtered doctor list (T-D3 re-role).
 * T-D3 vitalia-fase2-mateo-nueva-cita delta (RE-ROLES T-FE-3).
 *
 * RE-ROLE: previously received pre-filtered doctors from useNuevaCitaFreeDoctors
 * (based on a specific startIso+duration). Now receives ALL doctors for the day
 * from useServiceDayStrips and filters client-side by the selected hora (advisory).
 *
 * Behavior:
 *   - No hora selected → hint: "Pon una hora para filtrar los médicos disponibles"
 *   - Hora selected → filter via isDoctorFreeAt (advisory, RN-10)
 *     - Results → clickable buttons (1-click doctor select)
 *     - Empty after filter → "No hay médicos disponibles a las {hora}"
 *
 * HIPAA: doctor_label = professional display name only. No patient PHI.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch-delta-availability.md § 4 FreeDoctorsList-re-role
 */

"use client";

import * as React from "react";
import { cn } from "@/lib/cn";
import { useNuevaCitaStore } from "../../store/nueva-cita-store";
import { filterFreeDoctors } from "../../utils/availability-filter";
import type { ServiceDayDoctor } from "../../types/agenda-schema";

// ── Props ──────────────────────────────────────────────────────────────────

export interface FreeDoctorsListProps {
  tenantId: string;
  /** All doctors for the day (from useServiceDayStrips in parent). */
  doctors: ServiceDayDoctor[];
  /** Selected hour in "HH:mm" format. Empty string = no hora set yet. */
  startHourStr: string;
  /** Tenant timezone for advisory client-side filter (isDoctorFreeAt). */
  timezone: string;
}

// ── Component ──────────────────────────────────────────────────────────────

/**
 * FreeDoctorsList — advisory time-filtered doctor selector (T-D3 re-role).
 *
 * Positioned in NuevaCitaView right column below DayAvailabilityStrip.
 * Filters ALL-day doctors down to those free at the selected hora.
 * 1-click selects the doctor (writes to Zustand store → DoctorPicker syncs).
 * Server availability/check remains the AUTHORITY (RN-10).
 */
export function FreeDoctorsList({
  doctors,
  startHourStr,
  timezone,
}: FreeDoctorsListProps) {
  const selectedDoctorId = useNuevaCitaStore((s) => s.selectedDoctorId);
  const setSelectedDoctorId = useNuevaCitaStore((s) => s.setSelectedDoctorId);

  // No hora selected yet → hint
  if (!startHourStr) {
    return (
      <p
        data-testid="free-doctors-no-slot"
        className="text-xs text-muted-foreground"
      >
        Pon una hora para filtrar los médicos disponibles.
      </p>
    );
  }

  // Client-side advisory filter (RN-10: server is the authority)
  const filtered = filterFreeDoctors(doctors, startHourStr, timezone);

  if (filtered.length === 0) {
    return (
      <p
        data-testid="free-doctors-empty"
        className="text-xs text-muted-foreground"
      >
        No hay médicos disponibles a las {startHourStr}.
      </p>
    );
  }

  return (
    <ul
      role="listbox"
      aria-label={`Médicos disponibles a las ${startHourStr}`}
      className="flex flex-wrap gap-2"
    >
      {filtered.map((doc) => {
        const isSelected = doc.doctorId === selectedDoctorId;
        return (
          <li key={doc.doctorId} role="option" aria-selected={isSelected}>
            <button
              type="button"
              data-testid={`free-doctor-btn-${doc.doctorId}`}
              aria-pressed={isSelected}
              onClick={() => setSelectedDoctorId(doc.doctorId)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs transition-colors",
                isSelected
                  ? "border-[hsl(var(--agent-mateo))] bg-[hsl(var(--agent-mateo)/10)] font-medium text-foreground"
                  : "border-border bg-background text-muted-foreground hover:border-[hsl(var(--agent-mateo))] hover:text-foreground",
              )}
            >
              {doc.doctorLabel}
            </button>
          </li>
        );
      })}
    </ul>
  );
}
