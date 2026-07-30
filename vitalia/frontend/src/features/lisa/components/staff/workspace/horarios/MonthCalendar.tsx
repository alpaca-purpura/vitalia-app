// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * MonthCalendar.tsx — Month view (6×7 grid) for doctor availability blocks.
 *
 * Architecture:
 *   - Receives currentMonth (YYYY-MM-DD, first of month) as prop — parent owns state.
 *   - Internally navigates prev/next/hoy (local month nav state).
 *   - Data: consumes useAvailabilityOccurrences over [firstVisibleDay, lastVisibleDay].
 *   - Paints EXACTLY the BE-projected occurrences (RN-D3E-1 — zero client expansion).
 *   - Click day → onSwitchToWeek(mondayOfThatWeek) (SC-D3E-2 — nav to week view).
 *   - Overflow: MAX_CHIPS_PER_DAY=2 visible chips + "+N más" label (SC-D3E-4).
 *   - States: skeleton (loading), error+retry, empty (no occurrences), grid (data).
 *   - a11y: role="grid" + role="row" + role="gridcell" + aria-label per day.
 *   - master-data.md: NEVER toLocaleDateString() — Intl.DateTimeFormat("es-419").
 *   - NO writes from this view (RN-D3E-2).
 *
 * T-FE-vista-mes vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-E · validators: RN-D3E-1, RN-D3E-2, SC-D3E-1..4
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import React, { useState, useMemo, useCallback } from "react";
import { ChevronLeft, ChevronRight, Calendar } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAvailabilityOccurrences } from "../../../../api/staff";
import type { AvailabilityOccurrence } from "../../../../types/staff.types";
// bug7 r4: TZ-stable date math SSoT (no toISOString drift). Aliases keep the
// month-view call sites unchanged while sharing ONE implementation.
import {
  parseLocalDate,
  toLocalIsoDate as toIsoDate,
  mondayOfWeek as getMondayOfWeek,
} from "@/lib/format/calendarDates";

// ── Constants ─────────────────────────────────────────────────────────────────

const MAX_CHIPS_PER_DAY = 2;

const DAY_HEADERS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

// ── Date helpers (F6: NEVER toLocaleDateString — Intl.DateTimeFormat) ─────────
// parseLocalDate / toIsoDate / getMondayOfWeek now come from the shared
// calendarDates SSoT (imported above) — single TZ-stable implementation.

/**
 * Add N months to a YYYY-MM-01 date string. Returns YYYY-MM-01.
 */
function addMonths(yearMonth: string, delta: number): string {
  const [y, m] = yearMonth.split("-").map(Number);
  const date = new Date(y!, m! - 1 + delta, 1);
  return toIsoDate(date);
}

/**
 * Get the first day of the visible 6×7 grid for a given month.
 * = Monday of the week containing the 1st of the month.
 */
function getFirstVisibleDay(yearMonthDay: string): string {
  const firstOfMonth = yearMonthDay.substring(0, 7) + "-01";
  return getMondayOfWeek(firstOfMonth);
}

/**
 * Get the last day of the visible 6×7 grid for a given month.
 * = 6 weeks × 7 days from firstVisibleDay (inclusive end: day 41, 0-indexed).
 */
function getLastVisibleDay(firstVisibleDay: string): string {
  const d = parseLocalDate(firstVisibleDay);
  d.setDate(d.getDate() + 41); // 6×7 = 42 cells, last = index 41
  return toIsoDate(d);
}

/**
 * Build the 42 ISO date strings for the 6×7 grid.
 */
function buildGridDays(firstVisibleDay: string): string[] {
  return Array.from({ length: 42 }, (_, i) => {
    const d = parseLocalDate(firstVisibleDay);
    d.setDate(d.getDate() + i);
    return toIsoDate(d);
  });
}

/**
 * Format month label: "noviembre 2025" using Intl (es-419).
 */
function formatMonthLabel(yearMonthDay: string): string {
  const date = parseLocalDate(yearMonthDay.substring(0, 7) + "-01");
  return new Intl.DateTimeFormat("es-419", { month: "long", year: "numeric" }).format(date);
}

/**
 * Format a day date for aria-label: "10 de noviembre de 2025".
 */
function formatDayAriaLabel(isoDate: string): string {
  const date = parseLocalDate(isoDate);
  return new Intl.DateTimeFormat("es-419", { day: "numeric", month: "long", year: "numeric" }).format(date);
}

/**
 * Display HH:mm (strips seconds if BE returns "HH:mm:ss").
 */
function fmtHHmm(time: string): string {
  return time.length >= 5 ? time.slice(0, 5) : time;
}

/**
 * Get today's YYYY-MM-DD local string.
 */
function getTodayIso(): string {
  return toIsoDate(new Date());
}

/**
 * Get the current month's first day as YYYY-MM-01.
 */
function getCurrentMonthFirst(): string {
  const today = new Date();
  return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-01`;
}

// ── Props ──────────────────────────────────────────────────────────────────────

export interface MonthCalendarProps {
  /** UUID of the doctor whose availability blocks are displayed. */
  doctorId: string;
  /**
   * Initial month to display (YYYY-MM-DD, typically first of month).
   * Component manages internal navigation from this seed.
   */
  currentMonth?: string;
  /**
   * Called when user clicks a day cell — provides the ISO Monday string
   * of the week containing the clicked day, so parent can switch to week view.
   */
  onSwitchToWeek: (mondayIso: string) => void;
}

// ── Chip component ─────────────────────────────────────────────────────────────

interface MonthChipProps {
  occurrence: AvailabilityOccurrence;
}

function MonthChip({ occurrence }: MonthChipProps) {
  return (
    <span
      data-testid={`month-chip-${occurrence.occurrenceDate}-${occurrence.blockId}`}
      className={cn(
        "block w-full truncate rounded px-1 py-0.5 text-xs font-semibold leading-tight",
        "bg-agent-lisa-soft border-l-2 border-agent-lisa text-foreground",
        "select-none",
      )}
      aria-label={`${fmtHHmm(occurrence.startTime)}–${fmtHHmm(occurrence.endTime)}`}
    >
      {fmtHHmm(occurrence.startTime)}–{fmtHHmm(occurrence.endTime)}
    </span>
  );
}

// ── Main component ─────────────────────────────────────────────────────────────

export function MonthCalendar({
  doctorId,
  currentMonth,
  onSwitchToWeek,
}: MonthCalendarProps) {
  // Internal month navigation state (YYYY-MM-01)
  const [displayMonth, setDisplayMonth] = useState<string>(() => {
    if (currentMonth) {
      return currentMonth.substring(0, 7) + "-01";
    }
    return getCurrentMonthFirst();
  });

  // Compute grid bounds from displayMonth
  const firstVisibleDay = useMemo(() => getFirstVisibleDay(displayMonth), [displayMonth]);
  const lastVisibleDay = useMemo(() => getLastVisibleDay(firstVisibleDay), [firstVisibleDay]);
  const gridDays = useMemo(() => buildGridDays(firstVisibleDay), [firstVisibleDay]);
  const monthYear = useMemo(() => formatMonthLabel(displayMonth), [displayMonth]);
  const todayIso = useMemo(() => getTodayIso(), []);

  // The displayed month's year-month prefix for dim/active cell detection
  const displayYearMonth = displayMonth.substring(0, 7);

  // Data: one query per month range (RN-D3E-1 — consume BE projection, no client expansion)
  const { data: occurrences, isLoading, isError, refetch } = useAvailabilityOccurrences(
    doctorId,
    firstVisibleDay,
    lastVisibleDay,
  );

  // Group occurrences by date for O(1) lookup per cell
  const occurrencesByDate = useMemo(() => {
    const map: Record<string, AvailabilityOccurrence[]> = {};
    if (!occurrences) return map;
    for (const occ of occurrences) {
      if (!map[occ.occurrenceDate]) {
        map[occ.occurrenceDate] = [];
      }
      map[occ.occurrenceDate]!.push(occ);
    }
    return map;
  }, [occurrences]);

  const hasAnyOccurrence = useMemo(
    () => Boolean(occurrences && occurrences.length > 0),
    [occurrences],
  );

  // Navigation handlers
  const handlePrev = useCallback(() => {
    setDisplayMonth((prev) => addMonths(prev, -1));
  }, []);

  const handleNext = useCallback(() => {
    setDisplayMonth((prev) => addMonths(prev, 1));
  }, []);

  const handleHoy = useCallback(() => {
    setDisplayMonth(getCurrentMonthFirst());
  }, []);

  // Day click → onSwitchToWeek(mondayOfThatWeek)
  const handleDayClick = useCallback(
    (isoDate: string) => {
      const monday = getMondayOfWeek(isoDate);
      onSwitchToWeek(monday);
    },
    [onSwitchToWeek],
  );

  // ── Render: loading skeleton ──────────────────────────────────────────────

  if (isLoading) {
    return (
      <section data-testid="month-skeleton" className="flex flex-col gap-2 p-4" aria-label="Cargando calendario">
        {/* Header skeleton */}
        <div className="flex items-center justify-between mb-2">
          <Skeleton className="h-5 w-32" />
          <div className="flex gap-1">
            <Skeleton className="h-8 w-8 rounded-md" />
            <Skeleton className="h-8 w-14 rounded-md" />
            <Skeleton className="h-8 w-8 rounded-md" />
          </div>
        </div>
        {/* Day headers skeleton */}
        <ul className="grid grid-cols-7 gap-px mb-1 list-none p-0 m-0">
          {DAY_HEADERS.map((d) => (
            <li key={d}>
              <Skeleton className="h-5 w-full rounded" />
            </li>
          ))}
        </ul>
        {/* Grid skeleton — 6 rows */}
        {Array.from({ length: 6 }).map((_, row) => (
          <ul key={row} className="grid grid-cols-7 gap-px list-none p-0 m-0">
            {Array.from({ length: 7 }).map((_, col) => (
              <li key={col}>
                <Skeleton className="h-16 w-full rounded" />
              </li>
            ))}
          </ul>
        ))}
      </section>
    );
  }

  // ── Render: error state ───────────────────────────────────────────────────

  if (isError) {
    return (
      <section
        data-testid="month-error-state"
        className="flex flex-col items-center justify-center gap-3 p-8 text-center"
        aria-label="Error al cargar el calendario"
      >
        <p className="text-sm text-muted-foreground">
          No se pudieron cargar los horarios del mes.
        </p>
        <Button
          data-testid="month-retry-btn"
          variant="outline"
          size="sm"
          onClick={() => void refetch()}
        >
          Reintentar
        </Button>
      </section>
    );
  }

  // ── Render: grid ──────────────────────────────────────────────────────────

  return (
    <div data-testid="month-calendar" className="flex flex-col h-full">
      {/* ── Header: month label + nav ─────────────────────────────────── */}
      <div className="flex items-center justify-between px-4 py-3 flex-shrink-0 border-b border-border/40">
        <span
          data-testid="month-label"
          className="text-sm font-semibold capitalize text-foreground"
        >
          {monthYear}
        </span>
        <div className="flex items-center gap-1">
          <Button
            data-testid="month-nav-prev"
            variant="outline"
            size="icon"
            className="h-7 w-7"
            onClick={handlePrev}
            aria-label="Mes anterior"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            data-testid="month-nav-hoy"
            variant="outline"
            size="sm"
            className="h-7 px-2 text-xs"
            onClick={handleHoy}
            aria-label="Ir al mes actual"
          >
            Hoy
          </Button>
          <Button
            data-testid="month-nav-next"
            variant="outline"
            size="icon"
            className="h-7 w-7"
            onClick={handleNext}
            aria-label="Mes siguiente"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* ── Day-of-week headers ──────────────────────────────────────────── */}
      <header className="grid grid-cols-7 border-b border-border/40 flex-shrink-0" aria-hidden="true">
        {DAY_HEADERS.map((dayLabel) => (
          <span
            key={dayLabel}
            className="py-2 text-center text-xs font-medium text-muted-foreground uppercase tracking-wide block"
          >
            {dayLabel}
          </span>
        ))}
      </header>

      {/* ── Day grid ──────────────────────────────────────────────────────── */}
      <div
        role="grid"
        aria-label={`Calendario de ${monthYear}`}
        className="flex-1 grid grid-cols-7 grid-rows-6 overflow-hidden"
      >
        {gridDays.map((isoDate, idx) => {
          const isCurrentMonth = isoDate.startsWith(displayYearMonth);
          const isToday = isoDate === todayIso;
          const dayNumber = parseInt(isoDate.split("-")[2] ?? "0", 10);
          const dayOccs = occurrencesByDate[isoDate] ?? [];
          const visibleOccs = dayOccs.slice(0, MAX_CHIPS_PER_DAY);
          const overflowCount = dayOccs.length - visibleOccs.length;

          // Role landmarks for a11y
          const isRowStart = idx % 7 === 0;

          return (
            <React.Fragment key={isoDate}>
              {isRowStart && <div role="row" style={{ display: "contents" }} />}
              <div
                role="gridcell"
                data-testid={`month-day-${isoDate}`}
                className={cn(
                  "relative flex flex-col gap-0.5 p-1 border-b border-r border-border/30 cursor-pointer",
                  "hover:bg-accent/50 transition-colors min-h-0",
                  !isCurrentMonth && "bg-muted/20",
                  isToday && "bg-primary/5",
                )}
                onClick={() => handleDayClick(isoDate)}
                aria-label={formatDayAriaLabel(isoDate)}
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    handleDayClick(isoDate);
                  }
                }}
              >
                {/* Day number */}
                <span
                  className={cn(
                    "self-end font-medium leading-none",
                    isToday
                      ? "flex h-5 w-5 items-center justify-center rounded-full bg-primary text-primary-foreground font-bold text-xs"
                      : isCurrentMonth
                        ? "text-foreground text-xs"
                        : "text-muted-foreground/50 text-xs",
                  )}
                >
                  {dayNumber}
                </span>

                {/* Chips */}
                <ul className="flex flex-col gap-0.5 overflow-hidden w-full list-none p-0 m-0">
                  {visibleOccs.map((occ) => (
                    <li key={`${occ.blockId}-${occ.occurrenceDate}`}>
                      <MonthChip occurrence={occ} />
                    </li>
                  ))}
                  {overflowCount > 0 && (
                    <li
                      data-testid={`month-overflow-${isoDate}`}
                      className="text-xs text-muted-foreground font-medium pl-1 leading-tight"
                    >
                      +{overflowCount} más
                    </li>
                  )}
                </ul>
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {/* ── Empty state (in grid area when no occurrences) ──────────────── */}
      {!hasAnyOccurrence && !isLoading && !isError && (
        <section
          data-testid="month-empty-state"
          className="flex flex-col items-center justify-center gap-2 py-12 pointer-events-none"
          aria-label="Sin horarios en este mes"
        >
          <Calendar className="h-8 w-8 text-muted-foreground/40" aria-hidden="true" />
          <p className="text-sm text-muted-foreground text-center px-4">
            Sin horarios definidos para este mes.
            <br />
            <span className="text-xs">Agrega bloques en la vista semana.</span>
          </p>
        </section>
      )}
    </div>
  );
}
