// canon: design-system-canon.md §6.1 · story-origin: core-ds-foundation
/**
 * Color token NAME contract — shared semantic + agent token names (RN-5).
 *
 * NAMES only — the hex/HSL VALUE of each token is PER-BRAND (lives in each
 * brand's globals.css). Never merge brand palettes here. A component referencing
 * `agent-lisa` resolves to whatever each brand paints that token.
 *  - surface/semantic: primary, background, foreground, card, muted, border, ring
 *  - per-agent accents: agent-{lisa,lucas,adrian,valeria,camila,mateo,config}
 *  - status: success, warning, danger, info
 */
export const COLOR_NAMES = Object.freeze([
  "primary",
  "background",
  "foreground",
  "card",
  "muted",
  "border",
  "ring",
  "agent-lisa",
  "agent-lucas",
  "agent-adrian",
  "agent-valeria",
  "agent-camila",
  "agent-mateo",
  "agent-config",
  "success",
  "warning",
  "danger",
  "info",
] as const);

export type ColorName = (typeof COLOR_NAMES)[number];
