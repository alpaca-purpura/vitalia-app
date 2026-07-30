// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AgendaCalendar.tsx — Calendar view dispatcher (Day / Week / Month).
 * T-13 vitalia-fase2-valeria-agenda · F2-S1
 *
 * Reads current view from useAgendaFilters and renders the appropriate variant:
 *   - "dia"    → DayCalendar (+ react-window when >50 slots, A4)
 *   - "semana" → WeekCalendar (default, 7-day grid, A1)
 *   - "mes"    → MonthCalendar (aggregate dots, A5)
 *   - isLoading → SkeletonCalendar
 *
 * On slot click → calls onSlotClick(appointmentId).
 * On month-day click → calls onDayClick(date) [optional, triggers view change].
 *
 * Spanish neutro LatAm — sin voseo.
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.5 + 06-tickets.yaml T-13
 */

import { useCallback } from "react";
import { cn } from "@/lib/cn";
import { DayCalendar } from "./DayCalendar";
import { WeekCalendar } from "./WeekCalendar";
import { MonthCalendar } from "./MonthCalendar";
import { SkeletonCalendar } from "./SkeletonCalendar";
import { useAgendaFilters } from "../../hooks/useAgendaFilters";
import type { AgendaSlot } from "../../types/agenda.types";
import type { MonthAggregates } from "./MonthCalendar";

// ── Props ─────────────────────────────────────────────────────────────────────

export interface AgendaCalendarProps {
  /** Slots for the current view (filtered by date + preset by server). */
  slots: AgendaSlot[];
  /** Tenant ID (HIPAA dual filter — passed to sub-calendars). */
  tenantId: string;
  /** Month aggregates — required when view="mes" (A5). */
  monthAggregates?: MonthAggregates | null;
  /** True during initial load — shows SkeletonCalendar. */
  isLoading?: boolean;
  /**
   * Called with appointmentId when a slot is clicked.
   * Parent (MateoAgendaView) opens AppointmentDrawer.
   */
  onSlotClick?: (appointmentId: string) => void;
  /**
   * Called when a month-view day cell is clicked.
   * Parent can switch to DayCalendar for that date.
   */
  onDayClick?: (date: string) => void;
  /**
   * T-FE-1: Called when an empty time slot is clicked.
   * Parent (MateoAgendaView) pushes to /nueva-cita?date=&time=
   */
  onEmptySlotClick?: (date: string, time: string) => void;
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Calendar view dispatcher.
 *
 * Reads `view` from useAgendaFilters (URL SSoT) and renders
 * the appropriate calendar variant.
 *
 * isLoading=true → SkeletonCalendar (pre-load / initial fetch)
 * view="semana"  → WeekCalendar (7-day grid)
 * view="dia"     → DayCalendar (timeline, react-window when >50)
 * view="mes"     → MonthCalendar (aggregate dots, no slot list)
 */
export function AgendaCalendar({
  slots,
  tenantId,
  monthAggregates = null,
  isLoading = false,
  onSlotClick,
  onDayClick,
  onEmptySlotClick,
  className,
}: AgendaCalendarProps) {
  const { view, date } = useAgendaFilters();

  const handleSlotClick = useCallback(
    (appointmentId: string) => {
      onSlotClick?.(appointmentId);
    },
    [onSlotClick],
  );

  const handleDayClick = useCallback(
    (clickedDate: string) => {
      onDayClick?.(clickedDate);
    },
    [onDayClick],
  );

  const handleEmptySlotClick = useCallback(
    (emptyDate: string, emptyTime: string) => {
      onEmptySlotClick?.(emptyDate, emptyTime);
    },
    [onEmptySlotClick],
  );

  // Show skeleton during initial load
  if (isLoading) {
    return <SkeletonCalendar className={className} />;
  }

  // Dispatch to the appropriate calendar variant
  return (
    <div className={cn("flex-1 overflow-hidden", className)}>
      {view === "dia" && (
        <DayCalendar
          slots={slots}
          date={date}
          tenantId={tenantId}
          onSlotClick={handleSlotClick}
          onEmptySlotClick={handleEmptySlotClick}
        />
      )}

      {view === "semana" && (
        <WeekCalendar
          slots={slots}
          date={date}
          tenantId={tenantId}
          onSlotClick={handleSlotClick}
          onEmptySlotClick={handleEmptySlotClick}
        />
      )}

      {view === "mes" && (
        <MonthCalendar
          tenantId={tenantId}
          date={date}
          aggregates={monthAggregates}
          onDayClick={handleDayClick}
        />
      )}
    </div>
  );
}
