// cap: scheduling.mateo-agenda
/**
 * DoctorPicker.tsx — Controlled doctor selector for nueva-cita.
 * T-FE-2 vitalia-fase2-mateo-nueva-cita
 *
 * AC-1: No UUID text input — only a Select with named options.
 * AC-2: Only shows active doctors for the requested time slot.
 *
 * Controlled component: value/onChange props only.
 * No internal data fetching — parent wires useNuevaCitaFreeDoctors.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § F4 + 06-tickets.yaml T-FE-2
 */

"use client";

import * as React from "react";
import { cn } from "@/lib/cn";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import type { NuevaCitaDoctorItem } from "../../hooks/use-nueva-cita";

// ── Types ─────────────────────────────────────────────────────────────────────

// UUID pattern — L3: defensive label fallback for dirty seed data
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export interface DoctorPickerProps {
  doctors: NuevaCitaDoctorItem[];
  /** Currently selected doctorId */
  value: string | null;
  onChange: (doctorId: string) => void;
  loading?: boolean;
  /** H4: true when the doctors fetch failed */
  error?: boolean;
  /** H4: retry callback when error is true */
  onRetry?: () => void;
  /** Disable when no time slot selected (parent drives this) */
  disabled?: boolean;
  /** Shown as tooltip/placeholder hint when disabled */
  disabledReason?: string;
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * DoctorPicker — Select control for doctor assignment.
 * Only named doctor options; no UUID text entry (AC-1).
 */
export function DoctorPicker({
  doctors,
  value,
  onChange,
  loading = false,
  error = false,
  onRetry,
  disabled = false,
  disabledReason,
  className,
}: DoctorPickerProps) {
  if (loading) {
    return (
      <Skeleton
        data-testid="doctor-picker-loading"
        className={cn("h-10 w-full rounded-md", className)}
      />
    );
  }

  // H4: fetch error — show error message + retry
  if (error) {
    return (
      <div
        data-testid="doctor-picker-error"
        className={cn(
          "flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/5 px-3 py-2 text-sm text-destructive",
          className,
        )}
      >
        No se pudieron cargar los médicos disponibles.
        {onRetry ? (
          <button
            type="button"
            className="underline hover:no-underline"
            onClick={onRetry}
            aria-label="Reintentar cargar médicos"
          >
            Reintentar
          </button>
        ) : null}
      </div>
    );
  }

  const isDisabled = disabled || doctors.length === 0;

  const placeholder = disabled
    ? (disabledReason ?? "Selecciona fecha y hora primero")
    : doctors.length === 0
      ? "No hay médicos disponibles"
      : "Selecciona un médico…";

  // Empty state (not disabled, but no doctors for slot)
  const showEmpty = !disabled && !loading && doctors.length === 0;

  return (
    <Select
      // M6: always controlled (empty string = no selection); avoids controlled→uncontrolled warning
      value={value ?? ""}
      onValueChange={onChange}
      disabled={isDisabled}
    >
      <SelectTrigger
        data-testid="doctor-picker-trigger"
        aria-label="Médico"
        className={cn("w-full", className)}
        title={disabled ? (disabledReason ?? undefined) : undefined}
      >
        {showEmpty ? (
          <span
            data-testid="doctor-picker-empty"
            className="text-muted-foreground"
          >
            {placeholder}
          </span>
        ) : (
          <SelectValue placeholder={placeholder} />
        )}
      </SelectTrigger>
      {doctors.length > 0 && (
        <SelectContent>
          {doctors.map((doc) => {
            // L3: defensive label for dirty seed data (UUID as label)
            const label =
              !doc.doctorLabel || UUID_RE.test(doc.doctorLabel.trim())
                ? "Médico sin nombre"
                : doc.doctorLabel;
            return (
              <SelectItem
                key={doc.doctorId}
                value={doc.doctorId}
                data-testid={`doctor-picker-option-${doc.doctorId}`}
              >
                {label}
              </SelectItem>
            );
          })}
        </SelectContent>
      )}
    </Select>
  );
}
