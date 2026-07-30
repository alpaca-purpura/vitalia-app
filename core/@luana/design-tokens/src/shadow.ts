// canon: design-system-canon.md §6.1 · story-origin: core-ds-foundation C2-T2
/**
 * Shadow elevation scale — shared VALUES cross-brand (same idiom as spacing.ts / z-index.ts).
 *
 * Every brand's globals.css @theme mirrors these values as --shadow-{key}.
 * The arch-test (test-ds-single-token-source) asserts no-drift.
 *
 * CSS-ship descartado (canon §6.8): this package ships TS ONLY.
 * Brands project via @theme; NO .css importable emitted from here.
 */

export const SHADOW = Object.freeze({
  none: "none",
  sm: "0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
  md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
  lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
  xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
} as const);

export type ShadowKey = keyof typeof SHADOW;
