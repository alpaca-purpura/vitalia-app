// cap: scheduling.mateo-agenda
/**
 * ServicePicker.tsx — Controlled service selector for nueva-cita.
 * T-FE-2 vitalia-fase2-mateo-nueva-cita
 *
 * Controlled component: value/onChange props only.
 * onChange fires { offerId, durationMinutes } so the parent can update
 * form duration defaulting logic.
 *
 * Consumes NuevaCitaServiceItem[] from use-nueva-cita hooks (passed as props).
 * No internal data fetching — parent wires useNuevaCitaServices.
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
import type { NuevaCitaServiceItem } from "../../hooks/use-nueva-cita";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ServicePickerChange {
  offerId: string;
  durationMinutes: number | null;
}

export interface ServicePickerProps {
  services: NuevaCitaServiceItem[];
  /** Currently selected offerId */
  value: string | null;
  onChange: (change: ServicePickerChange) => void;
  loading?: boolean;
  /** H4: true when the services fetch failed */
  error?: boolean;
  /** H4: retry callback when error is true */
  onRetry?: () => void;
  disabled?: boolean;
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * ServicePicker — Select control for appointment service.
 * Selection drives duration prefill (initialApptDurationMinutes).
 */
export function ServicePicker({
  services,
  value,
  onChange,
  loading = false,
  error = false,
  onRetry,
  disabled = false,
  className,
}: ServicePickerProps) {
  if (loading) {
    return (
      <Skeleton
        data-testid="service-picker-loading"
        className={cn("h-10 w-full rounded-md", className)}
      />
    );
  }

  // H4: fetch error — show error message + retry
  if (error) {
    return (
      <div
        data-testid="service-picker-error"
        className={cn(
          "flex items-center gap-2 rounded-md border border-destructive/50 bg-destructive/5 px-3 py-2 text-sm text-destructive",
          className,
        )}
      >
        No se pudieron cargar los servicios.
        {onRetry ? (
          <button
            type="button"
            className="underline hover:no-underline"
            onClick={onRetry}
            aria-label="Reintentar cargar servicios"
          >
            Reintentar
          </button>
        ) : null}
      </div>
    );
  }

  if (!loading && services.length === 0) {
    return (
      <div
        data-testid="service-picker-empty"
        className={cn(
          "flex h-10 w-full items-center rounded-md border border-input bg-muted px-3 text-sm text-muted-foreground",
          className,
        )}
      >
        No hay servicios disponibles
      </div>
    );
  }

  const handleValueChange = (offerId: string) => {
    const service = services.find((s) => s.offerId === offerId);
    onChange({
      offerId,
      durationMinutes: service?.initialApptDurationMinutes ?? null,
    });
  };

  return (
    <Select
      // M6: always controlled (empty string = no selection); avoids controlled→uncontrolled warning
      value={value ?? ""}
      onValueChange={handleValueChange}
      disabled={disabled}
    >
      <SelectTrigger
        data-testid="service-picker-trigger"
        aria-label="Servicio"
        className={cn("w-full", className)}
      >
        <SelectValue placeholder="Selecciona un servicio…" />
      </SelectTrigger>
      <SelectContent>
        {services.map((svc) => (
          <SelectItem
            key={svc.offerId}
            value={svc.offerId}
            data-testid={`service-picker-option-${svc.offerId}`}
          >
            {svc.publicName}
            {svc.initialApptDurationMinutes != null && (
              <span className="ml-2 text-xs text-muted-foreground">
                ({svc.initialApptDurationMinutes} min)
              </span>
            )}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
