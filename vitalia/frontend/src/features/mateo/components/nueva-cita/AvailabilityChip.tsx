// cap: scheduling.mateo-agenda
/**
 * AvailabilityChip.tsx — 4-state availability badge for nueva-cita form.
 * T-FE-3 vitalia-fase2-mateo-nueva-cita
 * UX-FIXLOOP-2 obs#3: each status maps to a DISTINCT badge variant.
 *
 * Displays:
 *   available    → Badge success   "✓ Médico disponible"
 *   busy         → Badge destructive "✕ Ocupado — se solapa con HH:MM"
 *   out_of_hours → Badge warning   "✕ Fuera del horario" + contextual Alert
 *   no_schedule  → Badge secondary "○ Sin horario registrado" + contextual Alert
 *   loading      → skeleton span
 *   error        → inline error + retry button (SC-disponibilidad-falla)
 *
 * HIPAA: chip shows scheduling metadata only — no PHI (conflict_label is time-only).
 * A11y: aria-live="polite" on chip container, aria-busy on loading.
 *
 * Syncs status to store (setAvailabilityStatus) so T-FE-4 can block submit.
 * Clears on unmount.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

"use client";

import * as React from "react";
import { Alert, AlertDescription, Badge } from "@luana/ui-kit";
import { useAvailabilityCheck } from "../../hooks/use-availability";
import { useNuevaCitaStore } from "../../store/nueva-cita-store";

// ── Props ──────────────────────────────────────────────────────────────────

export interface AvailabilityChipProps {
  tenantId: string;
  // token removed — hook calls getToken() fresh per-request (T-FE-4)
  doctorId: string | null;
  startIso: string;
  durationMinutes: number;
}

// ── Status config ──────────────────────────────────────────────────────────

type BadgeVariant = "success" | "destructive" | "warning" | "secondary";

interface StatusConfig {
  label: string;
  variant: BadgeVariant;
  /** Contextual guidance shown below the chip; null = no Alert */
  guide: string | null;
}

function getStatusConfig(
  status: string,
  conflictLabel: string | null,
): StatusConfig {
  switch (status) {
    case "available":
      return { label: "✓ Médico disponible", variant: "success", guide: null };
    case "busy":
      return {
        label: conflictLabel
          ? `✕ Ocupado — ${conflictLabel}`
          : "✕ Ocupado",
        variant: "destructive",
        guide: null, // FreeDoctorsList handles guidance for busy
      };
    case "out_of_hours":
      return {
        label: "✕ Fuera del horario",
        variant: "warning",
        guide:
          "Elige una hora dentro del horario de atención, o reasigna a otro médico que atienda más temprano.",
      };
    case "no_schedule":
    default:
      return {
        label: "○ Sin horario registrado",
        variant: "secondary",
        guide: "Carga el horario de este médico primero en Mi Clínica › Horarios.",
      };
  }
}

// ── Component ──────────────────────────────────────────────────────────────

/**
 * AvailabilityChip — standalone badge that reflects current slot availability.
 *
 * Wired into NuevaCitaView by T-FE-4 next to the Médico field.
 * Exposes isAvailable via store (setAvailabilityStatus) for submit-block.
 */
export function AvailabilityChip({
  tenantId,
  doctorId,
  startIso,
  durationMinutes,
}: AvailabilityChipProps) {
  const setAvailabilityStatus = useNuevaCitaStore(
    (s) => s.setAvailabilityStatus,
  );

  const { data, isPending, isError, refetch } = useAvailabilityCheck({
    tenantId,
    doctorId,
    startIso,
    durationMinutes,
  });

  // Sync availability status to store for T-FE-4 submit-block
  React.useEffect(() => {
    setAvailabilityStatus(data?.status ?? null);
    return () => {
      // Clear on unmount so submit-block resets
      setAvailabilityStatus(null);
    };
  }, [data?.status, setAvailabilityStatus]);

  // Nothing when doctorId not selected
  if (!doctorId) return null;

  // Loading skeleton
  if (isPending) {
    return (
      <span
        role="status"
        aria-label="Verificando disponibilidad..."
        aria-busy={true}
        className="inline-block h-5 w-32 animate-pulse rounded-full bg-muted"
      />
    );
  }

  // SC-disponibilidad-falla: endpoint down → error + retry
  if (isError || !data) {
    return (
      <span
        data-testid="availability-chip-error"
        className="inline-flex items-center gap-1.5 text-xs text-destructive"
      >
        No se pudo verificar disponibilidad.
        <button
          type="button"
          className="underline hover:no-underline"
          onClick={() => void refetch()}
          aria-label="Reintentar verificar disponibilidad"
        >
          Reintentar
        </button>
      </span>
    );
  }

  const { label, variant, guide } = getStatusConfig(
    data.status,
    data.conflictLabel,
  );

  return (
    <span
      data-testid="availability-chip"
      aria-live="polite"
      aria-atomic="true"
      className="inline-flex flex-col gap-1.5"
    >
      {/* data-variant used by tests to assert distinct variants */}
      <Badge variant={variant} data-variant={variant}>
        {label}
      </Badge>
      {guide !== null && (
        <Alert
          data-testid="availability-chip-alert"
          className="py-2 text-xs"
        >
          <AlertDescription>{guide}</AlertDescription>
        </Alert>
      )}
    </span>
  );
}
