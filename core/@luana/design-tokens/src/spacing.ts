// canon: design-system-canon.md §6.1 · story-origin: core-ds-foundation
/**
 * Spacing scale — Tailwind 4px-base ladder, AS-IS (D1, RN-4).
 *
 * IDENTICAL cross-brand: a token VALUE, not just a name. Every brand shares
 * the same rhythm so layouts compose the same. Same frozen idiom as z-index.ts.
 */
export const SPACING = Object.freeze({
  "0": "0",
  "1": ".25rem", // 4px
  "2": ".5rem", // 8px
  "3": ".75rem", // 12px
  "4": "1rem", // 16px
  "5": "1.25rem", // 20px
  "6": "1.5rem", // 24px
  "8": "2rem", // 32px
  "10": "2.5rem", // 40px
  "12": "3rem", // 48px
  "16": "4rem", // 64px
} as const);

export type SpacingKey = keyof typeof SPACING;
