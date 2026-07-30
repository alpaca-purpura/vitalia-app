// cap: platform.design-tokens-foundation
// story-origin: vitalia-fase1-s3-TBD
/**
 * tenant-palette.ts — deterministic color palette for tenant badges.
 * F1-S3 vitalia-fase1-tenant-switcher — T-1
 *
 * Maps a tenantId string to one of 6 accessible Tailwind color pairs via
 * a simple charCode sum hash. The mapping is deterministic and stable
 * cross-session (same id → same color every time).
 *
 * Contrast fix forward (03-arch § 2.9 + 01-spec § 11):
 * - cyan-500 (#00b8db) on text-white → fails WCAG AA (2.36:1) → use text-cyan-950
 * - amber-500 on white → fails WCAG AA (4.5:1) → use text-amber-950
 * - lime-500 on white → fails WCAG AA → use text-lime-950
 * - All other entries use text-white (passes ≥4.5:1 on those BGs)
 *
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — cosmetic only, derives from tenantId (not PHI).
 *
 * downstream-regression-na: brand-local lib; no cross-brand consumers
 */

export interface PaletteColor {
  /** Tailwind background class */
  readonly bg: string;
  /** Tailwind text class — WCAG AA compliant with bg */
  readonly text: string;
}

/**
 * 6-entry color palette for tenant badges.
 * Index is determined by `pickPaletteColor` hash function.
 * Shrink-only: do NOT reorder entries (would break existing tenant→color mapping).
 */
export const PALETTE = [
  { bg: "bg-cyan-500", text: "text-cyan-950" },  // #00b8db bg → needs dark text (2.36 white fails WCAG AA)
  { bg: "bg-purple-500", text: "text-white" },
  { bg: "bg-fuchsia-500", text: "text-white" },
  { bg: "bg-amber-500", text: "text-amber-950" },
  { bg: "bg-lime-500", text: "text-lime-950" },
  { bg: "bg-rose-500", text: "text-white" },
] as const satisfies ReadonlyArray<PaletteColor>;

/**
 * Deterministically picks a palette color for a given tenantId.
 *
 * Algorithm: sum of charCodes modulo PALETTE.length.
 * Stable across sessions — same tenantId always maps to same index.
 *
 * @param tenantId - The tenant identifier string
 * @returns A PaletteColor entry from PALETTE
 */
export function pickPaletteColor(tenantId: string): PaletteColor {
  if (!tenantId) return PALETTE[0];
  const hash = tenantId
    .split("")
    .reduce((acc, ch) => acc + ch.charCodeAt(0), 0);
  const index = hash % PALETTE.length;
  return PALETTE[index];
}
