// cap: platform.lift-shell-chrome-ui-kit
/**
 * StatusDot — color indicator dot (T-K2 port, brand-agnostic).
 *
 * VERBATIM port of vitalia StatusDot. Generic by construction (the variant
 * classes are semantic Tailwind colors, NOT agent/brand tokens), so the body
 * is unchanged; only the cn import is re-pointed to @luana/format/utils.
 *
 * Server Component — purely presentational, no state.
 */

import { cn } from "@luana/format/utils";

export type StatusDotVariant = "green" | "yellow" | "gray";

export interface StatusDotProps {
  /** Color variant */
  variant: StatusDotVariant;
  /** Optional accessible label (aria-label) */
  label?: string;
  className?: string;
}

const VARIANT_CLASSES: Record<StatusDotVariant, string> = {
  green: "bg-green-500",
  yellow: "bg-yellow-500",
  gray: "bg-gray-400",
};

/**
 * StatusDot — small circular color indicator.
 * Server Component.
 */
export function StatusDot({ variant, label, className }: StatusDotProps) {
  return (
    <span
      role="img"
      aria-label={label ?? variant}
      data-testid={`status-dot-${variant}`}
      className={cn(
        "inline-block h-2 w-2 shrink-0 rounded-full",
        VARIANT_CLASSES[variant],
        className,
      )}
    />
  );
}
