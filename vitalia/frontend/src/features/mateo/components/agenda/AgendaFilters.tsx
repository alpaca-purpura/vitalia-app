// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase1-s10-TBD
/**
 * AgendaFilters — fila de 6 chips de filtro visual (disabled F1).
 * F1-S10 vitalia-fase1-empty-states — T-7
 *
 * Mockup parity: valeria-agenda-placeholder.html (ratificado Chris batch 2 · 2026-05-26)
 *
 * Server Component — solo visual, sin estado. F2 cablea Zustand useAgendaFilters.
 * Named export (NO default) per FSD-Lite enforce.
 * No hex colors — Tailwind semantic tokens only.
 * Spanish neutro LatAm — sin voseo.
 *
 * spec_anchor: 03-arch.md § 3.2 Agenda + 06-tickets.yaml T-7
 * downstream-regression-na: brand-local feature/valeria; no cross-brand consumers
 */

import { cn } from "@/lib/utils";

export interface AgendaFiltersProps {
  className?: string;
}

/**
 * AgendaFilters — 6 chips de filtro deshabilitados (F1 placeholder visual).
 * Server Component.
 */
export function AgendaFilters({ className }: AgendaFiltersProps) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 flex-wrap px-4 py-2.5 border-b border-border bg-muted/30",
        className,
      )}
      data-testid="agenda-filters"
      aria-label="Filtros de agenda (disponibles en Fase 2)"
    >
      {/* Buscar paciente — input disabled */}
      <div className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-md bg-background text-[11px] text-muted-foreground">
        <span aria-hidden="true">🔍</span>
        <input
          type="text"
          placeholder="Buscar paciente"
          disabled
          aria-label="Buscar paciente (disponible en Fase 2)"
          className="bg-transparent outline-none text-xs w-28 cursor-not-allowed placeholder:text-muted-foreground/60"
        />
      </div>

      {/* Doctor filter chip */}
      <button
        type="button"
        disabled
        aria-label="Filtrar por doctor (disponible en Fase 2)"
        className="inline-flex items-center gap-1 px-3 py-1.5 border border-border rounded-md bg-background text-[11px] text-muted-foreground cursor-not-allowed opacity-70 hover:bg-muted transition-colors"
      >
        🩺 Doctor:{" "}
        <strong className="text-foreground font-semibold">Todos</strong>
        <span className="text-[9px] ml-0.5">▾</span>
      </button>

      {/* Especialidad filter chip */}
      <button
        type="button"
        disabled
        aria-label="Filtrar por especialidad (disponible en Fase 2)"
        className="inline-flex items-center gap-1 px-3 py-1.5 border border-border rounded-md bg-background text-[11px] text-muted-foreground cursor-not-allowed opacity-70 hover:bg-muted transition-colors"
      >
        📋 Especialidad:{" "}
        <strong className="text-foreground font-semibold">Todas</strong>
        <span className="text-[9px] ml-0.5">▾</span>
      </button>

      {/* Status pago filter chip */}
      <button
        type="button"
        disabled
        aria-label="Filtrar por estado de pago (disponible en Fase 2)"
        className="inline-flex items-center gap-1 px-3 py-1.5 border border-border rounded-md bg-background text-[11px] text-muted-foreground cursor-not-allowed opacity-70 hover:bg-muted transition-colors"
      >
        💰 Status pago:{" "}
        <strong className="text-foreground font-semibold">Todos</strong>
        <span className="text-[9px] ml-0.5">▾</span>
      </button>

      {/* Solo riesgo no-show checkbox */}
      <label className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-md bg-muted/50 text-[11px] text-muted-foreground cursor-not-allowed opacity-70">
        <input
          type="checkbox"
          disabled
          aria-label="Solo riesgo no-show (disponible en Fase 2)"
          className="w-3 h-3 cursor-not-allowed"
        />
        Solo riesgo no-show
      </label>

      {/* Solo walk-in checkbox */}
      <label className="inline-flex items-center gap-1.5 px-3 py-1.5 border border-border rounded-md bg-muted/50 text-[11px] text-muted-foreground cursor-not-allowed opacity-70">
        <input
          type="checkbox"
          disabled
          aria-label="Solo walk-in (disponible en Fase 2)"
          className="w-3 h-3 cursor-not-allowed"
        />
        Solo walk-in
      </label>
    </div>
  );
}
