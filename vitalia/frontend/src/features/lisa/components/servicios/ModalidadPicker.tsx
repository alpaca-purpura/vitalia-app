// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// ModalidadPicker — discriminated-union picker for how a service is delivered:
// `unica` (single visit), `sesiones` (multi-session package), `recurrente`
// (maintenance cadence). Selecting `sesiones`/`recurrente` reveals the matching
// detail slot (progressive disclosure). The detail content is provided by the
// caller (form-runtime wiring lives at the workspace level); this molecule owns
// the option grid + the discriminated reveal.
"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/cn";

export type Modalidad = "unica" | "sesiones" | "recurrente";

interface ModalidadOption {
  value: Modalidad;
  icon: string;
  title: string;
  description: string;
}

const OPTIONS: ModalidadOption[] = [
  { value: "unica", icon: "🟢", title: "Sesión única", description: "Se resuelve en una sola cita" },
  {
    value: "sesiones",
    icon: "🔁",
    title: "Por sesiones",
    description: "Un paquete de varias sesiones completa el tratamiento",
  },
  {
    value: "recurrente",
    icon: "📅",
    title: "Recurrente",
    description: "El paciente lo repite cada cierto tiempo (mantenimiento)",
  },
];

interface ModalidadPickerProps {
  value: Modalidad;
  onChange: (value: Modalidad) => void;
  disabled?: boolean;
  /** Detail slot revealed when modalidad=sesiones (progressive disclosure). */
  sesionesDetail?: ReactNode;
  /** Detail slot revealed when modalidad=recurrente (progressive disclosure). */
  recurrenteDetail?: ReactNode;
  className?: string;
}

export function ModalidadPicker({
  value,
  onChange,
  disabled = false,
  sesionesDetail,
  recurrenteDetail,
  className,
}: ModalidadPickerProps) {
  return (
    <div className={className}>
      <div
        role="radiogroup"
        aria-label="Modalidad del servicio"
        className="flex gap-1.5"
      >
        {OPTIONS.map((opt) => {
          const selected = opt.value === value;
          return (
            <button
              key={opt.value}
              type="button"
              role="radio"
              aria-checked={selected}
              data-testid={`mod-${opt.value}`}
              data-sel={selected}
              disabled={disabled}
              onClick={() => onChange(opt.value)}
              className={cn(
                "flex-1 basis-0 rounded-lg border border-border p-2 text-left transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "disabled:cursor-not-allowed disabled:opacity-50",
                selected && "border-agent-lisa bg-agent-lisa-soft/50",
                !disabled && !selected && "hover:border-agent-lisa/50",
              )}
            >
              <span className="flex items-center gap-1.5 text-xs font-semibold">
                <span aria-hidden>{opt.icon}</span>
                {opt.title}
              </span>
              <span className="mt-0.5 block text-xs leading-snug text-muted-foreground">
                {opt.description}
              </span>
            </button>
          );
        })}
      </div>

      {value === "sesiones" && (
        <div data-testid="mod-detail-sesiones" className="mt-3">
          {sesionesDetail}
        </div>
      )}
      {value === "recurrente" && (
        <div data-testid="mod-detail-recurrente" className="mt-3">
          {recurrenteDetail}
        </div>
      )}
    </div>
  );
}
