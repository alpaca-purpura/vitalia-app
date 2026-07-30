// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * ScoreDonut — Compact SVG donut chart for lead score (0-100).
 *
 * D.5 spec: 34×34 viewport, radius 10, stroke-width 4.
 * Color by tier: ≥70 emerald (green), 40-69 amber, <40 red.
 * Number centered inside the donut.
 *
 * Design rules:
 * - Server Component (no state, no effects).
 * - No hardcoded hex — Tailwind token classes only.
 * - a11y: score number visible (not color-only). aria-label includes score.
 * - SVG dimensions: 34×34, r=10, circumference≈62.83, stroke-width=4.
 *
 * Usage:
 *   <ScoreDonut score={72} />
 *   <ScoreDonut score={48} className="shrink-0" />
 *
 * spec_anchor: 03-arch-fe.md § NEW ScoreDonut D.5 + 01-spec.md § LeadCard item 3
 * downstream-regression-na: brand-local shared component
 */

import { cn } from "@/lib/utils";

// ── Score constants ───────────────────────────────────────────────────────────

const SIZE = 34;
const RADIUS = 10;
const STROKE_WIDTH = 4;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS; // ≈ 62.83

// ── Score tier helpers ────────────────────────────────────────────────────────

/** Score color tier used for stroke and label styling. */
type ScoreTier = "green" | "amber" | "red";

function scoreTier(score: number): ScoreTier {
  if (score >= 70) return "green";
  if (score >= 40) return "amber";
  return "red";
}

/** Tailwind stroke class for the progress arc. */
function strokeClass(tier: ScoreTier): string {
  switch (tier) {
    case "green":
      return "stroke-emerald-500 dark:stroke-emerald-400";
    case "amber":
      return "stroke-amber-500 dark:stroke-amber-400";
    case "red":
      return "stroke-red-500 dark:stroke-red-400";
  }
}

/** Tailwind text class for the centered number label. */
function labelClass(tier: ScoreTier): string {
  switch (tier) {
    case "green":
      return "fill-emerald-700 dark:fill-emerald-300";
    case "amber":
      return "fill-amber-700 dark:fill-amber-300";
    case "red":
      return "fill-red-700 dark:fill-red-300";
  }
}

// ── Component Props ───────────────────────────────────────────────────────────

export interface ScoreDonutProps {
  /** Lead score 0-100. Values outside this range are clamped. */
  score: number;
  /** Optional extra Tailwind classes on the outer wrapper. */
  className?: string;
}

// ── ScoreDonut ────────────────────────────────────────────────────────────────

/**
 * ScoreDonut — Compact SVG donut for lead score.
 *
 * Renders a 34×34 SVG with:
 * - A muted track arc (full circle)
 * - A colored progress arc proportional to score/100
 * - The score number centered inside
 *
 * a11y: number is always visible text inside the SVG (not only color).
 * The wrapper div has aria-label="Puntuación: {score}/100".
 */
export function ScoreDonut({ score, className }: ScoreDonutProps) {
  // Clamp score to 0-100
  const clamped = Math.max(0, Math.min(100, score));
  const tier = scoreTier(clamped);

  // Progress arc: dashoffset drives how much of the circumference is visible.
  // When offset = 0, the full arc is shown. When offset = circumference, nothing is shown.
  const dashOffset = CIRCUMFERENCE * (1 - clamped / 100);

  // Center coordinates
  const cx = SIZE / 2;
  const cy = SIZE / 2;

  // SVG start: top of the circle (rotate -90° so arc starts at 12 o'clock)
  // Implemented via SVG transform on the progress circle

  // Font size for the centered label — compact for 2-digit numbers, smaller for 3
  const fontSize = clamped === 100 ? 7 : 9;

  return (
    <div
      className={cn("relative inline-flex items-center justify-center", className)}
      aria-label={`Puntuación: ${clamped}/100`}
      role="img"
    >
      <svg
        width={SIZE}
        height={SIZE}
        viewBox={`0 0 ${SIZE} ${SIZE}`}
        aria-hidden
        focusable="false"
      >
        {/* Track — full muted circle */}
        <circle
          cx={cx}
          cy={cy}
          r={RADIUS}
          fill="none"
          strokeWidth={STROKE_WIDTH}
          className="stroke-muted-foreground/20"
        />

        {/* Progress arc — colored by tier */}
        <circle
          cx={cx}
          cy={cy}
          r={RADIUS}
          fill="none"
          strokeWidth={STROKE_WIDTH}
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={dashOffset}
          strokeLinecap="round"
          // Rotate -90° so arc starts at top (12 o'clock)
          transform={`rotate(-90 ${cx} ${cy})`}
          className={cn(strokeClass(tier), "transition-[stroke-dashoffset] duration-500")}
        />

        {/* Centered score number — always visible (a11y: not color-only) */}
        <text
          x={cx}
          y={cy}
          textAnchor="middle"
          dominantBaseline="central"
          fontSize={fontSize}
          fontWeight="600"
          className={labelClass(tier)}
        >
          {clamped}
        </text>
      </svg>
    </div>
  );
}
