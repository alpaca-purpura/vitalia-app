// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase1-s10-TBD
/**
 * AgendaSummaryFooter — footer con leyenda de status + resumen Adrián+Lucas.
 * F1-S10 vitalia-fase1-empty-states — T-7
 *
 * Mockup parity: valeria-agenda-placeholder.html (ratificado Chris batch 2 · 2026-05-26)
 *
 * Server Component — puramente presentacional.
 * Named export (NO default) per FSD-Lite enforce.
 * No hex colors — Tailwind semantic tokens only.
 * Spanish neutro LatAm — sin voseo.
 *
 * spec_anchor: 03-arch.md § 3.2 Agenda + 06-tickets.yaml T-7
 * downstream-regression-na: brand-local feature/valeria; no cross-brand consumers
 */

import { cn } from "@/lib/utils";

export interface AgendaSummaryFooterProps {
  /** How many appointments Adrián proposed today (mock: 4). */
  proposalsToday?: number;
  /** How many without payment (mock: 3). */
  unpaidCount?: number;
  /** How many leads ready from Lucas (mock: 3). */
  leadsReadyCount?: number;
  className?: string;
}

/** Status legend items */
const STATUS_LEGEND = [
  { color: "bg-[color:var(--vitalia-success-color)]", label: "Pagado" },
  { color: "bg-agent-adrian", label: "30% depósito" },
  { color: "bg-amber-500", label: "Sin pago" },
  { color: "bg-red-500", label: "No-show riesgo" },
] as const;

/**
 * AgendaSummaryFooter — status legend + Adrián+Lucas summary text.
 * Server Component.
 */
export function AgendaSummaryFooter({
  proposalsToday = 4,
  unpaidCount = 3,
  leadsReadyCount = 3,
  className,
}: AgendaSummaryFooterProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between flex-wrap gap-3 px-4 py-2.5 border-t border-border text-[11px]",
        className,
      )}
      data-testid="agenda-summary-footer"
    >
      {/* Left: status legend + origin icons hint */}
      <div className="flex items-center gap-3 flex-wrap">
        <span className="text-[9px] font-semibold uppercase tracking-wide text-muted-foreground">
          Leyenda
        </span>

        {STATUS_LEGEND.map(({ color, label }) => (
          <span
            key={label}
            className="flex items-center gap-1.5 text-foreground"
          >
            <span
              className={cn(
                "inline-block w-2.5 h-2.5 rounded-full shrink-0",
                color,
              )}
              aria-hidden="true"
            />
            {label}
          </span>
        ))}

        <span className="text-muted-foreground">
          🚶 walk-in · 📞 phone · ✉ proactiva
        </span>
      </div>

      {/* Right: Adrián + Lucas summary */}
      <div
        className="text-muted-foreground italic text-right"
        data-testid="agenda-summary-text"
      >
        <span className="font-semibold text-agent-adrian">Adrián</span> propuso{" "}
        {proposalsToday} turnos hoy · {unpaidCount} sin pago ·{" "}
        <span className="font-semibold text-agent-lucas">Lucas</span>:{" "}
        {leadsReadyCount} leads listos
      </div>
    </div>
  );
}
