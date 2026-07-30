// canon: design-system-canon.md §2.6 · story-origin: core-ds-foundation
"use client";

/**
 * FloatingAutosaveIndicator.tsx — Indicador de autoguardado flotante (@luana/ui-kit).
 *
 * Canon §2.6 (autosave): UNA sola instancia por HOJA (SSoT del estado de guardado),
 * anclada al borde inferior de la hoja (centro), SIEMPRE visible (incl. idle) para que
 * el usuario nunca pierda de vista el estado. Reemplaza el badge inline per-bloque —
 * no se renderiza un badge por grupo.
 *
 * ★ Pertenece a la HOJA, no a la página/viewport (`anchor`, default "sheet"): se ancla
 * `absolute` al borde inferior del marco `relative` de la hoja (el panel del shell —
 * `AppPanelSlot`), centrado en el ancho de la HOJA, no de la ventana. Siempre pegado
 * abajo (contenido corto o largo). El escape hatch `anchor="page"` (`fixed` al viewport)
 * es SOLO para el caso EXCEPCIONAL no-mapeado, sin hoja contenedora.
 *
 * Brand-agnostic: colores 100% por tokens semánticos (border/card/muted/destructive +
 * emerald AA-safe para "guardado"). NUNCA hex hardcodeado ni color por-agente acá —
 * la barrita de agente vive en <Group>, no en el indicador global.
 *
 * Accesibilidad:
 *  - role="status" + aria-live="polite" → anuncia transiciones sin interrumpir.
 *  - El wrapper es pointer-events-none (jamás bloquea el contenido detrás); la píldora
 *    es pointer-events-auto para que tooltip/hover sigan funcionando.
 *  - Punto + texto, nunca color solo (WCAG 1.4.1 Use of Color).
 *
 * i18n: labels en Spanish neutro LatAm por defecto; `labels` permite override por locale.
 *
 * Uso: dentro del marco `relative` de la HOJA (el panel del shell), como hermano del
 * contenido scrolleable (NO dentro del scroll) → overlay pegado al fondo de la hoja:
 *   <div className="relative ...hoja...">      {// AppPanelSlot ya es relative }
 *     <div className="overflow-y-auto">...contenido...</div>
 *     <FloatingAutosaveIndicator status={status} savedAt={savedAt} />   {// anchor="sheet" }
 *   </div>
 *
 * core-ds-foundation T-7 (lift desde vitalia FloatingAutosaveIndicator, generalizado).
 */

import { cn } from "@luana/format/utils";
import type { AutosaveStatus } from "@luana/hooks";

// ── Default labels (Spanish neutro LatAm — sin voseo) ─────────────────────────

export const DEFAULT_FLOATING_AUTOSAVE_LABELS: Record<AutosaveStatus, string> = {
  idle: "Los cambios se guardan automáticamente",
  dirty: "Cambios sin guardar",
  saving: "Guardando…",
  saved: "Guardado",
  error: "Error al guardar. Vuelve a intentarlo.",
};

// ── Relative time helper ──────────────────────────────────────────────────────

function relativeTime(date: Date): string {
  const seconds = Math.round((Date.now() - date.getTime()) / 1000);
  if (seconds < 5) return "ahora mismo";
  if (seconds < 60) return `hace ${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes === 1) return "hace 1 min";
  return `hace ${minutes} min`;
}

// ── Token-based style maps (NUNCA hex) ────────────────────────────────────────

const PILL_STYLES: Record<AutosaveStatus, string> = {
  idle: "border-border bg-card/95 text-muted-foreground",
  dirty: "border-amber-400/40 bg-card/95 text-amber-700 dark:text-amber-400",
  saving: "border-border bg-card/95 text-muted-foreground",
  saved: "border-emerald-500/40 bg-card/95 text-emerald-700 dark:text-emerald-400",
  error: "border-destructive/40 bg-card/95 text-destructive",
};

const DOT_STYLES: Record<AutosaveStatus, string> = {
  idle: "bg-muted-foreground/40",
  dirty: "bg-amber-500 animate-pulse",
  saving: "bg-primary animate-pulse",
  saved: "bg-emerald-500",
  error: "bg-destructive",
};

// ── Props ─────────────────────────────────────────────────────────────────────

export interface FloatingAutosaveIndicatorProps {
  /** Estado actual del ciclo de autoguardado. */
  status: AutosaveStatus;
  /** Timestamp del último guardado exitoso → "Guardado hace Xs" cuando status=saved. */
  savedAt?: Date | null;
  /**
   * Override de labels — merge con los defaults.
   * Pasa cualquier subconjunto de claves AutosaveStatus para i18n / copy por tenant.
   */
  labels?: Partial<Record<AutosaveStatus, string>>;
  /**
   * Dónde vive el indicador. **Default `"sheet"` = la HOJA** (comportamiento principal):
   * `absolute` al borde inferior del marco `relative` de la hoja (panel del shell), centrado
   * en el ancho de la hoja, NUNCA del viewport. `"page"` = escape hatch EXCEPCIONAL
   * (`fixed` al viewport) para el caso no-mapeado sin hoja contenedora — usar con cuidado.
   */
  anchor?: "sheet" | "page";
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * FloatingAutosaveIndicator — píldora de estado de guardado, anclada al fondo de la HOJA.
 * UNA por hoja (canon §2.6). El wrapper no captura punteros; la píldora sí.
 *
 * @example
 * ```tsx
 * // dentro del marco relative de la hoja (AppPanelSlot)
 * <FloatingAutosaveIndicator status={status} savedAt={savedAt} />
 * ```
 */
export function FloatingAutosaveIndicator({
  status,
  savedAt,
  labels,
  anchor = "sheet",
  className,
}: FloatingAutosaveIndicatorProps) {
  const base = labels?.[status] ?? DEFAULT_FLOATING_AUTOSAVE_LABELS[status];
  const label =
    status === "saved" && savedAt ? `${base} ${relativeTime(savedAt)}` : base;

  return (
    <div
      className={cn(
        "pointer-events-none z-30 flex justify-center",
        // "sheet" (default) = ancla al marco relative de la HOJA · "page" = viewport (excepcional)
        anchor === "page" ? "fixed inset-x-0 bottom-4" : "absolute inset-x-0 bottom-4",
        className,
      )}
    >
      <div
        role="status"
        aria-live={status === "error" ? "assertive" : "polite"}
        aria-atomic="true"
        aria-label={label}
        data-testid="autosave-indicator"
        data-state={status}
        className={cn(
          "pointer-events-auto flex items-center gap-2 rounded-full border px-3.5 py-1.5",
          "text-xs font-medium shadow-lg backdrop-blur transition-all duration-300",
          PILL_STYLES[status],
        )}
      >
        <span
          className={cn("h-2 w-2 shrink-0 rounded-full", DOT_STYLES[status])}
          aria-hidden="true"
        />
        <span>{label}</span>
      </div>
    </div>
  );
}

FloatingAutosaveIndicator.displayName = "FloatingAutosaveIndicator";
