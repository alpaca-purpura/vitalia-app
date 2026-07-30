// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AgendaPresetFilters.tsx — 5 preset filter chips with URL param sync.
 * T-16 vitalia-fase2-valeria-agenda
 *
 * Single-select chips. Active chip highlights in agent-valeria color.
 * Click active chip → clear filter (toggle behavior).
 * Horizontal scroll on mobile via ScrollArea.
 *
 * ARIA: role="switch" aria-checked per spec SC-1.
 * URL SSoT via useAgendaFilters.setPresetFilter → React Query refetch via key change.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 01-spec.md SC-1 + 03-arch.md § 3.2 + 06-tickets.yaml T-16
 */

import * as React from "react";
import { cn } from "@/lib/utils";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { useAgendaFilters } from "../../hooks/useAgendaFilters";
import type { AgendaFilter } from "../../types/agenda.types";

// ── Chip definitions (spec 01-spec.md § 4 microcopy) ─────────────────────────

interface FilterChip {
  filter: AgendaFilter;
  label: string;
  /** Emoji icon prefix per spec. */
  icon: string;
  /** Accessible description for screen readers. */
  ariaLabel: string;
}

const FILTER_CHIPS: FilterChip[] = [
  {
    filter: "today",
    label: "Hoy",
    icon: "📅",
    ariaLabel: "Filtrar citas de hoy",
  },
  {
    filter: "tomorrow_pending",
    label: "Por confirmar mañana",
    icon: "⏰",
    ariaLabel: "Filtrar citas por confirmar mañana",
  },
  {
    filter: "reschedule",
    label: "Re-agendar pendientes",
    icon: "↩️",
    ariaLabel: "Filtrar citas pendientes de re-agendar",
  },
  {
    filter: "no_shows",
    label: "No-shows del día",
    icon: "🚫",
    ariaLabel: "Filtrar no-shows del día",
  },
  {
    filter: "pending_balances",
    label: "Saldos pendientes",
    icon: "💰",
    ariaLabel: "Filtrar pacientes con saldos pendientes",
  },
] as const;

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AgendaPresetFiltersProps {
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * AgendaPresetFilters — horizontal chip row for quick agenda filtering.
 *
 * Each chip maps to an AgendaFilter value stored in URL params.
 * Clicking the active chip clears the filter (toggle off).
 */
export function AgendaPresetFilters({ className }: AgendaPresetFiltersProps) {
  const { presetFilter, setPresetFilter } = useAgendaFilters();

  const handleChipClick = React.useCallback(
    (filter: AgendaFilter) => {
      // Toggle: click active chip → clear; click inactive chip → select
      if (presetFilter === filter) {
        setPresetFilter(null);
      } else {
        setPresetFilter(filter);
      }
    },
    [presetFilter, setPresetFilter],
  );

  return (
    <div
      className={cn(
        "border-b border-border bg-background px-4 py-2",
        className,
      )}
      data-testid="agenda-preset-filters"
    >
      <ScrollArea className="w-full whitespace-nowrap">
        {/* role="group" with label to announce filter set to screen readers */}
        <div
          role="group"
          aria-label="Filtros rápidos de agenda"
          className="flex gap-2 pb-2"
        >
          {FILTER_CHIPS.map(({ filter, label, icon, ariaLabel }) => {
            const isActive = presetFilter === filter;

            return (
              <button
                key={filter}
                type="button"
                role="switch"
                aria-checked={isActive}
                aria-label={ariaLabel}
                data-testid={`preset-chip-${filter}`}
                onClick={() => handleChipClick(filter)}
                className={cn(
                  // Base chip styles
                  "inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-medium",
                  "border transition-all duration-150 whitespace-nowrap",
                  "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                  "select-none cursor-pointer",
                  // Active state: agent-valeria accent (Tailwind utility classes)
                  isActive
                    ? "border-agent-valeria bg-agent-valeria-soft text-agent-valeria"
                    : "border-border bg-background text-muted-foreground hover:bg-muted hover:text-foreground hover:border-border",
                )}
              >
                <span aria-hidden="true">{icon}</span>
                {label}
              </button>
            );
          })}
        </div>
        <ScrollBar orientation="horizontal" />
      </ScrollArea>
    </div>
  );
}
