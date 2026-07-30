// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s3-TBD
/**
 * TenantBadge — tenant initials badge atom.
 * F1-S3 vitalia-fase1-tenant-switcher — T-2
 *
 * Server Component (no "use client").
 * Renders a 2-character initials badge with a deterministic background color
 * derived from the tenant ID via pickPaletteColor (tenant-palette.ts).
 *
 * Initials: first character of each word (max 2), uppercased.
 * Fallback: "?" when tenant name is empty.
 *
 * aria-hidden=true: decorative element — TenantOption provides accessible name via sr-only.
 *
 * 03-arch.md § 2.3 — implementation verbatim.
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — tenant name is NOT PHI (business entity, not patient data).
 *
 * downstream-regression-na: brand-local shell-organism atom; no cross-brand consumers
 */

import { cn } from "@/lib/utils";
import { pickPaletteColor } from "@/lib/tenant-palette";
import type { Tenant } from "./types";

export interface TenantBadgeProps {
  /** The tenant to display initials and color for */
  tenant: Tenant;
  /** Additional CSS classes to apply */
  className?: string;
}

/**
 * Derives 2-character uppercase initials from a tenant name.
 * Takes the first character of each word (up to 2 words).
 * Falls back to "?" for empty names.
 */
function getInitials(name: string): string {
  if (!name.trim()) return "?";
  return (
    name
      .split(/\s+/)
      .slice(0, 2)
      .map((word) => word[0]?.toUpperCase() ?? "")
      .join("") || "?"
  );
}

/**
 * TenantBadge — circular/rounded badge showing tenant initials.
 * Server Component.
 */
export function TenantBadge({ tenant, className }: TenantBadgeProps) {
  const { bg, text } = pickPaletteColor(tenant.id);
  const initials = getInitials(tenant.name);

  return (
    <span
      aria-hidden="true"
      className={cn(
        "inline-flex size-6 shrink-0 items-center justify-center rounded text-xs font-bold",
        bg,
        text,
        className,
      )}
    >
      {initials}
    </span>
  );
}
