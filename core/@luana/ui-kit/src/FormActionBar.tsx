// canon: design-system-canon.md §2.6 · story-origin: vitalia-fase2-mateo-nueva-cita (P-0)
"use client";

/**
 * FormActionBar.tsx — Canon sticky submit bar (@luana/ui-kit · NET-NEW, no prior art).
 *
 * El "segundo modo" del canon de formularios: el canon de hoy es SOLO autosave
 * (FloatingAutosaveIndicator + use-autosave, sin botón de guardado). Este es el
 * modo EXPLÍCITO — crear/enviar un registro nuevo con un submit deliberado
 * (ej. "Nueva cita"): el usuario completa, ve el hint del estado, y confirma.
 *
 * Anatomy:
 *   ┌─ sticky bottom · border-top · shadow hacia arriba · bg-card ────────────────┐
 *   │  {hint texto izquierda}                       [ Cancelar ]  [ Crear cita ]   │
 *   └──────────────────────────────────────────────────────────────────────────────┘
 *
 * Mismo lenguaje visual que la franja N3 invertida: full-bleed sticky con borde +
 * sombra que apunta hacia ARRIBA (la franja N3 apunta hacia abajo). bg-card.
 *
 * Token-driven accent: `accent` recibe la CLAVE de un agente (ej. "mateo") y el
 * botón primario se tiñe con `hsl(var(--agent-{accent}))` vía inline style — mismo
 * patrón que EntityInfoCard `accentVar`. NUNCA un hex. Sin `accent` → primary del tema.
 *
 * Slot/prop driven + brand-agnostic. Strings default en español neutro LatAm.
 */

import * as React from "react";
import { Loader2 } from "lucide-react";

import { cn } from "@luana/format/utils";
import { Button } from "./button";

export interface FormActionBarProps {
  /** Texto de estado a la izquierda (ej. "Sin guardar todavía"). */
  hint?: React.ReactNode;
  /** Etiqueta del botón cancelar. Default "Cancelar". */
  cancelLabel?: string;
  /** Etiqueta del botón de envío (ej. "Crear cita"). Obligatoria. */
  submitLabel: string;
  /** Click en cancelar. Cuando se omite, no se renderiza el botón cancelar. */
  onCancel?: () => void;
  /** Click en enviar. */
  onSubmit?: () => void;
  /** En curso → deshabilita el submit + spinner. */
  submitting?: boolean;
  /** Bloqueo por validación → deshabilita el submit (sin spinner). */
  submitDisabled?: boolean;
  /**
   * Clave de color de agente (ej. "mateo") — tiñe el botón primario con
   * `hsl(var(--agent-{accent}))` vía inline style (token-driven, NUNCA hex).
   * Sin `accent` → color primary del tema.
   */
  accent?: string;
  /** Stable testid seed. Renderiza `{testId}` + sufijos. Default "form-action-bar". */
  testId?: string;
  className?: string;
}

/**
 * FormActionBar — barra sticky de envío explícito.
 * data-testid="{testId}" en el contenedor (default "form-action-bar").
 */
export function FormActionBar({
  hint,
  cancelLabel = "Cancelar",
  submitLabel,
  onCancel,
  onSubmit,
  submitting = false,
  submitDisabled = false,
  accent,
  testId = "form-action-bar",
  className,
}: FormActionBarProps) {
  const isSubmitDisabled = submitting || submitDisabled;
  // Token-driven accent → inline style on the primary button (mirror EntityInfoCard accentVar).
  const accentStyle: React.CSSProperties | undefined = accent
    ? { backgroundColor: `hsl(var(--agent-${accent}))` }
    : undefined;

  return (
    <div
      role="group"
      aria-label="Acciones del formulario"
      data-testid={testId}
      className={cn(
        // Sticky full-bleed bottom bar: border-top + upward shadow + card surface.
        "sticky bottom-0 z-10 flex items-center justify-between gap-4",
        "border-t border-border bg-card px-6 py-3 shadow-[0_-2px_8px_-4px_rgba(0,0,0,0.12)]",
        className,
      )}
    >
      <div className="min-w-0 flex-1 truncate text-sm text-muted-foreground" data-testid={`${testId}-hint`}>
        {hint}
      </div>
      <div className="flex shrink-0 items-center gap-2">
        {onCancel ? (
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={submitting}
            data-testid={`${testId}-cancel`}
          >
            {cancelLabel}
          </Button>
        ) : null}
        <Button
          type="button"
          variant="default"
          onClick={onSubmit}
          disabled={isSubmitDisabled}
          aria-busy={submitting || undefined}
          style={accentStyle}
          data-testid={`${testId}-submit`}
        >
          {submitting ? <Loader2 className="animate-spin" aria-hidden="true" /> : null}
          {submitLabel}
        </Button>
      </div>
    </div>
  );
}
