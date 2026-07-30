// canon: design-system-canon.md §6.1 · story-origin: core-ds-foundation C2-T2
/**
 * Typography — shared tier NAMES + default scale VALUES cross-brand.
 *
 * NAMES (TYPOGRAPHY_TIERS) = shared contract, RN-5.
 * VALUES (TYPOGRAPHY_SCALE) = cross-brand baseline. Brands may override per-tier
 * in their globals.css @theme --text-{tier}; the arch-test asserts completeness.
 *
 *  - display — page hero / largest
 *  - heading — section titles
 *  - body    — default reading text
 *  - caption — meta / helper text
 *
 * CSS-ship descartado (canon §6.8): TS-only. Brands project via @theme.
 */

export const TYPOGRAPHY_TIERS = Object.freeze(["display", "heading", "body", "caption"] as const);

export type TypographyTier = (typeof TYPOGRAPHY_TIERS)[number];

/**
 * Shared base scale VALUES. Cross-brand default; each brand's @theme may
 * override individual tiers (brand typography identity). The arch-test checks
 * that all tiers are present with size/lineHeight/weight, not that the exact
 * values match (per-brand sizing is intentional).
 */
export const TYPOGRAPHY_SCALE = Object.freeze({
  display: { size: "2.25rem", lineHeight: "2.5rem", weight: "700" },
  heading: { size: "1.5rem", lineHeight: "2rem", weight: "600" },
  body: { size: "1rem", lineHeight: "1.5rem", weight: "400" },
  caption: { size: "0.75rem", lineHeight: "1rem", weight: "400" },
} as const);

export type TypographyScaleEntry = (typeof TYPOGRAPHY_SCALE)[TypographyTier];
