// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * MonthCalendar.tsx — Monthly calendar grid with aggregate dots.
 * T-13 vitalia-fase2-valeria-agenda · F2-S1
 *
 * A5 acceptance: consumes aggregates endpoint (not bulk slots).
 * Renders 5-week grid (Mon–Sun) with dot indicators per day.
 * Dots represent payment status breakdown from aggregates.
 * Click on day → calls onDayClick with ISO date string.
 *
 * Performance design (03-arch.md § 6.12):
 *   - NO FixedSizeList (aggregate dots, not slot list)
 *   - NO individual slot rendering (only totalSlots count + statusBreakdown)
 *   - Lightweight — O(35 cells) maximum
 *
 * Spanish neutro LatAm — sin voseo.
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.5 + § 6.12 + 06-tickets.yaml T-13 acceptance A5
 */

import { useMemo } from "react";
import { cn } from "@/lib/cn";
import type { SlotPaymentStatus } from "../../types/agenda.types";

// ── Types ─────────────────────────────────────────────────────────────────────

/** Per-day aggregate data from AgendaAggregatesResponseDTO (03-arch.md § 4.2). */
export interface DayAggregate {
  /** ISO 8601 date string (YYYY-MM-DD). */
  date: string;
  /** Total slots for this day. */
  totalSlots: number;
  /** Count per payment status. */
  statusBreakdown: Partial<Record<SlotPaymentStatus, number>>;
}

/** Month aggregates shape (matches AgendaAggregatesResponseDTO). */
export interface MonthAggregates {
  /** "YYYY-MM" format. */
  month: string;
  days: DayAggregate[];
}

// ── Props ─────────────────────────────────────────────────────────────────────

export interface MonthCalendarProps {
  /** Tenant ID (HIPAA dual filter). */
  tenantId: string;
  /** ISO 8601 date string (YYYY-MM-DD) — any day in the target month. */
  date: string;
  /** Aggregate data from /aggregates endpoint (A5). */
  aggregates: MonthAggregates | null;
  /** Called with ISO date string when a day cell is clicked. */
  onDayClick: (date: string) => void;
  className?: string;
}

// ── Constants ─────────────────────────────────────────────────────────────────

/** Day-of-week column headers (Monday-first). */
const DAY_HEADERS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

/** Status dot colors (vitalia CSS custom property color shortcuts — no raw hex/hsl literals). */
const STATUS_DOT_CLASS: Record<SlotPaymentStatus, string> = {
  paid:    "bg-[color:var(--vitalia-success-color)]",
  deposit: "bg-[color:var(--vitalia-warning-color)]",
  unpaid:  "bg-[color:var(--vitalia-danger-color)]",
  no_show: "bg-[color:var(--vitalia-muted-status-color)]",
};

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Returns a Date representing the 1st of the month for a given ISO date. */
function getMonthStart(dateStr: string): Date {
  const d = new Date(`${dateStr}T12:00:00`);
  return new Date(d.getFullYear(), d.getMonth(), 1);
}

/** Returns day-of-week offset for Monday-first grid (0=Mon, 6=Sun). */
function getMondayOffset(d: Date): number {
  const dow = d.getDay(); // 0=Sun
  return dow === 0 ? 6 : dow - 1;
}

/** Extracts YYYY-MM-DD string from a Date (local date). */
function toDateKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

interface CalendarCell {
  dateKey: string;
  dayNumber: number;
  isCurrentMonth: boolean;
  isToday: boolean;
}

/**
 * Builds a 5×7 grid of calendar cells for the month.
 * Fills leading/trailing days from adjacent months.
 */
function buildMonthGrid(dateStr: string): CalendarCell[] {
  const firstOfMonth = getMonthStart(dateStr);
  const monthIdx = firstOfMonth.getMonth();
  const year = firstOfMonth.getFullYear();

  const offset = getMondayOffset(firstOfMonth);
  const today = new Date();
  const todayKey = toDateKey(today);

  // Total cells: 5 rows × 7 cols = 35
  const cells: CalendarCell[] = [];
  const startDate = new Date(firstOfMonth);
  startDate.setDate(startDate.getDate() - offset);

  for (let i = 0; i < 35; i++) {
    const d = new Date(startDate);
    d.setDate(startDate.getDate() + i);
    const key = toDateKey(d);
    cells.push({
      dateKey: key,
      dayNumber: d.getDate(),
      isCurrentMonth: d.getMonth() === monthIdx && d.getFullYear() === year,
      isToday: key === todayKey,
    });
  }

  return cells;
}

// ── Dot indicators ─────────────────────────────────────────────────────────────

interface DotIndicatorsProps {
  dayAggregate: DayAggregate | undefined;
}

function DotIndicators({ dayAggregate }: DotIndicatorsProps) {
  if (!dayAggregate || dayAggregate.totalSlots === 0) return null;

  // Show up to 3 dots — one per dominant status
  const breakdown = dayAggregate.statusBreakdown;
  const statusEntries = (Object.entries(breakdown) as [SlotPaymentStatus, number][])
    .filter(([, count]) => (count ?? 0) > 0)
    .sort(([, a], [, b]) => (b ?? 0) - (a ?? 0))
    .slice(0, 3);

  return (
    <div className="mt-0.5 flex items-center justify-center gap-0.5">
      {statusEntries.map(([status]) => (
        <span
          key={status}
          className={cn("h-1.5 w-1.5 rounded-full", STATUS_DOT_CLASS[status])}
          aria-hidden="true"
        />
      ))}
    </div>
  );
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Monthly calendar grid — aggregate dots view.
 *
 * Renders 5 rows × 7 columns (Mon-first).
 * Each day shows colored dot indicators from statusBreakdown.
 * Click on any day → onDayClick(dateKey).
 * A5: NO individual slot rendering, NO FixedSizeList.
 */
export function MonthCalendar({
  date,
  aggregates,
  onDayClick,
  className,
}: MonthCalendarProps) {
  const cells = useMemo(() => buildMonthGrid(date), [date]);

  // Build lookup map: dateKey → DayAggregate
  const aggregateMap = useMemo(() => {
    const map: Record<string, DayAggregate> = {};
    if (aggregates) {
      for (const day of aggregates.days) {
        map[day.date] = day;
      }
    }
    return map;
  }, [aggregates]);

  return (
    <div
      className={cn(
        "flex w-full flex-col overflow-hidden rounded-lg border bg-card",
        className,
      )}
      data-testid="month-calendar"
    >
      {/* Day-of-week headers */}
      <div className="grid grid-cols-7 border-b bg-muted/30">
        {DAY_HEADERS.map((header) => (
          <div
            key={header}
            className="py-2 text-center text-[11px] font-medium text-muted-foreground"
          >
            {header}
          </div>
        ))}
      </div>

      {/* 5-week grid */}
      <div className="grid flex-1 grid-cols-7">
        {cells.map((cell, idx) => {
          const dayAgg = aggregateMap[cell.dateKey];
          const hasSlots = (dayAgg?.totalSlots ?? 0) > 0;

          return (
            <button
              key={idx}
              type="button"
              className={cn(
                "flex min-h-[64px] flex-col items-center border-b border-r p-1",
                "transition-colors hover:bg-muted/50",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
                // Fade out-of-month days
                !cell.isCurrentMonth && "opacity-40",
                // Today highlight
                cell.isToday && "bg-primary/5",
                // Last row / last col — remove double borders
                idx % 7 === 6 && "border-r-0",
                idx >= 28 && "border-b-0",
              )}
              onClick={() => onDayClick(cell.dateKey)}
              aria-label={`${cell.dateKey}${hasSlots ? `, ${dayAgg!.totalSlots} cita${dayAgg!.totalSlots === 1 ? "" : "s"}` : ", sin citas"}`}
              data-testid={`month-day-${cell.dateKey}`}
            >
              {/* Day number */}
              <span
                className={cn(
                  "flex h-5 w-5 items-center justify-center rounded-full text-xs",
                  cell.isToday
                    ? "bg-primary font-semibold text-primary-foreground"
                    : "text-foreground",
                )}
              >
                {cell.dayNumber}
              </span>

              {/* Aggregate dot indicators (A5) */}
              <DotIndicators dayAggregate={dayAgg} />

              {/* Slot count text for days with appointments */}
              {hasSlots && (
                <span className="mt-0.5 text-[9px] text-muted-foreground">
                  {dayAgg!.totalSlots}
                </span>
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
