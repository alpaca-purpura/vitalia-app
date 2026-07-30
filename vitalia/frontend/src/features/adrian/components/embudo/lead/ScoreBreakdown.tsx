// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * ScoreBreakdown — Glass-box score explanation block (D.8, Resumen tab).
 * T-FE-3 vitalia-fase2-adrian-embudo
 *
 * Renders: score + temperatura + barra + breakdown factors.
 * Each factor shows: label · delta (positive green, negative red).
 * Note: "Reglas + recencia, sin caja negra."
 *
 * Server Component (no state, no effects) — pure display.
 * spec_anchor: 01-spec.md § V3 Bloque Score + 03-arch-fe.md § ScoreBreakdown
 * downstream-regression-na: brand-local vitalia FE
 */

import { cn } from "@/lib/utils";
import type { ScoreFactor } from "../../../types/embudo.types";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface ScoreBreakdownProps {
  score: number | null;
  factors: ScoreFactor[];
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * ScoreBreakdown — displays glass-box explanation of the lead score.
 *
 * Factors: each factor shows label + delta (+ green, - red).
 * Score bar: progress visualization of score/100.
 */
export function ScoreBreakdown({
  score,
  factors,
  className,
}: ScoreBreakdownProps) {
  const safeScore = score ?? 0;
  const scoreColor =
    safeScore >= 70
      ? "bg-emerald-500"
      : safeScore >= 40
        ? "bg-amber-500"
        : "bg-red-500";

  return (
    <div
      className={cn("flex flex-col gap-3", className)}
      data-testid="score-breakdown"
    >
      {/* Score bar */}
      <div className="flex items-center gap-3">
        <span className="text-2xl font-bold tabular-nums">
          {score !== null ? safeScore : "—"}
        </span>
        <div className="flex-1 h-2 bg-muted rounded-full overflow-hidden">
          <div
            className={cn("h-full rounded-full transition-all duration-500", scoreColor)}
            style={{ width: `${safeScore}%` }}
            role="progressbar"
            aria-valuenow={safeScore}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Puntuación: ${safeScore} de 100`}
          />
        </div>
      </div>

      {/* Disclaimer */}
      <p className="text-xs text-muted-foreground">
        Reglas + recencia, sin caja negra. Adrián lo recalcula en cada mensaje.
      </p>

      {/* Factors list */}
      {factors.length > 0 ? (
        <ul
          className="flex flex-col gap-1.5"
          aria-label="Factores que afectan el puntaje"
        >
          {factors.map((factor, idx) => (
            <li
              key={`${factor.label}-${idx}`}
              className="flex items-center justify-between text-sm"
            >
              <span className="text-muted-foreground">{factor.label}</span>
              <span
                className={cn(
                  "font-medium tabular-nums",
                  factor.delta > 0
                    ? "text-emerald-600 dark:text-emerald-400"
                    : "text-red-600 dark:text-red-400",
                )}
              >
                {factor.delta > 0 ? `+${factor.delta}` : factor.delta}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-sm text-muted-foreground/60 italic">
          Aún sin factores calculados
        </p>
      )}
    </div>
  );
}
