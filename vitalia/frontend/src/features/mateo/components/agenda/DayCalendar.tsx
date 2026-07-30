// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * DayCalendar.tsx — Single-day timeline calendar view.
 * T-13 vitalia-fase2-valeria-agenda · F2-S1
 *
 * Renders appointments for a single day in a scrollable list.
 * A4 acceptance criterion: uses react-window List when slots > 50.
 *
 * Virtualization threshold: VIRTUAL_THRESHOLD = 50 (from 03-arch.md § 6.12)
 * Item height: 80px (SLOT_ITEM_SIZE_PX)
 * Overscan: 2 rows (performance)
 *
 * Note: Uses react-window v2 API (`List` with rowComponent/rowProps/rowCount/rowHeight).
 * Test mock intercepts at module level so tests use their own mock.
 *
 * Spanish neutro LatAm — sin voseo.
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.5 + § 6.12 + 06-tickets.yaml T-13 acceptance A4
 */

import { useCallback } from "react";
import { List } from "react-window";
import { cn } from "@/lib/cn";
import { AgendaSlotInteractive } from "./AgendaSlotInteractive";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import type { AgendaSlot } from "../../types/agenda.types";

// ── Constants (03-arch.md § 6.12) ─────────────────────────────────────────────

/** Virtualization threshold — switch to List above this count. */
const VIRTUAL_THRESHOLD = 50;

/** Row height for List items (px). */
const SLOT_ITEM_SIZE_PX = 80;

/** Visible height of the virtual list container (px). */
const VIRTUAL_LIST_HEIGHT = 560;

/** Overscan rows for react-window (pre-render above/below visible area). */
const OVERSCAN_COUNT = 2;

// ── Props ─────────────────────────────────────────────────────────────────────

export interface DayCalendarProps {
  /** Appointments for the day, sorted by startTime. */
  slots: AgendaSlot[];
  /** ISO 8601 date string (YYYY-MM-DD) — used for header display. */
  date: string;
  /** Tenant ID (HIPAA dual filter — passed to slot click handlers). */
  tenantId: string;
  /** Called with appointmentId when a slot is clicked. */
  onSlotClick: (appointmentId: string) => void;
  /**
   * T-FE-1: Called when the empty state "+" button is clicked.
   * Passes date + "09:00" as default time for prefill in nueva-cita.
   */
  onEmptySlotClick?: (date: string, time: string) => void;
  className?: string;
}

// ── Row data type for react-window v2 rowProps ─────────────────────────────────

interface SlotRowData {
  slots: AgendaSlot[];
  onSlotClick: (appointmentId: string) => void;
}

// ── Row renderer for react-window v2 ─────────────────────────────────────────

function SlotRowComponent(
  props: {
    ariaAttributes: { "aria-posinset": number; "aria-setsize": number; role: "listitem" };
    index: number;
    style: React.CSSProperties;
  } & SlotRowData,
) {
  const { index, style, slots, onSlotClick } = props;
  const slot = slots[index];
  if (!slot) return null;

  return (
    <div style={style} className="px-2 py-1">
      <AgendaSlotInteractive
        slot={slot}
        onClick={() => onSlotClick(slot.appointmentId)}
        className="h-[72px]"
      />
    </div>
  );
}

// ── Formatted date header ──────────────────────────────────────────────────────

function formatDayHeader(dateStr: string, timezone: string, locale: string): string {
  try {
    const d = new Date(`${dateStr}T12:00:00`);
    if (isNaN(d.getTime())) return dateStr;
    return new Intl.DateTimeFormat(locale, {
      weekday: "long",
      day: "numeric",
      month: "long",
      timeZone: timezone,
    }).format(d);
  } catch {
    return dateStr;
  }
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Single-day timeline calendar.
 *
 * - ≤50 slots: plain scrollable list
 * - >50 slots: react-window List (A4 virtualization)
 * - 0 slots: "Sin citas" empty state
 *
 * All PHI-masked via AgendaSlotInteractive (never raw patient.name).
 */
export function DayCalendar({
  slots,
  date,
  onSlotClick,
  onEmptySlotClick,
  className,
}: DayCalendarProps) {
  const { timezone, locale } = useTenantLocale();
  const dayLabel = formatDayHeader(date, timezone, locale);
  const useVirtualization = slots.length > VIRTUAL_THRESHOLD;

  const handleSlotClick = useCallback(
    (appointmentId: string) => {
      onSlotClick(appointmentId);
    },
    [onSlotClick],
  );

  return (
    <div
      className={cn(
        "flex flex-col overflow-hidden rounded-lg border bg-card",
        className,
      )}
      data-testid="day-calendar"
    >
      {/* Day header */}
      <div className="border-b px-4 py-3">
        <h2 className="text-sm font-semibold capitalize text-foreground">
          {dayLabel}
        </h2>
        <p className="text-xs text-muted-foreground">
          {`${slots.length} cita${slots.length === 1 ? "" : "s"}`}
        </p>
      </div>

      {/* Empty state — T-FE-1: clickable if onEmptySlotClick provided */}
      {slots.length === 0 && (
        <div
          className="flex flex-1 items-center justify-center p-8"
          aria-live="polite"
        >
          {onEmptySlotClick ? (
            <button
              type="button"
              className="flex flex-col items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
              onClick={() => onEmptySlotClick(date, "09:00")}
              data-testid="day-empty-slot-btn"
              aria-label="Crear cita para este día"
            >
              <span className="text-2xl">+</span>
              <span>Sin citas — crear una</span>
            </button>
          ) : (
            <p className="text-sm text-muted-foreground">Sin citas para este día.</p>
          )}
        </div>
      )}

      {/* Virtualized list — only when >50 slots (A4 / SC-9) */}
      {slots.length > 0 && useVirtualization && (
        <List<SlotRowData>
          style={{ height: VIRTUAL_LIST_HEIGHT }}
          rowCount={slots.length}
          rowHeight={SLOT_ITEM_SIZE_PX}
          overscanCount={OVERSCAN_COUNT}
          rowProps={{ slots, onSlotClick: handleSlotClick }}
          rowComponent={SlotRowComponent}
        />
      )}

      {/* Plain list — when ≤50 slots */}
      {slots.length > 0 && !useVirtualization && (
        <div className="flex flex-col gap-1.5 overflow-y-auto p-2">
          {slots.map((slot) => (
            <AgendaSlotInteractive
              key={slot.appointmentId}
              slot={slot}
              onClick={() => handleSlotClick(slot.appointmentId)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// Re-export for tree-shaking clarity
export { VIRTUAL_THRESHOLD as DAY_CALENDAR_VIRTUAL_THRESHOLD };
