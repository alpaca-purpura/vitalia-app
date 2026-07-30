// cap: platform.design-tokens-foundation
// story-origin: TBD
/**
 * cn — lightweight utility for conditional Tailwind class merging.
 * Mirrors Shadcn `cn()` pattern without requiring clsx/tailwind-merge.
 * Usage: cn("base", condition && "active", className)
 */
export function cn(
  ...classes: (string | boolean | undefined | null)[]
): string {
  return classes.filter(Boolean).join(" ");
}
