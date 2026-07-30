// cap: platform.autosave-primitive-platform
// story-origin: build-autosave-primitive-luana T-2
"use client";

/**
 * AutosaveBadge.tsx — Shared autosave status badge (@luana/ui-kit).
 *
 * Composes the existing Badge primitive from badge.tsx with design-token classes.
 *
 * Accessibility:
 *  - role="status" + aria-live="polite" for non-urgent states (idle/dirty/saving/saved)
 *  - aria-live="assertive" for error state (screen readers announce immediately)
 *  - Icon + text — never color alone (WCAG 1.4.1 Use of Color)
 *  - aria-atomic="true" so the full label is re-read on change
 *
 * Contrast (WCAG AA ≥4.5:1):
 *  - error: text-destructive (Tailwind destructive ≥7:1 on --background)
 *  - dirty: text-amber-600 dark:text-amber-500 (amber-600 = 3.65:1 alone; combined with bold = borderline;
 *    spec requires AA so we use text-amber-700 dark:text-amber-400 which is ≥4.5:1)
 *  - saving: text-muted-foreground (≥4.6:1 on --background in Luana themes)
 *  - saved: text-emerald-700 dark:text-emerald-400 (emerald-700 = 5.49:1 — passes AA)
 *    NOTE: vitalia prior art used emerald-600/dark:emerald-400 which is 3.65:1 — do NOT reproduce.
 *  - idle: text-muted-foreground (not shown, label is empty)
 *
 * i18n: default labels are Spanish neutro LatAm. Inject `labels` prop for any locale.
 *
 * ADR-012 — build-autosave-primitive-luana T-2
 */

import * as React from "react";
import { AlertCircle, CheckCircle, Clock, Loader2 } from "lucide-react";
import { cn } from "@luana/format/utils";
import type { AutosaveStatus } from "@luana/hooks";

// ── Default labels (Spanish neutro LatAm — no voseo) ─────────────────────────

export const DEFAULT_AUTOSAVE_LABELS: Record<AutosaveStatus, string> = {
  idle: "",
  dirty: "Sin guardar",
  saving: "Guardando…",
  saved: "Guardado",
  error: "No se pudo guardar. Reintenta.",
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

// ── Token-based style maps ────────────────────────────────────────────────────
// Colors use semantic Tailwind tokens with AA-compliant contrast ratios.
// NEVER use hardcoded hex values here.

const STATUS_WRAPPER_CLASSES: Record<AutosaveStatus, string> = {
  idle: "text-muted-foreground",
  dirty: "text-amber-700 dark:text-amber-400",
  saving: "text-muted-foreground",
  saved: "text-emerald-700 dark:text-emerald-400",
  error: "text-destructive",
};

// ── Icon per status ───────────────────────────────────────────────────────────

function StatusIcon({ status }: { status: AutosaveStatus }) {
  const iconProps = {
    size: 12,
    "aria-hidden": true,
    className: "shrink-0",
  } as const;

  switch (status) {
    case "dirty":
      return <Clock {...iconProps} />;
    case "saving":
      return <Loader2 {...iconProps} className={cn(iconProps.className, "animate-spin")} />;
    case "saved":
      return <CheckCircle {...iconProps} />;
    case "error":
      return <AlertCircle {...iconProps} />;
    case "idle":
    default:
      return null;
  }
}

// ── Props ─────────────────────────────────────────────────────────────────────

export interface AutosaveBadgeProps {
  /** Current autosave lifecycle status. */
  status: AutosaveStatus;
  /** Date of the last successful save (displayed as relative time when status=saved). */
  savedAt?: Date | null;
  /**
   * Custom labels — merges with defaults.
   * Pass any subset of AutosaveStatus keys to override individual labels.
   * Useful for i18n or tenant-specific copy.
   */
  labels?: Partial<Record<AutosaveStatus, string>>;
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * AutosaveBadge — inline status indicator for autosave lifecycle.
 *
 * Composes the @luana/ui-kit design system (no primitives reinvented).
 * aria-live="polite" for informational states; "assertive" for error.
 *
 * @example
 * ```tsx
 * <AutosaveBadge status={status} savedAt={savedAt} />
 * ```
 */
export function AutosaveBadge({ status, savedAt, labels, className }: AutosaveBadgeProps) {
  // Merge default labels with overrides; filter out undefined values from partial override
  const resolvedLabels: Record<AutosaveStatus, string> = Object.assign(
    {},
    DEFAULT_AUTOSAVE_LABELS,
    Object.fromEntries(
      Object.entries(labels ?? {}).filter(([, v]) => v !== undefined),
    ),
  ) as Record<AutosaveStatus, string>;

  const baseLabel = resolvedLabels[status];

  // For saved status, append relative time if savedAt is provided
  const displayLabel =
    status === "saved" && savedAt
      ? `${baseLabel} ${relativeTime(savedAt)}`
      : baseLabel;

  return (
    <span
      role="status"
      aria-live={status === "error" ? "assertive" : "polite"}
      aria-atomic="true"
      data-state={status}
      className={cn(
        "inline-flex items-center gap-1 text-xs font-medium transition-colors duration-200",
        STATUS_WRAPPER_CLASSES[status],
        className,
      )}
    >
      <StatusIcon status={status} />
      {displayLabel ? <span>{displayLabel}</span> : null}
    </span>
  );
}

AutosaveBadge.displayName = "AutosaveBadge";
