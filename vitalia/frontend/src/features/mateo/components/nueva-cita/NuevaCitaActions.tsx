// cap: scheduling.mateo-agenda
/**
 * NuevaCitaActions.tsx — FormActionBar wrapper for the nueva-cita form.
 * T-FE-4 vitalia-fase2-mateo-nueva-cita
 *
 * Thin wrapper: applies accent="mateo" + standard labels.
 * Consumed by NuevaCitaView — sticky bottom bar.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 06-tickets.yaml T-FE-4
 */

"use client";

import * as React from "react";
import { FormActionBar } from "@luana/ui-kit";

// ── Props ──────────────────────────────────────────────────────────────────────

export interface NuevaCitaActionsProps {
  onCancel: () => void;
  onSubmit: () => void;
  submitting?: boolean;
  /** True = availability not AVAILABLE or form invalid (fail-closed RN-10). */
  submitDisabled?: boolean;
  hint?: React.ReactNode;
}

// ── Component ──────────────────────────────────────────────────────────────────

/**
 * NuevaCitaActions — sticky FormActionBar for the nueva-cita leaf sheet.
 *
 * accent="mateo" → primary button uses --agent-mateo token (#FEE209).
 * submitDisabled = !isValid || availabilityStatus !== "available" (RN-10 fail-closed).
 */
export function NuevaCitaActions({
  onCancel,
  onSubmit,
  submitting = false,
  submitDisabled = false,
  hint,
}: NuevaCitaActionsProps) {
  return (
    <FormActionBar
      accent="mateo"
      submitLabel="Crear cita"
      cancelLabel="Cancelar"
      onCancel={onCancel}
      onSubmit={onSubmit}
      submitting={submitting}
      submitDisabled={submitDisabled}
      hint={hint}
      testId="nueva-cita-actions"
    />
  );
}
