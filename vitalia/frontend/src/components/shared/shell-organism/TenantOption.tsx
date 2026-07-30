// cap: shell-organism.shell-vitalia
// story-origin: vitalia-fase1-s3-TBD
/**
 * TenantOption — tenant row molecule for the dropdown list.
 * F1-S3 vitalia-fase1-tenant-switcher — T-3
 *
 * Server Component (no "use client").
 * Renders: TenantBadge (left) + name + city column (center) + Check (right, when active).
 *
 * Active state styling: bg-accent/40 background.
 * Inactive state styling: hover:bg-muted on hover.
 * data-testid: tenant-option-{tenantId} for Playwright selectors.
 * data-active: "true" | "false" for E2E assertions.
 *
 * 03-arch.md § 2.4 — implementation verbatim.
 * Named export (no default export) per FSD-Lite enforce.
 * HIPAA-lite: no-phi-scope — tenant/clinic name is NOT PHI.
 *
 * downstream-regression-na: brand-local shell-organism molecule; no cross-brand consumers
 */

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { TenantBadge } from "./TenantBadge";
import type { Tenant } from "./types";

export interface TenantOptionProps {
  /** The tenant to display */
  tenant: Tenant;
  /** Whether this is the currently active tenant */
  active: boolean;
}

/**
 * TenantOption — row component for the tenant list inside the dropdown.
 * Server Component.
 */
export function TenantOption({ tenant, active }: TenantOptionProps) {
  return (
    <div
      data-testid={`tenant-option-${tenant.id}`}
      data-active={String(active)}
      className={cn(
        "flex w-full items-center gap-3 rounded-sm px-2 py-2",
        active ? "bg-accent/40" : "hover:bg-muted",
      )}
    >
      <TenantBadge tenant={tenant} />

      {/* Name + city column */}
      <div className="flex min-w-0 flex-1 flex-col">
        <span className="truncate text-sm font-medium text-foreground">
          {tenant.name}
        </span>
        {tenant.city ? (
          <span className="truncate text-xs text-muted-foreground">
            {tenant.city}
          </span>
        ) : null}
      </div>

      {/* Active indicator */}
      {active ? (
        <>
          <Check
            className="size-4 shrink-0 text-foreground"
            aria-hidden="true"
          />
          <span className="sr-only">Clínica activa</span>
        </>
      ) : null}
    </div>
  );
}
