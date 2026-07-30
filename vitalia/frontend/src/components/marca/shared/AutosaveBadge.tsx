// cap: brand_studio.lisa-marca
// story-origin: vitalia-fase2-s7-TBD
/**
 * AutosaveBadge.tsx — Shared autosave status badge.
 *
 * Displays the autosave lifecycle: idle → dirty → saving → saved | error.
 * Shared across T-5 (Identidad), T-6 (Voz y tono), T-7 (Presencia).
 *
 * Placed in components/marca/shared/ (not features/lisa) because it is
 * reused across all 3 sub-sub-tabs without domain coupling.
 *
 * Accessibility: role="status" with aria-live="polite" for screen readers.
 * Spanish neutro LatAm — no voseo.
 *
 * T-5 vitalia-fase2-lisa-marca
 * spec_anchor: 06-tickets.yaml T-5 deliverables
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import { cn } from "@/lib/utils";

export type AutosaveStatus = "idle" | "dirty" | "saving" | "saved" | "error";

export interface AutosaveBadgeProps {
  status: AutosaveStatus;
  /** Timestamp of last successful save (shown as "Guardado hace Xs"). */
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

const STATUS_STYLES: Record<AutosaveStatus, string> = {
  idle: "text-muted-foreground",
  dirty: "text-amber-600 dark:text-amber-400",
  saving: "text-muted-foreground",
  saved: "text-emerald-600 dark:text-emerald-400",
  error: "text-destructive",
};

const STATUS_DOTS: Record<AutosaveStatus, string> = {
  idle: "bg-muted-foreground/30",
  dirty: "bg-amber-400 animate-pulse",
  saving: "bg-primary/50 animate-pulse",
  saved: "bg-emerald-500",
  error: "bg-destructive",
};

/**
 * AutosaveBadge — displays autosave state as a small inline status indicator.
 * Role="status" with aria-live="polite" so screen readers announce changes.
 */
export function AutosaveBadge({ status, savedAt, className }: AutosaveBadgeProps) {
  const label = (() => {
    switch (status) {
      case "saving":
        return "Guardando...";
      case "saved":
        return savedAt ? `Guardado ${relativeTime(savedAt)}` : "Guardado";
      case "error":
        return "Error al guardar";
      case "dirty":
        return "Cambios sin guardar";
      case "idle":
      default:
        return null;
    }
  })();

  return (
    <div
      role="status"
      aria-live="polite"
      aria-label={label ?? "Estado de guardado"}
      data-testid="autosave-badge"
      data-state={status}
      className={cn(
        "flex items-center gap-1.5 text-xs font-medium transition-all duration-300",
        STATUS_STYLES[status],
        className,
      )}
    >
      <span
        className={cn("h-1.5 w-1.5 shrink-0 rounded-full", STATUS_DOTS[status])}
        aria-hidden="true"
      />
      {label && <span>{label}</span>}
    </div>
  );
}

AutosaveBadge.displayName = "AutosaveBadge";
