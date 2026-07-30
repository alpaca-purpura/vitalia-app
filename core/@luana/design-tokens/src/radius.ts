// canon: design-system-canon.md §6.1 · story-origin: core-ds-foundation C2-T2
/**
 * Radius — shared NAMES + scale RELATIONSHIPS cross-brand.
 *
 * NAMES (RADIUS_NAMES) = shared contract, RN-5.
 * SCALE (RADIUS_SCALE) = calc()-based relationships relative to each brand's
 *   `--radius` base value (magnitude stays per-brand). Brands declare their
 *   --radius in globals.css :root; RADIUS_SCALE provides the delta template.
 *
 *  - sm / md / lg  — surface scale (cards, inputs, sheets)
 *  - bubble        — chat bubble radius (agent surfaces)
 *  - pill          — fully-rounded chips / toggles
 *  - control       — brand-overridable control-atom radius (Button/Input/Select/Textarea).
 *                    Each brand sets `--radius-control` in globals.css. Brands that omit
 *                    the token fall back to `var(--radius)` (= current md behaviour, RN-7).
 *
 * CSS-ship descartado (canon §6.8): TS-only. Brands project via @theme.
 */

export const RADIUS_NAMES = Object.freeze(["sm", "md", "lg", "bubble", "pill", "control"] as const);

export type RadiusName = (typeof RADIUS_NAMES)[number];

/**
 * Shared scale RELATIONSHIPS — calc expressions relative to `--radius` base.
 * Brands follow these deltas in their @theme. `bubble` and `pill` are
 * brand-owned absolute values (not delta-based), so they are omitted here.
 *
 * control = md − 2px (RN-7): sits between sm (md-4px) and md (base).
 */
export const RADIUS_SCALE = Object.freeze({
  sm: "calc(var(--radius) - 4px)",
  md: "var(--radius)",
  lg: "calc(var(--radius) + 4px)",
  control: "calc(var(--radius) - 2px)", // ponytail: RN-7 DECOUPLED — brands may override in :root
} as const);

export type RadiusScaleKey = keyof typeof RADIUS_SCALE;
