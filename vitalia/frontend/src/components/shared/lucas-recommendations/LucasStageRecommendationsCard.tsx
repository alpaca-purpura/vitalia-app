// cap: platform.shell-foundation-shadcn-tailwind-v4
// story-origin: TBD
/**
 * LucasStageRecommendationsCard — scaffold stub.
 *
 * Placeholder for Lucas AI agent stage-based recommendations.
 * Full implementation arrives in copilot-tools-impl story (Slice 2).
 *
 * Per design-system.md: card recipe (vt-bg-surface vt-border).
 * All colors via vt-* CSS classes from globals.css (no hsl literals in TSX).
 */

import { cn } from "@/lib/cn";

export interface StageRecommendation {
  /** Unique recommendation ID */
  id: string;
  /** Short recommendation title (Spanish neutro) */
  title: string;
  /** Detail explanation (optional) */
  detail?: string;
  /** Action label for primary CTA */
  actionLabel?: string;
  /** Priority level (drives visual weight) */
  priority?: "high" | "medium" | "low";
}

export interface LucasStageRecommendationsCardProps {
  /** Patient or lead stage label (e.g. "Nutrición") */
  stageLabel: string;
  /** Recommendations from Lucas agent */
  recommendations?: StageRecommendation[];
  /** Whether data is loading */
  isLoading?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Scaffold — shows Lucas stage recommendations.
 * Real implementation (with copilot hooks + streaming) arrives in Slice 2.
 */
export function LucasStageRecommendationsCard({
  stageLabel,
  recommendations = [],
  isLoading = false,
  className,
}: LucasStageRecommendationsCardProps) {
  return (
    <section
      className={cn(
        "vt-bg-surface vt-border",
        "border rounded-[var(--radius-lg)] p-5 shadow-sm",
        className,
      )}
      aria-label={`Recomendaciones de Lucas para etapa: ${stageLabel}`}
      aria-busy={isLoading}
    >
      <header className="flex items-center gap-2 mb-4">
        <span
          className="inline-flex items-center justify-center w-6 h-6 rounded-full text-[10px] font-semibold text-white vitalia-agent-gradient-lucas"
          aria-hidden="true"
        >
          LU
        </span>
        <h2 className="text-sm font-semibold vt-text">
          Lucas — Etapa: {stageLabel}
        </h2>
      </header>

      {isLoading && (
        <div className="text-xs vt-text-muted" aria-live="polite">
          Cargando recomendaciones...
        </div>
      )}

      {!isLoading && recommendations.length === 0 && (
        <p className="text-xs vt-text-faint text-center py-2">
          Sin recomendaciones para esta etapa.
          {/* Placeholder — Slice 2 impl */}
        </p>
      )}

      {!isLoading && recommendations.length > 0 && (
        <ul className="space-y-3" aria-label="Lista de recomendaciones">
          {recommendations.map((rec) => (
            <li
              key={rec.id}
              className={cn(
                "p-3 rounded-[var(--radius)] border",
                rec.priority === "high"
                  ? "vt-bg-cian-8 vt-border-cian"
                  : "vt-bg-muted vt-border",
              )}
            >
              <p className="text-sm font-medium vt-text">{rec.title}</p>
              {rec.detail && (
                <p className="text-xs vt-text-muted mt-1">{rec.detail}</p>
              )}
            </li>
          ))}
        </ul>
      )}

      <p className="mt-3 text-xs vt-text-faint italic">
        Implementación completa en Slice 2 (copilot-tools-impl).
      </p>
    </section>
  );
}
