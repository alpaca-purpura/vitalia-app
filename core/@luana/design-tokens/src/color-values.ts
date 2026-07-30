// canon: design-system-canon.md §6.1 · story-origin: core-ds-foundation C2-T2
/**
 * Semantic color VALUES — shared cross-brand defaults (NOT per-brand palettes — RN-5).
 *
 * Only the 4 STATUS colors (success/warning/danger/info) ship shared VALUES.
 * All other colors (primary, brand, agent-*) remain per-brand in globals.css.
 *
 * Format: "H S% L%" (HSL channel values) — same format as Tailwind v4 + Shadcn.
 * Brands project into @theme as: --color-success: hsl(var(--success))
 * and declare :root { --success: <value>; } using these channels.
 *
 * Contrast contract (canon §2.8): agent accent colors with warm/bright backgrounds
 * require dark foreground text. The AGENT_ACCENT_CONTRAST constant captures the
 * mapping from color family → foreground requirement.
 *
 * CSS-ship descartado (canon §6.8): TS-only. Brands project via @theme.
 */

/**
 * Shared semantic status color defaults (HSL channel format "H S% L%").
 * success/warning/danger/info + their foreground variants.
 *
 * warning-foreground is dark (L=4%) to ensure contrast on amber (canon §2.8).
 */
export const SEMANTIC_COLOR_DEFAULTS = Object.freeze({
  success: "142 71% 45%",
  "success-foreground": "0 0% 98%",
  warning: "38 92% 50%",
  "warning-foreground": "20 14% 4%", // dark — warm/amber background needs dark text (canon §2.8)
  danger: "0 84% 60%",
  "danger-foreground": "0 0% 98%",
  info: "217 91% 60%",
  "info-foreground": "0 0% 98%",
} as const);

export type SemanticColorKey = keyof typeof SEMANTIC_COLOR_DEFAULTS;

/**
 * Agent accent contrast families (canon §2.8).
 *
 * Brands map their per-brand agent token to the family that matches its
 * luminance profile. Consumers of the agent accent color choose their
 * foreground class based on this family mapping.
 *
 * Examples per brand (NOT hardcoded here — per RN-5):
 *   vitalia/agent-mateo (#FEE209 yellow)  → "yellow-warm" → dark-foreground
 *   vitalia/agent-lucas (near-black)       → "dark-neutral" → light-foreground
 *   nicolify/agent-sara (amber #F59E0B)    → "yellow-warm" → dark-foreground
 */
export const AGENT_ACCENT_CONTRAST = Object.freeze({
  "yellow-warm": "dark-foreground", // bright/warm accent bg → dark text
  "dark-neutral": "light-foreground", // dark accent bg → light text
} as const);

export type AgentAccentContrastFamily = keyof typeof AGENT_ACCENT_CONTRAST;
