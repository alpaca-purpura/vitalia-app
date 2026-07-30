// cap: patients.nps-tracking
// story-origin: TBD
"use client";

/**
 * NPSRowCompact — table row for NPS reduced view.
 *
 * PHI: patient name guarded by RequireRole + PiiMaskedSpan.
 * Reuses NPSTagBadge from shared/nps.
 *
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 */

import { cn } from "@/lib/cn";
import { NPSTagBadge } from "@/components/shared/nps";
import { RequireRole } from "@/components/shared/phi";
import { PiiMaskedSpan } from "@/components/shared/phi";
import { formatTenantDate } from "@/lib/format/formatTenantDate";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { useCurrentUser } from "@/hooks/useCurrentUser";
import type { NPSRowDTO } from "../types/nps";

interface NPSRowCompactProps {
  row: NPSRowDTO;
  className?: string;
}

/**
 * Compact NPS row for NPS tab table.
 */
export function NPSRowCompact({ row, className }: NPSRowCompactProps) {
  const { role } = useCurrentUser();
  const { timezone } = useTenantLocale();

  return (
    <li
      className={cn(
        "flex items-start gap-3 border-b border-[hsl(var(--vitalia-border,220_13%_91%))] py-3 last:border-b-0",
        className,
      )}
    >
      {/* NPS badge */}
      <div className="shrink-0">
        <NPSTagBadge score={row.score} />
      </div>

      {/* Patient name — PHI guarded */}
      <div className="min-w-0 flex-1">
        <RequireRole
          roles={["doctor", "nurse", "admin_clinic"]}
          userRole={role}
          fallback={
            <PiiMaskedSpan
              value={row.patientName}
              fieldType="name"
              className="text-sm"
            />
          }
        >
          <p className="truncate text-sm font-medium text-[hsl(var(--vitalia-fg,220_25%_15%))]">
            {row.patientName}
          </p>
        </RequireRole>

        {row.commentShort && (
          <p className="mt-0.5 truncate text-xs text-[hsl(var(--vitalia-muted,220_10%_55%))]">
            {row.commentShort}
          </p>
        )}
      </div>

      {/* Date */}
      <time
        dateTime={row.respondedAt}
        className="shrink-0 text-xs text-[hsl(var(--vitalia-muted,220_10%_55%))]"
      >
        {formatTenantDate(row.respondedAt, timezone)}
      </time>
    </li>
  );
}
