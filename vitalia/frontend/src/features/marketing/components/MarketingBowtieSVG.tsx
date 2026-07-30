// cap: public_landing.public-clinic-landing
// story-origin: TBD
/**
 * MarketingBowtieSVG — SVG bowtie funnel visualization (pixel-invariante per mockup v1 Batch 6).
 * Renders 5 ellipse stages connected by arrows using vitalia CSS var color tokens.
 *
 * Promoted from scaffold (components/shared/marketing/) to real implementation
 * consuming useBowtieSummary data.
 *
 * @see 02-design-ui-mockup.html (viewBox="0 0 900 180", ellipse geometry per stage)
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */
"use client";

import { cn } from "@/lib/cn";
import type { BowtieStage } from "../types/bowtie";
import { MARKETING_COPY } from "../copy";

// Stage ellipse geometry per mockup (cx, cy, rx, ry) — pixel-invariante
const STAGE_GEOMETRY = [
  { cx: 100, cy: 90, rx: 70, ry: 55 }, // attraction — widest left
  { cx: 290, cy: 90, rx: 50, ry: 40 }, // qualification
  { cx: 450, cy: 90, rx: 35, ry: 28 }, // reservation — narrowest pivot
  { cx: 600, cy: 90, rx: 50, ry: 40 }, // adoption
  { cx: 800, cy: 90, rx: 70, ry: 55 }, // expansion — widest right
] as const;

// Arrow connector x1/x2 pairs per mockup
const ARROW_CONNECTORS = [
  { x1: 170, x2: 240 },
  { x1: 340, x2: 400 },
  { x1: 485, x2: 545 },
  { x1: 650, x2: 710 },
] as const;

// Count label font sizes per stage (larger for wider ellipses)
const COUNT_FONT_SIZES = [22, 18, 15, 18, 22] as const;

const STAGE_COUNT_SUBLABELS: readonly string[] = [
  "leads",
  "leads",
  "res",
  "adop",
  "re-eng",
];

export type MarketingBowtieSVGProps = {
  stages?: BowtieStage[];
  isLoading?: boolean;
  className?: string;
  /** viewBox width — fixed at 900 per mockup */
  width?: number;
  /** viewBox height — fixed at 180 per mockup */
  height?: number;
};

export function MarketingBowtieSVG({
  stages = [],
  isLoading = false,
  className,
}: MarketingBowtieSVGProps) {
  const hasData = stages.length > 0;

  return (
    <figure
      className={cn("w-full", className)}
      aria-label={MARKETING_COPY.bowtie.title}
    >
      <svg
        viewBox="0 0 900 180"
        className="w-full"
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label={
          isLoading
            ? MARKETING_COPY.bowtie.loadingMessage
            : hasData
              ? MARKETING_COPY.bowtie.title
              : MARKETING_COPY.bowtie.emptyMessage
        }
        aria-busy={isLoading}
      >
        <defs>
          {/* arrowhead marker — uses pre-computed CSS var (no hsl() in TSX) */}
          <marker
            id="mktg-arrowhead"
            markerWidth="10"
            markerHeight="7"
            refX="9"
            refY="3.5"
            orient="auto"
          >
            <polygon
              points="0 0, 10 3.5, 0 7"
              fill="var(--vitalia-text-muted-color)"
            />
          </marker>

          {/* Gradient for stages 1-4: cian → azul-marino */}
          <linearGradient
            id="mktg-grad-acquisition"
            x1="0"
            y1="0"
            x2="1"
            y2="1"
          >
            <stop offset="0%" stopColor="var(--vitalia-cian-color)" />
            <stop offset="100%" stopColor="var(--vitalia-azul-marino-color)" />
          </linearGradient>

          {/* Gradient for stage 5 (expansion): cian → purpura → verde-lima */}
          <linearGradient id="mktg-grad-expansion" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--vitalia-cian-color)" />
            <stop offset="50%" stopColor="var(--vitalia-purpura-color)" />
            <stop offset="100%" stopColor="var(--vitalia-verde-lima-color)" />
          </linearGradient>
        </defs>

        {/* Arrow connectors between stages */}
        {ARROW_CONNECTORS.map(({ x1, x2 }, i) => (
          <line
            key={`arrow-${i}`}
            x1={x1}
            y1={90}
            x2={x2}
            y2={90}
            stroke="var(--vitalia-text-muted-color)"
            strokeWidth={2}
            fill="none"
            markerEnd="url(#mktg-arrowhead)"
            aria-hidden="true"
          />
        ))}

        {/* Stage ellipses */}
        {STAGE_GEOMETRY.map(({ cx, cy, rx, ry }, i) => {
          const stage = stages[i];
          const isExpansion = i === 4;
          const gradientId = isExpansion
            ? "mktg-grad-expansion"
            : "mktg-grad-acquisition";
          const opacity = isExpansion ? 0.85 : [0.85, 0.7, 0.6, 0.7, 0.85][i];
          const countLabel = stage?.count ?? (isLoading ? "…" : "—");
          const kpiLabel =
            stage?.primaryKpiValue != null
              ? `${stage.primaryKpiLabel} ${stage.primaryKpiValue}`
              : null;
          const countFontSize = COUNT_FONT_SIZES[i];
          const countSubLabel = STAGE_COUNT_SUBLABELS[i];

          return (
            <g key={`stage-${i}`} aria-label={stage?.label ?? `Etapa ${i + 1}`}>
              <ellipse
                cx={cx}
                cy={cy}
                rx={rx}
                ry={ry}
                fill={`url(#${gradientId})`}
                opacity={opacity}
              />
              {/* Count metric label */}
              <text
                x={cx}
                y={cy - 12}
                fontSize={countFontSize}
                fontWeight={700}
                fill="white"
                textAnchor="middle"
              >
                {countLabel}
              </text>
              {/* Count sub-label (leads/res/adop/re-eng) */}
              <text
                x={cx}
                y={cy + 8}
                fontSize={i === 0 || i === 4 ? 9 : 8}
                fontWeight={600}
                fill="white"
                textAnchor="middle"
              >
                {countSubLabel}
              </text>
              {/* Stage name label below ellipse */}
              <text
                x={cx}
                y={160}
                fontSize={11}
                fontWeight={600}
                fill="var(--vitalia-text-color)"
                textAnchor="middle"
              >
                {stage?.label ?? `Etapa ${i + 1}`}
              </text>
              {/* KPI sub-label below stage name */}
              {kpiLabel && (
                <text
                  x={cx}
                  y={174}
                  fontSize={9}
                  fill="var(--vitalia-text-muted-color)"
                  textAnchor="middle"
                >
                  {kpiLabel}
                </text>
              )}
            </g>
          );
        })}

        {/* Loading overlay */}
        {isLoading && (
          <text
            x={450}
            y={90}
            textAnchor="middle"
            fontSize={13}
            fill="var(--vitalia-text-muted-color)"
          >
            {MARKETING_COPY.bowtie.loadingMessage}
          </text>
        )}

        {/* Empty state */}
        {!isLoading && !hasData && (
          <text
            x={450}
            y={90}
            textAnchor="middle"
            fontSize={13}
            fill="var(--vitalia-text-muted-color)"
          >
            {MARKETING_COPY.bowtie.emptyMessage}
          </text>
        )}
      </svg>
    </figure>
  );
}

MarketingBowtieSVG.displayName = "MarketingBowtieSVG";
