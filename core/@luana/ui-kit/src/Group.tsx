// canon: design-system-canon.md §2.6 · story-origin: core-ds-foundation
"use client";

/**
 * Group.tsx — Bloque/grupo de formulario compartido (@luana/ui-kit).
 *
 * Generaliza el patrón "grupo de campos con cabecera + estado de error semántico"
 * (lift de nicolify IcpDatosForm Group/GroupHeader, ampliado con la barrita de
 * color por agente a la IZQUIERDA).
 *
 * Anatomía:
 *   ┌╴ agent-color LEFT strip (border-l-4, token-driven) ─────────────────────────┐
 *   │  título            [chip "para qué" ▸ tooltip]                                │
 *   │  Falta: campo A, campo B        ← inline cuando hay error semántico           │
 *   │  ───────────────────────────────────────────────────────────────────────────│
 *   │  children (campos del grupo)                                                  │
 *   └──────────────────────────────────────────────────────────────────────────────┘
 *
 * Estado de error SEMÁNTICO: cuando `hasError` (o `missingFields` no vacío) el
 * contenedor pinta borde rojo (border-destructive) y la lista de campos faltantes
 * se muestra inline con role="alert" — no un toast suelto, el error vive en el grupo.
 *
 * Barrita de color por agente (opcional, IZQUIERDA): token-driven, NUNCA hex.
 *   - `accentClass`: utility Tailwind de border-color (ej. "border-l-agent-lisa").
 *   - `accentVar`:   nombre de CSS var, aplicado inline (ej. "--agent-lisa")
 *                    → style={{ borderLeftColor: hsl(var(--agent-lisa)) }} + border-l-4.
 *   Sin ninguna de las dos → sin barrita (border-l normal).
 *
 * Chip "para qué": <WhatForChip> genérico (label + tooltip opcional). Brand-agnostic:
 * NO conoce agentes/marca; el consumer pasa el texto que corresponda.
 *
 * Slot/prop driven. Strings default a Spanish neutro LatAm — sin voseo.
 *
 * core-ds-foundation T-7 (lift desde nicolify Group/GroupHeader, generalizado).
 */

import * as React from "react";

import { cn } from "@luana/format/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "./tooltip";

// ── WhatForChip (chip "para qué") ─────────────────────────────────────────────

export interface WhatForChipProps {
  /** Texto visible del chip (ej. "Para Adrián" / "Mejora la captación"). */
  label: string;
  /** Texto del tooltip que explica para qué sirve el grupo (opcional). */
  tooltip?: React.ReactNode;
  className?: string;
}

/**
 * WhatForChip — chip discreto que comunica "para qué sirve este grupo".
 * Brand-agnostic: solo label + tooltip; el consumer decide el contenido.
 */
export function WhatForChip({ label, tooltip, className }: WhatForChipProps) {
  const chip = (
    <span
      data-testid="whatfor-chip"
      className={cn(
        "inline-flex items-center rounded-full border border-border/60 bg-muted/50",
        "px-2 py-0.5 text-[11px] font-medium text-muted-foreground",
        tooltip && "cursor-help",
        className,
      )}
    >
      {label}
    </span>
  );

  if (!tooltip) return chip;

  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>{chip}</TooltipTrigger>
        <TooltipContent>{tooltip}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  );
}

WhatForChip.displayName = "WhatForChip";

// ── GroupHeader ───────────────────────────────────────────────────────────────

export interface GroupHeaderProps {
  /** Título del grupo. */
  title: string;
  /** Label del chip "para qué" (opcional). */
  whatFor?: string;
  /** Tooltip del chip "para qué" (opcional, requiere whatFor). */
  whatForTooltip?: React.ReactNode;
  /**
   * Campos faltantes a mostrar inline cuando el grupo está en error.
   * Vacío/undefined → no se muestra el alert.
   */
  missingFields?: string[];
  /** Texto que precede a la lista de faltantes. @default "Falta" */
  missingLabel?: string;
  /** Slot a la derecha de la cabecera (ej. acción/contador). */
  trailing?: React.ReactNode;
  className?: string;
}

/**
 * GroupHeader — cabecera de un <Group>: título + chip "para qué" + lista inline
 * de campos faltantes (error semántico).
 */
export function GroupHeader({
  title,
  whatFor,
  whatForTooltip,
  missingFields,
  missingLabel = "Falta",
  trailing,
  className,
}: GroupHeaderProps) {
  const hasMissing = (missingFields?.length ?? 0) > 0;

  return (
    <div className={cn("mb-3 flex flex-col gap-1", className)}>
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-foreground">{title}</h3>
          {whatFor ? (
            <WhatForChip label={whatFor} tooltip={whatForTooltip} />
          ) : null}
        </div>
        {trailing ? <div className="shrink-0">{trailing}</div> : null}
      </div>
      {hasMissing ? (
        <p
          role="alert"
          aria-live="polite"
          className="text-xs font-medium text-destructive"
        >
          {missingLabel}: {missingFields!.join(", ")}
        </p>
      ) : null}
    </div>
  );
}

GroupHeader.displayName = "GroupHeader";

// ── Group ─────────────────────────────────────────────────────────────────────

export interface GroupProps {
  children: React.ReactNode;
  /**
   * Marca el grupo en estado de error semántico (borde rojo).
   * También se activa automáticamente si `missingFields` (en GroupHeader hijo)
   * tiene elementos — pero este flag permite forzarlo desde el contenedor.
   */
  hasError?: boolean;
  /**
   * Barrita de color por agente (IZQUIERDA): utility Tailwind de border-color
   * (ej. "border-l-agent-lisa"). Token-driven, NUNCA hex.
   */
  accentClass?: string;
  /**
   * Barrita de color por agente (IZQUIERDA) vía CSS var, aplicada inline
   * (ej. "--agent-lisa" → borderLeftColor: hsl(var(--agent-lisa))). Úsalo
   * cuando no exista una utility class. Token-driven, NUNCA hex.
   */
  accentVar?: string;
  className?: string;
}

/**
 * Group — contenedor de un grupo de campos con borde de estado y barrita de agente.
 *
 * @example
 * ```tsx
 * <Group accentVar="--agent-lisa" hasError={hasMissing}>
 *   <GroupHeader title="Identidad" whatFor="Para Lisa" missingFields={faltan} />
 *   ...campos...
 * </Group>
 * ```
 */
export function Group({
  children,
  hasError = false,
  accentClass,
  accentVar,
  className,
}: GroupProps) {
  const hasAccent = Boolean(accentClass || accentVar);

  return (
    <div
      data-testid="group"
      data-state={hasError ? "error" : "default"}
      style={
        accentVar
          ? { borderLeftColor: `hsl(var(${accentVar}))` }
          : undefined
      }
      className={cn(
        "rounded-xl border bg-card p-4 transition-colors",
        // estado de error semántico: el rojo manda sobre el borde general
        hasError ? "border-destructive/50" : "border-border/60",
        // barrita de agente a la izquierda (estructural + color por token):
        // va DESPUÉS para que tailwind-merge conserve el color del borde izquierdo
        // sin que el borde general (above) lo pise.
        hasAccent && "border-l-4",
        accentClass,
        className,
      )}
    >
      {children}
    </div>
  );
}

Group.displayName = "Group";
