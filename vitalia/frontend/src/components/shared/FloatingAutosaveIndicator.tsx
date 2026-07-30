// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * FloatingAutosaveIndicator.tsx — STANDARD autosave indicator for every functional
 * block with autosave (Chris, comentario diseño #3 2026-06-07).
 *
 * Replaces the per-block header `AutosaveBadge`: a single floating pill anchored
 * bottom-center of the content panel that is ALWAYS visible (incl. idle) and
 * sticks while the panel scrolls — so the user never loses sight of the save state.
 *
 * Usage: render as the LAST child of the view's scroll container.
 *   <div className="flex flex-col gap-6 p-6">
 *     ...content...
 *     <FloatingAutosaveIndicator status={autosaveStatus} savedAt={savedAt} />
 *   </div>
 *
 * Accessibility: role="status" + aria-live="polite" announces transitions.
 * Spanish neutro LatAm — sin voseo.
 *
 * Standard SSoT: any block with autosave uses THIS (not a bespoke inline hint).
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { cn } from "@/lib/utils";

/** Superset of all autosave lifecycles in the app (perfil omits "dirty"). */
export type AutosaveStatus = "idle" | "dirty" | "saving" | "saved" | "error";

export interface FloatingAutosaveIndicatorProps {
  status: AutosaveStatus;
  /** Timestamp of last successful save → "Guardado hace Xs". */
  savedAt?: Date | null;
  className?: string;
}

function relativeTime(date: Date): string {
  const seconds = Math.round((Date.now() - date.getTime()) / 1000);
  if (seconds < 5) return "ahora mismo";
  if (seconds < 60) return `hace ${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  if (minutes === 1) return "hace 1 min";
  return `hace ${minutes} min`;
}

const PILL_STYLES: Record<AutosaveStatus, string> = {
  idle: "border-border bg-card/95 text-muted-foreground",
  dirty: "border-amber-400/40 bg-card/95 text-amber-600 dark:text-amber-400",
  saving: "border-border bg-card/95 text-muted-foreground",
  saved: "border-agent-lisa/40 bg-card/95 text-foreground",
  error: "border-destructive/40 bg-card/95 text-destructive",
};

const DOT_STYLES: Record<AutosaveStatus, string> = {
  idle: "bg-muted-foreground/40",
  dirty: "bg-amber-400 animate-pulse",
  saving: "bg-primary animate-pulse",
  saved: "bg-agent-lisa",
  error: "bg-destructive",
};

/**
 * FloatingAutosaveIndicator — sticky bottom-center save-state pill.
 * Wrapper is pointer-events-none (never blocks the content behind it); the pill
 * itself is pointer-events-auto so its tooltip/hover still works.
 */
export function FloatingAutosaveIndicator({
  status,
  savedAt,
  className,
}: FloatingAutosaveIndicatorProps) {
  const label = (() => {
    switch (status) {
      case "saving":
        return "Guardando…";
      case "saved":
        return savedAt ? `Guardado ${relativeTime(savedAt)}` : "Guardado";
      case "error":
        return "Error al guardar. Vuelve a intentarlo.";
      case "dirty":
        return "Cambios sin guardar";
      case "idle":
      default:
        return "Los cambios se guardan automáticamente";
    }
  })();

  return (
    <div
      className={cn(
        "pointer-events-none sticky bottom-4 z-30 mt-2 flex justify-center",
        className,
      )}
    >
      <div
        role="status"
        aria-live="polite"
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
