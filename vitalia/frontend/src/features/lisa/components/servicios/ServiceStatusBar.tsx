// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-7
"use client";
/**
 * ServiceStatusBar.tsx — Header bar shown at the top of each workspace leaf.
 *
 * Displays:
 *   - Switch activo/inactivo (AC-19: NUNCA bloqueado, incluso con campos vacíos)
 *   - ChipOrigen (estándar/personalizado)
 *   - FichaCompletenessChip (completitud del servicio)
 *
 * Activating fires a confirm dialog first (G2-F2a: hacer público un servicio es
 * una acción visible, se avisa antes). Deactivating fires immediately.
 * The toggle is a POST (NOT an autosave field).
 */

import { useState } from "react";
import {
  Switch,
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
} from "@luana/ui-kit";
import { Label } from "@/components/ui/label";
import { ChipOrigen } from "./ChipOrigen";
import { FichaCompletenessChip } from "./FichaCompletenessChip";
import type { ServiceDetail } from "../../types/servicios.types";

export interface ServiceStatusBarProps {
  servicio: ServiceDetail;
  /** Completitud fields info */
  filledCount?: number;
  totalCount?: number;
  missingFields?: string[];
  /** Called when the activo switch is toggled */
  onToggleActive?: (isActive: boolean) => void;
  /** Whether the toggle mutation is pending */
  isToggling?: boolean;
}

export function ServiceStatusBar({
  servicio,
  filledCount = 0,
  totalCount = 0,
  missingFields = [],
  onToggleActive,
  isToggling = false,
}: ServiceStatusBarProps) {
  const switchId = `activo-switch-${servicio.offer_id}`;
  const [confirmOpen, setConfirmOpen] = useState(false);

  // Activating → confirm first (G2-F2a). Deactivating → fire immediately.
  const handleSwitch = (next: boolean) => {
    if (next) setConfirmOpen(true);
    else onToggleActive?.(false);
  };
  const confirmActivate = () => {
    setConfirmOpen(false);
    onToggleActive?.(true);
  };

  return (
    <div
      className="flex items-center gap-4 px-4 py-2 border-b border-border bg-card sticky top-0 z-10"
      aria-label="Estado del servicio"
    >
      {/* Activo toggle — AC-19: NUNCA bloqueado */}
      <div className="flex items-center gap-2">
        <Switch
          id={switchId}
          checked={servicio.is_active}
          disabled={isToggling}
          onCheckedChange={handleSwitch}
          aria-label={servicio.is_active ? "Desactivar servicio" : "Activar servicio"}
        />
        <Label htmlFor={switchId} className="text-sm cursor-pointer">
          {servicio.is_active ? "Activo" : "Inactivo"}
        </Label>
      </div>

      {/* G2-F2a: confirmación antes de activar (hacer el servicio público) */}
      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>¿Activar este servicio?</AlertDialogTitle>
            <AlertDialogDescription>
              Al activarlo, “{servicio.public_name || "este servicio"}” queda visible
              y disponible para tus pacientes y para los agentes. Puedes desactivarlo
              cuando quieras.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={confirmActivate}>Activar</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="h-4 w-px bg-border" aria-hidden="true" />

      {/* Origen chip */}
      <ChipOrigen
        origen={servicio.canonical_service_ref ? "estandar" : "personalizado"}
      />

      <div className="h-4 w-px bg-border" aria-hidden="true" />

      {/* Completitud */}
      {totalCount > 0 && (
        <FichaCompletenessChip
          filled={filledCount}
          total={totalCount}
          title={
            missingFields.length > 0
              ? `Faltan: ${missingFields.join(", ")}`
              : undefined
          }
        />
      )}
    </div>
  );
}
