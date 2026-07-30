// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-mateo-nueva-cita (T-FE-1 — replaced modal with full-page push)
"use client";

/**
 * CrearCitaButton.tsx — Dropdown trigger for appointment creation.
 * T-FE-1 vitalia-fase2-mateo-nueva-cita (AC-9: replaced Dialog/modal with router.push)
 *
 * Previously (T-16): opened a Dialog wrapping CrearCitaForm.
 * Now (T-FE-1): pushes to /mateo/agenda/nueva-cita with ?origin= param.
 * D-G: CrearCitaForm modal REMOVED entirely. Full-page sheet is the SSoT.
 *
 * Opciones (2 — origin="existing_patient" dropped per DTO reconciliation):
 *   1. 👤 Paciente walk-in  → origin="walk_in"
 *   2. 📞 Reserva telefónica → origin="telefono"
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § F3 + 06-tickets.yaml T-FE-1
 */

import * as React from "react";
import { useRouter } from "next/navigation";
import { Plus, User, Phone } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface CrearCitaButtonProps {
  /** Tenant ID — used to build the navigation path. */
  tenantId: string;
  /** Clinic ID — kept for API compat but no longer used in route push. */
  clinicId: string;
  /** "button" (default, desktop) | "fab" (mobile fixed bottom-right). */
  variant?: "button" | "fab";
  /** Additional className for the outer wrapper. */
  className?: string;
}

type AppointmentOrigin = "walk_in" | "telefono";

// ── Dropdown option definitions ───────────────────────────────────────────────

interface CreateOption {
  origin: AppointmentOrigin;
  label: string;
  description: string;
  icon: React.ElementType;
  testId: string;
}

const CREATE_OPTIONS: CreateOption[] = [
  {
    origin: "walk_in",
    label: "Paciente walk-in",
    description: "Paciente que llega sin cita previa",
    icon: User,
    testId: "crear-cita-walk-in",
  },
  {
    origin: "telefono",
    label: "Reserva telefónica",
    description: "Cita agendada por teléfono",
    icon: Phone,
    testId: "crear-cita-telefono",
  },
];

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * CrearCitaButton — DropdownMenu with 2 appointment creation modes.
 * On select → router.push to /[tenantId]/mateo/agenda/nueva-cita?origin=...
 *
 * AC-9: No modal/drawer — full-page leaf sheet navigation.
 */
export function CrearCitaButton({
  tenantId,
  variant = "button",
  className,
}: CrearCitaButtonProps) {
  const router = useRouter();

  const handleOptionSelect = React.useCallback(
    (origin: AppointmentOrigin) => {
      router.push(`/${tenantId}/mateo/agenda/nueva-cita?origin=${origin}`);
    },
    [tenantId, router],
  );

  const isFab = variant === "fab";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        {isFab ? (
          <button
            type="button"
            aria-label="Nueva cita"
            data-testid="crear-cita-fab"
            className={cn(
              "fixed bottom-4 right-4 z-40",
              "flex items-center justify-center",
              "w-14 h-14 rounded-full",
              "bg-agent-valeria text-white",
              "shadow-lg hover:shadow-xl",
              "transition-all duration-150 hover:scale-105 active:scale-95",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
              className,
            )}
          >
            <Plus className="w-6 h-6" aria-hidden="true" />
          </button>
        ) : (
          <Button
            type="button"
            data-testid="crear-cita-button"
            aria-label="Crear nueva cita"
            className={cn("gap-2", className)}
          >
            <Plus className="w-4 h-4" aria-hidden="true" />
            Nueva cita
          </Button>
        )}
      </DropdownMenuTrigger>

      <DropdownMenuContent
        side={isFab ? "top" : "bottom"}
        align={isFab ? "end" : "start"}
        className="w-60"
        data-testid="crear-cita-dropdown"
      >
        {CREATE_OPTIONS.map(({ origin, label, description, icon: Icon, testId }) => (
          <DropdownMenuItem
            key={origin}
            data-testid={testId}
            onClick={() => handleOptionSelect(origin)}
            className="flex items-start gap-3 py-2.5 cursor-pointer"
          >
            <div
              className="flex-shrink-0 w-7 h-7 rounded-md bg-muted flex items-center justify-center mt-0.5"
              aria-hidden="true"
            >
              <Icon className="w-3.5 h-3.5 text-muted-foreground" />
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-sm font-medium">{label}</span>
              <span className="text-xs text-muted-foreground">{description}</span>
            </div>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
