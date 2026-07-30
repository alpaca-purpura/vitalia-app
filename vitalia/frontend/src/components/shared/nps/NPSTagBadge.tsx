// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * NPSTagBadge — NPS score category badge (cross-feature shared component).
 *
 * Category colors per design-system.md § vitalia-slice-1-fidelizacion 03-arch-fe.md:
 *   - Detractor (0-6):  rojo  → vt-bg-danger-12  + vt-text-danger
 *   - Pasivo   (7-8):  amarillo → vt-bg-warning-12 + vt-text-warning
 *   - Promotor (9-10): verde  → vt-bg-success-12 + vt-text-success
 *
 * All colors via vt-* CSS utility classes from globals.css — NEVER hsl() or
 * hex literals in TSX (arch test FE-A1 enforces this).
 *
 * Usage:
 *   import { NPSTagBadge } from "@/components/shared/nps";
 *   <NPSTagBadge score={9} size="md" variant="badge" />
 *
 * Reusable cross-feature: inbox (filter chip), fidelización (stat card),
 * patient detail, NPS table row, etc.
 *
 * downstream-regression-na: vitalia-local shared component — no cross-brand consumers.
 * Cross-brand candidate: promote to @luana/ui-kit once 2nd brand adopts NPS (Slice 2 gate).
 */

import { cn } from "@/lib/cn";

// ──────────────────────────────────────────────────────────────────────────────
// Types
// ──────────────────────────────────────────────────────────────────────────────

/** Internal NPS category (data-nps-category attribute value — stable selectors). */
export type NpsCategory = "detractor" | "passive" | "promoter";

/** Visual size of the badge element. */
export type NpsBadgeSize = "sm" | "md" | "lg";

/**
 * Shape variant:
 *   - badge: standard rounded corners (--radius) — default
 *   - chip:  pill-shaped (--radius-pill) — for inline filter chips
 *   - tag:   squared (rounded-sm) — for compact table cells
 */
export type NpsBadgeVariant = "badge" | "chip" | "tag";

export interface NPSTagBadgeProps {
  /**
   * NPS score 0–10. Accepts null/undefined to render a graceful "Sin NPS"
   * fallback (for records without a response yet).
   */
  score: number | null | undefined;
  /** Visual size of the badge. Default: "md". */
  size?: NpsBadgeSize;
  /** Shape variant. Default: "badge". */
  variant?: NpsBadgeVariant;
  /** Additional CSS classes passed through to the root element. */
  className?: string;
}

// ──────────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────────

function getNpsCategory(score: number): NpsCategory {
  if (score <= 6) return "detractor";
  if (score <= 8) return "passive";
  return "promoter";
}

/**
 * Spanish neutro LatAm labels (no voseo per .claude/rules/spanish-text.md).
 * Used in visible label text and aria-label.
 */
const CATEGORY_LABEL_ES: Record<NpsCategory, string> = {
  detractor: "detractor",
  passive: "pasivo",
  promoter: "promotor",
};

/**
 * CSS utility classes from globals.css.
 * No hsl() or hex literals — required by arch test FE-A1.
 */
const CATEGORY_STYLES: Record<NpsCategory, string> = {
  detractor: "vt-bg-danger-12 vt-text-danger vt-border-danger-30",
  passive: "vt-bg-warning-12 vt-text-warning vt-border-warning-30",
  promoter: "vt-bg-success-12 vt-text-success vt-border-success-30",
};

/** Text size classes per size variant. */
const SIZE_TEXT: Record<NpsBadgeSize, string> = {
  sm: "text-xs",
  md: "text-sm",
  lg: "text-base",
};

/** Padding classes per size variant. */
const SIZE_PADDING: Record<NpsBadgeSize, string> = {
  sm: "px-1.5 py-px",
  md: "px-2 py-0.5",
  lg: "px-3 py-1",
};

/** Border radius classes per variant. */
const VARIANT_RADIUS: Record<NpsBadgeVariant, string> = {
  badge: "rounded-[var(--radius)]",
  chip: "rounded-[var(--radius-pill)]",
  tag: "rounded-sm",
};

// ──────────────────────────────────────────────────────────────────────────────
// Component
// ──────────────────────────────────────────────────────────────────────────────

/**
 * NPSTagBadge — displays an NPS score with colour-coded category.
 *
 * Server Component compatible (no client state/effects).
 * Accessible: role="status" + aria-label with score + category name.
 */
export function NPSTagBadge({
  score,
  size = "md",
  variant = "badge",
  className,
}: NPSTagBadgeProps) {
  // ── Null / undefined — graceful fallback ──────────────────────────────────
  if (score === null || score === undefined) {
    return (
      <span
        role="status"
        className={cn(
          "inline-flex items-center gap-1 border font-medium",
          SIZE_TEXT[size],
          SIZE_PADDING[size],
          VARIANT_RADIUS[variant],
          "vt-bg-muted vt-text-faint vt-border",
          className,
        )}
        aria-label="NPS: sin datos"
      >
        Sin NPS
      </span>
    );
  }

  // Clamp to valid 0-10 range
  const clampedScore = Math.max(0, Math.min(10, Math.round(score)));
  const category = getNpsCategory(clampedScore);
  const labelEs = CATEGORY_LABEL_ES[category];

  return (
    <span
      role="status"
      data-nps-category={category}
      className={cn(
        "inline-flex items-center gap-1 border font-semibold",
        SIZE_TEXT[size],
        SIZE_PADDING[size],
        VARIANT_RADIUS[variant],
        CATEGORY_STYLES[category],
        className,
      )}
      aria-label={`Calificación NPS ${clampedScore}, categoría ${labelEs}`}
    >
      {/* aria-hidden score number + category label — both read via aria-label */}
      <span aria-hidden="true">NPS {clampedScore}</span>
    </span>
  );
}
