// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * WeekCalendar.tsx — 7-day grid calendar view (default view).
 * T-13 vitalia-fase2-valeria-agenda · F2-S1
 *
 * Renders 7 day columns (Mon–Sun) for the week containing the provided date.
 * Each column shows the appointments for that day.
 * A1 acceptance: slots assigned to correct day column.
 *
 * Spanish neutro LatAm — sin voseo.
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.5 + 06-tickets.yaml T-13 acceptance A1
 */

import { useMemo, useCallback } from "react";
import { cn } from "@/lib/cn";
import { AgendaSlotInteractive } from "./AgendaSlotInteractive";
import type { AgendaSlot } from "../../types/agenda.types";

// ── Constants ─────────────────────────────────────────────────────────────────

/** Day-of-week abbreviations in Spanish neutro LatAm. */
const DAY_ABBRS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

// ── Helpers ───────────────────────────────────────────────────────────────────

/**
 * Returns the ISO date string (YYYY-MM-DD) for Monday of the week
 * that contains the given date string.
 */
function getMondayOfWeek(dateStr: string): Date {
  const d = new Date(`${dateStr}T12:00:00`);
  const dayOfWeek = d.getDay(); // 0=Sun, 1=Mon, ..., 6=Sat
  // Convert to Mon=0 .. Sun=6
  const daysFromMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1;
  d.setDate(d.getDate() - daysFromMonday);
  return d;
}

/** Returns array of 7 Date objects representing Mon..Sun of the week. */
function getWeekDays(dateStr: string): Date[] {
  const monday = getMondayOfWeek(dateStr);
  return Array.from({ length: 7 }, (_, i) => {
    const d = new Date(monday);
    d.setDate(d.getDate() + i);
    return d;
  });
}

/** Extracts YYYY-MM-DD from a Date object (local date). */
function toDateKey(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Extracts YYYY-MM-DD from an ISO 8601 datetime string. */
function slotDateKey(isoStr: string): string {
  // Parse the date portion, respecting timezone offset
  const d = new Date(isoStr);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Returns "D" (day number) for display in column header. */
function formatDayNumber(d: Date): string {
  return String(d.getDate());
}

/** Returns true if the date matches today. */
function isToday(d: Date): boolean {
  const today = new Date();
  return (
    d.getFullYear() === today.getFullYear() &&
    d.getMonth() === today.getMonth() &&
    d.getDate() === today.getDate()
  );
}

// ── Props ─────────────────────────────────────────────────────────────────────

export interface WeekCalendarProps {
  /** All slots for the week, sorted by startTime. */
  slots: AgendaSlot[];
  /** ISO 8601 date string (YYYY-MM-DD) — any day in the target week. */
  date: string;
  /** Tenant ID (HIPAA dual filter). */
  tenantId: string;
  /** Called with appointmentId when a slot is clicked. */
  onSlotClick: (appointmentId: string) => void;
  /**
   * T-FE-1: Called when an empty day column is clicked.
   * Passes YYYY-MM-DD date + "09:00" as default time for prefill.
   */
  onEmptySlotClick?: (date: string, time: string) => void;
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * 7-column week calendar grid.
 *
 * - Computes Mon..Sun for the week of `date`
 * - Assigns each slot to the column matching its startTime date
 * - Shows empty placeholder when no slots for a column
 *
 * data-testid="week-day-col-{0..6}" for each column (0=Monday)
 */
export function WeekCalendar({
  slots,
  date,
  onSlotClick,
  onEmptySlotClick,
  className,
}: WeekCalendarProps) {
  // Compute the 7 days for this week
  const weekDays = useMemo(() => getWeekDays(date), [date]);

  // Group slots by date key
  const slotsByDay = useMemo(() => {
    const map: Record<string, AgendaSlot[]> = {};
    for (const day of weekDays) {
      map[toDateKey(day)] = [];
    }
    for (const slot of slots) {
      const key = slotDateKey(slot.startTime);
      if (map[key]) {
        map[key]!.push(slot);
      }
    }
    return map;
  }, [slots, weekDays]);

  const handleSlotClick = useCallback(
    (slot: AgendaSlot) => {
      onSlotClick(slot.appointmentId);
    },
    [onSlotClick],
  );

  return (
    <div
      className={cn(
        "flex h-full w-full flex-col overflow-hidden rounded-lg border bg-card",
        className,
      )}
      data-testid="week-calendar"
    >
      {/* Day header row */}
      <div className="grid grid-cols-7 border-b bg-muted/30">
        {weekDays.map((day, colIdx) => {
          const isCurrentDay = isToday(day);
          return (
            <div
              key={colIdx}
              className={cn(
                "flex flex-col items-center gap-0.5 border-r px-1 py-2 last:border-r-0",
                isCurrentDay && "bg-primary/5",
              )}
            >
              {/* T-V2 fix-loop (axe): muted #71717a sobre col hoy #eff8fc = 4.48 (<4.5 AA) */}
              <span className="text-[11px] font-medium text-foreground/75">
                {DAY_ABBRS[colIdx]}
              </span>
              <span
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full text-xs font-semibold",
                  // T-V2 fix-loop (axe destapado por edge-redirect): white sobre
                  // --primary cyan #01aef9 = 2.49 (AA fail). Texto oscuro fijo.
                  isCurrentDay
                    ? "bg-primary text-cyan-950"
                    : "text-foreground",
                )}
              >
                {formatDayNumber(day)}
              </span>
            </div>
          );
        })}
      </div>

      {/* Slot columns */}
      <div className="grid flex-1 grid-cols-7 overflow-y-auto">
        {weekDays.map((day, colIdx) => {
          const dayKey = toDateKey(day);
          const daySlots = slotsByDay[dayKey] ?? [];
          const isCurrentDay = isToday(day);

          return (
            <div
              key={colIdx}
              className={cn(
                "flex min-h-[160px] flex-col gap-1 border-r p-1 last:border-r-0",
                isCurrentDay && "bg-primary/5",
              )}
              data-testid={`week-day-col-${colIdx}`}
              /* T-V2 fix-loop (axe): aria-label requiere role que lo permita
                 (div genérico = aria-prohibited-attr). group = columna de slots. */
              role="group"
              aria-label={`${DAY_ABBRS[colIdx]} ${formatDayNumber(day)}`}
            >
              {daySlots.map((slot) => (
                <AgendaSlotInteractive
                  key={slot.appointmentId}
                  slot={slot}
                  onClick={() => handleSlotClick(slot)}
                />
              ))}
              {/* Empty column click target (T-FE-1: push to nueva-cita with date prefill) */}
              {daySlots.length === 0 && onEmptySlotClick && (
                <button
                  type="button"
                  className="flex-1 w-full cursor-pointer rounded-sm text-xs text-muted-foreground/50 hover:bg-muted/40 hover:text-muted-foreground transition-colors"
                  aria-label={`Crear cita el ${DAY_ABBRS[colIdx]} ${formatDayNumber(day)}`}
                  data-testid={`week-empty-slot-${colIdx}`}
                  onClick={() => onEmptySlotClick(dayKey, "09:00")}
                >
                  +
                </button>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
