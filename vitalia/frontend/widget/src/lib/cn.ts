/**
 * cn — lightweight conditional class merger for the widget bundle.
 * Mirrors the Shadcn cn() pattern without requiring clsx/tailwind-merge.
 * Kept minimal to avoid bundle size overhead in the UMD widget.
 */
export function cn(...classes: (string | boolean | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
