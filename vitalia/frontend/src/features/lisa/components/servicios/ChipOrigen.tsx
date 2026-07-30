// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// ChipOrigen — a small badge showing where a service came from: "estandar"
// (linked to the clinic's standard library — e.g. "Diseño de sonrisa dental")
// or "personalizado" (created from scratch by the clinic). The lisa-soft accent
// signals a standard-library link; muted signals a custom service.
"use client";

import { cn } from "@/lib/cn";

export type ServiceOrigen = "estandar" | "personalizado";

interface ChipOrigenProps {
  origen: ServiceOrigen;
  /** Standard-service name shown when origen=estandar (e.g. "Diseño de sonrisa"). */
  standardName?: string;
  className?: string;
}

export function ChipOrigen({ origen, standardName, className }: ChipOrigenProps) {
  const isEstandar = origen === "estandar";
  return (
    <span
      data-testid="chip-origen"
      data-origen={origen}
      title={
        isEstandar
          ? standardName
            ? `Vinculado a la biblioteca estándar: "${standardName}"`
            : "Vinculado a la biblioteca estándar de tu clínica"
          : "Servicio creado por tu clínica desde cero"
      }
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-xs font-semibold",
        isEstandar
          ? "bg-agent-lisa-soft text-agent-lisa"
          : "bg-muted text-muted-foreground",
        className,
      )}
    >
      {isEstandar ? (
        <>
          <span aria-hidden>📚</span>
          {standardName ? (
            <span>
              Servicio estándar: <strong className="font-semibold">{standardName}</strong>
            </span>
          ) : (
            <span>Estándar</span>
          )}
        </>
      ) : (
        <span>Personalizado</span>
      )}
    </span>
  );
}
