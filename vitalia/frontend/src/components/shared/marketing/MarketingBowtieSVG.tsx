// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * MarketingBowtieSVG — marketing attribution funnel bowtie visualization.
 *
 * Scaffold stub. Full implementation (with real funnel data + animations)
 * arrives in growth-studio story (Slice 2+).
 *
 * Shape: two triangles meeting at a center point — classic Bowtie model:
 *   [Awareness → Consideration → Decision]|[Retention → Expansion → Advocacy]
 *
 * All colors via vt-* CSS classes / Tailwind tokens (no hsl literals here).
 * SVG gradients reference CSS custom properties defined in globals.css.
 */

import { cn } from "@/lib/cn";

export interface BowtieStage {
  /** Stage key */
  id: string;
  /** Display label (Spanish neutro) */
  label: string;
  /** Value count */
  value: number;
  /** Funnel side */
  side: "acquisition" | "retention";
}

export interface MarketingBowtieSVGProps {
  /** Acquisition funnel stages (left of center) */
  acquisitionStages?: BowtieStage[];
  /** Retention funnel stages (right of center) */
  retentionStages?: BowtieStage[];
  /** Whether data is loading */
  isLoading?: boolean;
  /** SVG width in pixels */
  width?: number;
  /** SVG height in pixels */
  height?: number;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Bowtie SVG visualization — scaffold placeholder.
 * Renders labeled placeholder until Slice 2+ full impl.
 */
export function MarketingBowtieSVG({
  acquisitionStages = [],
  retentionStages = [],
  isLoading = false,
  width = 480,
  height = 200,
  className,
}: MarketingBowtieSVGProps) {
  const hasData = acquisitionStages.length > 0 || retentionStages.length > 0;

  return (
    <figure
      className={cn("flex flex-col items-center gap-2", className)}
      aria-label="Embudo de atribución marketing (Bowtie)"
      aria-busy={isLoading}
    >
      {isLoading ? (
        <div
          className="flex items-center justify-center vt-bg-muted rounded-[var(--radius-lg)]"
          style={{ width, height }}
          aria-live="polite"
        >
          <span className="text-xs vt-text-muted">Cargando métricas...</span>
        </div>
      ) : (
        <svg
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          role="img"
          aria-label="Bowtie de atribución — embudo de adquisición y retención"
        >
          <defs>
            {/* Gradient references CSS custom properties from globals.css */}
            <linearGradient id="bowtie-acq" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop
                offset="0%"
                stopColor="var(--vitalia-cian-color)"
                stopOpacity="0.9"
              />
              <stop
                offset="100%"
                stopColor="var(--vitalia-cian-color)"
                stopOpacity="0.3"
              />
            </linearGradient>
            <linearGradient id="bowtie-ret" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop
                offset="0%"
                stopColor="var(--vitalia-purpura-color)"
                stopOpacity="0.3"
              />
              <stop
                offset="100%"
                stopColor="var(--vitalia-purpura-color)"
                stopOpacity="0.9"
              />
            </linearGradient>
          </defs>

          {/* Acquisition funnel (left triangle) */}
          <polygon
            points={`0,10 ${width / 2 - 4},${height / 2} 0,${height - 10}`}
            fill="url(#bowtie-acq)"
            aria-label="Embudo adquisición"
          />

          {/* Retention funnel (right triangle) */}
          <polygon
            points={`${width / 2 + 4},${height / 2} ${width},10 ${width},${height - 10}`}
            fill="url(#bowtie-ret)"
            aria-label="Embudo retención"
          />

          {/* Center node */}
          <circle
            cx={width / 2}
            cy={height / 2}
            r={8}
            fill="var(--vitalia-cian-color)"
            aria-label="Punto de conversión"
          />

          {/* Axis labels */}
          <text
            x={10}
            y={height - 4}
            fontSize="10"
            fill="var(--vitalia-text-muted-color)"
            aria-hidden="true"
          >
            Adquisición
          </text>
          <text
            x={width - 80}
            y={height - 4}
            fontSize="10"
            fill="var(--vitalia-text-muted-color)"
            aria-hidden="true"
          >
            Retención
          </text>

          {/* Placeholder text when no real data */}
          {!hasData && (
            <text
              x={width / 2}
              y={height / 2 - 20}
              textAnchor="middle"
              fontSize="11"
              fill="var(--vitalia-text-faint-color)"
              aria-hidden="true"
            >
              Slice 2 — datos reales pendientes
            </text>
          )}
        </svg>
      )}

      <figcaption className="text-xs vt-text-faint text-center">
        Modelo Bowtie — adquisición y retención
      </figcaption>
    </figure>
  );
}
