// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase1-s10-TBD
/**
 * AgendaDayHeader — encabezado de columna del día (Lun, Mar, etc.).
 * F1-S10 vitalia-fase1-empty-states — T-7
 *
 * Mockup parity: valeria-agenda-placeholder.html (ratificado Chris batch 2 · 2026-05-26)
 *
 * Server Component — puramente presentacional.
 * Named export (NO default) per FSD-Lite enforce.
 * No hex colors — Tailwind agent tokens only.
 * Spanish neutro LatAm — sin voseo.
 *
 * today highlight:
 *   - dayLabel color: text-agent-valeria (agentic mode mock)
 *   - dayNum color: text-agent-adrian
 *
 * spec_anchor: 03-arch.md § 3.2 Agenda + 06-tickets.yaml T-7
 * downstream-regression-na: brand-local feature/valeria; no cross-brand consumers
 */

import { cn } from "@/lib/utils";

export interface AgendaDayHeaderProps {
  /** Short day label, e.g. "Lun", "Mar". */
  dayLabel: string;
  /** Day number, e.g. 26. */
  dayNum: number;
  /** Whether this column is today. */
  isToday?: boolean;
  className?: string;
}

/**
 * AgendaDayHeader — column header for a single day in the agenda grid.
 * Server Component.
 */
export function AgendaDayHeader({
  dayLabel,
  dayNum,
  isToday = false,
  className,
}: AgendaDayHeaderProps) {
  return (
    <div
      className={cn(
        "text-center py-2 px-1 border-r border-b border-border bg-muted/20",
        "uppercase tracking-wide",
        className,
      )}
      data-testid={`agenda-day-header-${dayNum}`}
      aria-label={`${dayLabel} ${dayNum}${isToday ? " — hoy" : ""}`}
    >
      {/* Short day label */}
      <span
        className={cn(
          "block text-[10px] font-medium",
          isToday ? "text-agent-valeria" : "text-muted-foreground",
        )}
      >
        {dayLabel}
      </span>

      {/* Day number */}
      <span
        className={cn(
          "block text-[15px] font-bold mt-0.5",
          isToday ? "text-agent-adrian" : "text-foreground",
        )}
      >
        {dayNum}
      </span>
    </div>
  );
}
