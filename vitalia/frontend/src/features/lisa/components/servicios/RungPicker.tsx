// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// RungPicker — the 5-step value ladder ("escalera de valor") for a service.
// Engine OfferValueLevel members map to vitalia medical labels (RN-2 / §7
// override). When `locked`, the ladder is read-only — it is dictated by the
// standard service and surfaced for context only (RN-31).
"use client";

import { cn } from "@/lib/cn";

/** Engine OfferValueLevel members (SSoT: core offer-studio value_level_catalog). */
export type OfferValueLevel =
  | "LEAD_MAGNET"
  | "ACTIVACION"
  | "TRANSFORMACION"
  | "MAXIMIZACION"
  | "CORPORATIVO";

/** Medical-vertical labels for vitalia (RN-2 / spec §7 override of generic labels). */
const RUNG_LABELS: Record<OfferValueLevel, string> = {
  LEAD_MAGNET: "Gancho gratuito",
  ACTIVACION: "Primera visita",
  TRANSFORMACION: "Tratamiento principal",
  MAXIMIZACION: "Premium",
  CORPORATIVO: "Plan/convenio",
};

const RUNG_ORDER: OfferValueLevel[] = [
  "LEAD_MAGNET",
  "ACTIVACION",
  "TRANSFORMACION",
  "MAXIMIZACION",
  "CORPORATIVO",
];

interface RungPickerProps {
  value: OfferValueLevel;
  onChange: (value: OfferValueLevel) => void;
  /** Read-only ladder: dictated by the standard service (RN-31). */
  locked?: boolean;
  className?: string;
}

export function RungPicker({ value, onChange, locked = false, className }: RungPickerProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Escalera de valor"
      className={cn("flex gap-1.5", className)}
    >
      {RUNG_ORDER.map((rung) => {
        const selected = rung === value;
        return (
          <button
            key={rung}
            type="button"
            role="radio"
            aria-checked={selected}
            data-testid={`rung-${rung}`}
            data-sel={selected}
            disabled={locked}
            onClick={() => onChange(rung)}
            className={cn(
              "flex-1 basis-0 rounded-lg border border-border px-1.5 py-2 text-center text-xs leading-tight transition-colors",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              selected && "border-agent-lisa bg-agent-lisa-soft font-semibold",
              !locked && !selected && "hover:border-agent-lisa/50",
              locked && !selected && "cursor-not-allowed opacity-45",
              locked && "cursor-not-allowed",
            )}
          >
            {RUNG_LABELS[rung]}
          </button>
        );
      })}
    </div>
  );
}

export { RUNG_LABELS };
