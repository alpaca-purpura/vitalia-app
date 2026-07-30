// cap: crm.adrian-embudo
// story-origin: vitalia-fase2-adrian-embudo
/**
 * EmbudoFilters — Collapsible filter panel for origin/doctor/etc. (D.2 spec).
 * T-FE-2 vitalia-fase2-adrian-embudo
 *
 * Filters: origen (canal) · doctor · etiquetas · rango fecha · score · operador.
 * Kept simple for this story — filter UI stub (full impl in follow-up if needed).
 *
 * spec_anchor: 01-spec.md § V1 Filtros
 */
"use client";

import type { BoardFilters } from "../../types/embudo.types";

export interface EmbudoFiltersProps {
  filters: Omit<BoardFilters, "view" | "sort">;
  onChange: (filters: Omit<BoardFilters, "view" | "sort">) => void;
}

export function EmbudoFilters({ filters, onChange }: EmbudoFiltersProps) {
  // Filter UI — stub for this story (full filter panel deferred per §spec scope)
  // Anti-creep: §spec out-of-scope: "Editor de customización de etapas per-vertical"
  return (
    <div
      className="flex flex-wrap gap-2 text-xs text-muted-foreground"
      aria-label="Filtros del embudo"
      role="region"
      data-testid="embudo-filters"
    >
      {/* Active filters display */}
      {filters.origin && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-muted">
          Canal: {filters.origin}
          <button
            type="button"
            aria-label={`Quitar filtro canal ${filters.origin}`}
            onClick={() => onChange({ ...filters, origin: null })}
            className="ml-1 hover:text-foreground"
          >
            ×
          </button>
        </span>
      )}
      {filters.search && (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-muted">
          Buscar: {filters.search}
          <button
            type="button"
            aria-label="Quitar filtro búsqueda"
            onClick={() => onChange({ ...filters, search: null })}
            className="ml-1 hover:text-foreground"
          >
            ×
          </button>
        </span>
      )}
    </div>
  );
}
