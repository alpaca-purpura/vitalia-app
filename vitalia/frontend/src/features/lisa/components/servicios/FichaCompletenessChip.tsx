// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// FichaCompletenessChip — a small progress chip ("ficha 23/26") showing how
// complete a service record is. Enriches what Adrián can answer; does NOT
// gate the "Activo" toggle (RN-32 — completeness is advisory, not a blocker).
"use client";

import { cn } from "@/lib/cn";

interface FichaCompletenessChipProps {
  filled: number;
  total: number;
  /** Tooltip text listing which fields are still missing (advisory). */
  title?: string;
  className?: string;
}

export function FichaCompletenessChip({
  filled,
  total,
  title,
  className,
}: FichaCompletenessChipProps) {
  const pct = total > 0 ? Math.round((filled / total) * 100) : 0;

  return (
    <span
      data-testid="completeness-chip"
      role="progressbar"
      aria-label="Completitud de la ficha"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      title={title}
      className={cn(
        "inline-flex cursor-help items-center gap-1.5 whitespace-nowrap text-xs text-muted-foreground",
        className,
      )}
    >
      <span className="inline-block h-1.5 w-[54px] shrink-0 overflow-hidden rounded-full bg-muted">
        <span
          className="block h-full rounded-full bg-agent-lisa transition-[width] duration-300"
          style={{ width: `${pct}%` }}
        />
      </span>
      <span>
        ficha <span data-testid="cc-count">{`${filled}/${total}`}</span>
      </span>
    </span>
  );
}
