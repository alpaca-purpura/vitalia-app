// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * AvailabilityCalendar.tsx — Custom week grid calendar for doctor availability blocks.
 *
 * Architecture per 03-arch-fe.md § Calendar decision:
 *   - Custom week grid (day × hour, CSS Grid) — optimised for columna angosta (~600px).
 *   - @dnd-kit/core for drag-to-create availability blocks.
 *   - Base range: 07:00–21:00. "Mostrar 24 horas" toggle expands to 00:00–23:00.
 *   - Week navigation ‹/› via Zustand calendarWeek state.
 *   - PAINT source: useAvailabilityOccurrences (BE projection SSoT) — fixes infinite
 *     paint bug (D3-C) where recurrentBlockVisibleInWeek() ignored occurrences/open_ended.
 *   - useAvailabilityBlocks kept ONLY for BloquePopover (edit/delete UI).
 *   - 24h format. Slots stored UTC; display via useTenantLocale (master-data.md).
 *   - Drag creates a draft block → BloquePopover opens.
 *
 * D3-C fix: deleted recurrentBlockVisibleInWeek / oneOffBlockVisibleInWeek / blockDayOfWeek
 *           (V-D3C-NODUP: grep these function names in src/ → 0 matches required).
 *
 * T-FE-occurrences-consume vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-C.1 + 03-arch-fe.md § AvailabilityCalendar
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import React, {
  useState,
  useCallback,
  useRef,
  useMemo,
  useEffect,
} from "react";
import {
  DndContext,
  useSensor,
  useSensors,
  PointerSensor,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { addLocalDays as addDays, parseLocalDate, toLocalIsoDate } from "@/lib/format/calendarDates";
import { useStaffUiStore } from "../../../../store/staff-ui-store";
import {
  useAvailabilityBlocks,
  useAvailabilityOccurrences,
} from "../../../../api/staff";
// F6 fix: per master-data.md — NEVER toLocaleDateString(); use Intl.DateTimeFormat with explicit locale
import type {
  AvailabilityBlock,
  AvailabilityOccurrence,
} from "../../../../types/staff.types";
import { BloquePopover, type BloquePopoverAnchor } from "./BloquePopover";

// ── Constants ─────────────────────────────────────────────────────────────────

const BASE_START_HOUR = 7; // 07:00
const BASE_END_HOUR = 21; // 21:00
const FULL_START_HOUR = 0;
const FULL_END_HOUR = 24;
const HOUR_HEIGHT = 48; // px per hour slot

const DAY_LABELS = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"];

// ── Week navigation helpers ────────────────────────────────────────────────────
// bug7 r4: date math comes from the TZ-stable SSoT (lib/format/calendarDates).
// addLocalDays builds dates from LOCAL components (never toISOString) so the
// week grid never drifts a day under a negative UTC offset.

/**
 * formatWeekLabel — deterministic week range label using Intl.DateTimeFormat.
 * F6 fix: per master-data.md — NEVER toLocaleDateString(). Use Intl.DateTimeFormat
 * with explicit locale "es-419" and no browser-default date locale resolution.
 */
function formatWeekLabel(mondayIso: string): string {
  const monday = new Date(mondayIso + "T00:00:00");
  const sunday = new Date(mondayIso + "T00:00:00");
  sunday.setDate(monday.getDate() + 6);
  const opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "short" };
  const formatter = new Intl.DateTimeFormat("es-419", opts);
  const monStr = formatter.format(monday);
  const sunStr = formatter.format(sunday);
  const year = monday.getFullYear();
  return `${monStr} – ${sunStr}, ${year}`;
}

/**
 * Get ISO date for a specific day in the week starting at mondayIso.
 * dayOfWeek: 0=Monday..6=Sunday
 */
function getDateForDayOfWeek(mondayIso: string, dayOfWeek: number): string {
  return addDays(mondayIso, dayOfWeek);
}

/**
 * Convert "HH:mm" to hours as decimal.
 */
function timeToHours(time: string): number {
  const [h, m] = time.split(":").map(Number);
  return (h ?? 0) + (m ?? 0) / 60;
}

/**
 * Display a time as "HH:mm" — strips seconds the BE may include ("10:00:00" → "10:00").
 */
function fmtHHmm(time: string): string {
  return time.length >= 5 ? time.slice(0, 5) : time;
}

/**
 * hourFromClientY — map a pointer clientY to an hour slot of a day column.
 *
 * bug7 r3 D-2: el drag-create ahora se computa por COORDENADAS contra el
 * rect de la columna (window listeners), no por mouseenter de cada celda.
 * Los mouseenter se rompían cuando el puntero pasaba sobre un bloque
 * existente (overlay pointer-events-auto tapa las celdas) → "no se
 * seleccionan las celdas y sale el popup solo" (clon GCal: arrastrar
 * ATRAVIESA eventos existentes cuando el drag arranca en celda vacía).
 *
 * Pure + exported for unit tests.
 */
export function hourFromClientY(
  clientY: number,
  columnTop: number,
  startHour: number,
  hourCount: number,
  hourHeight: number = HOUR_HEIGHT,
): number {
  const rawIdx = Math.floor((clientY - columnTop) / hourHeight);
  const clampedIdx = Math.max(0, Math.min(hourCount - 1, rawIdx));
  return startHour + clampedIdx;
}

/**
 * Days offset (0=Monday column) of an occurrence relative to the visible week's
 * Monday. Returns the RAW offset — bug7 r4: the old `Math.min(6, diff)` clamp
 * silently folded an out-of-window occurrence (diff=7, next Monday) into column
 * 6 (Sunday). The caller now DISCARDS anything outside [0,6] instead of
 * mis-painting it. With the week anchored on the real Monday (calendarDates),
 * in-window occurrences are always 0..6.
 */
function occurrenceDayOfWeek(occurrenceDate: string, mondayIso: string): number {
  const occDate = parseLocalDate(occurrenceDate);
  const weekMonday = parseLocalDate(mondayIso);
  return Math.round(
    (occDate.getTime() - weekMonday.getTime()) / (1000 * 60 * 60 * 24),
  );
}

// ── CalendarBlock component ────────────────────────────────────────────────────

interface CalendarBlockProps {
  occurrence: AvailabilityOccurrence;
  onOccurrenceClick: (occurrence: AvailabilityOccurrence, event: React.MouseEvent) => void;
}

/**
 * bug7 r3: CalendarBlock se posiciona via inset-y-0 DENTRO del wrapper que ya
 * setea top/height. Antes computaba su PROPIO top=(start-startHour)*48 además
 * del wrapper → DOBLE offset: un bloque 09:00 pintaba en la fila 11:00. Eso
 * corría todos los hitboxes (clicks/drags aterrizaban en bloques invisibles
 * desplazados → "sale el popup solo").
 */
function CalendarBlock({
  occurrence,
  onOccurrenceClick,
}: CalendarBlockProps) {
  // D3-F: use patternSummary from BE (SSoT) instead of hardcoded freq label.
  // Falls back to "Único" for one_off blocks without patternSummary.
  const patternLabel =
    occurrence.kind === "recurrent" && occurrence.patternSummary
      ? occurrence.patternSummary
      : occurrence.kind === "one_off"
        ? "Único"
        : "Recurrente";

  return (
    <button
      data-testid={`block-${occurrence.blockId}`}
      data-occurrence-date={occurrence.occurrenceDate}
      className={cn(
        "absolute left-0.5 right-0.5 inset-y-0 rounded-md cursor-pointer text-xs font-semibold",
        "bg-agent-lisa-soft border-l-[3px] border-agent-lisa text-foreground shadow-sm",
        "hover:opacity-90 hover:shadow transition-all",
        "flex flex-col items-start justify-start gap-0.5 px-1.5 py-1 overflow-hidden",
        "focus:outline-none focus:ring-2 focus:ring-agent-lisa",
      )}
      onClick={(e) => onOccurrenceClick(occurrence, e)}
      aria-label={`Bloque ${fmtHHmm(occurrence.startTime)}–${fmtHHmm(occurrence.endTime)} (${patternLabel})`}
    >
      <span className="truncate leading-tight">
        {fmtHHmm(occurrence.startTime)}–{fmtHHmm(occurrence.endTime)}
      </span>
      {occurrence.kind === "recurrent" && (
        <span
          className="truncate text-[10px] font-medium text-agent-lisa leading-none"
          data-testid={`block-pattern-${occurrence.blockId}`}
        >
          {patternLabel}
        </span>
      )}
    </button>
  );
}

// ── DroppableCell component ────────────────────────────────────────────────────

interface DroppableCellProps {
  dayIndex: number;
  hour: number;
  children?: React.ReactNode;
  onMouseDown: (dayIndex: number, hour: number, e: React.MouseEvent) => void;
  /** Cell is in the past — disable interaction, apply visual cue */
  isPast?: boolean;
}

function DroppableCell({
  dayIndex,
  hour,
  children,
  onMouseDown,
  isPast = false,
}: DroppableCellProps) {
  return (
    <div
      data-testid={`cell-${dayIndex}-${hour}`}
      data-past={isPast ? "true" : undefined}
      className={cn(
        "absolute inset-0 border-b border-border/30",
        isPast && "bg-muted/20 opacity-60 cursor-not-allowed",
      )}
      onMouseDown={(e) => {
        if (isPast) return;
        onMouseDown(dayIndex, hour, e);
      }}
      role="button"
      tabIndex={-1}
      aria-disabled={isPast || undefined}
      aria-label={
        isPast
          ? `${DAY_LABELS[dayIndex]} ${String(hour).padStart(2, "0")}:00 — no disponible`
          : `Crear bloque el ${DAY_LABELS[dayIndex]} a las ${String(hour).padStart(2, "0")}:00`
      }
    >
      {children}
    </div>
  );
}

// ── Main AvailabilityCalendar ─────────────────────────────────────────────────

export interface AvailabilityCalendarProps {
  doctorId: string;
  /** Optional Monday ISO override — used by tests to control the visible week
   *  without needing to change Zustand store state. In production the component
   *  reads calendarWeek from useStaffUiStore. */
  mondayIso?: string;
}

export function AvailabilityCalendar({ doctorId, mondayIso: mondayIsoProp }: AvailabilityCalendarProps) {
  const calendarWeekStore = useStaffUiStore((s) => s.calendarWeek);
  const setCalendarWeek = useStaffUiStore((s) => s.setCalendarWeek);
  const setDragDraft = useStaffUiStore((s) => s.setDragDraft);

  // mondayIsoProp only used in tests; production uses the store value.
  const calendarWeek = mondayIsoProp ?? calendarWeekStore;

  // ── Past-cell computation ──────────────────────────────────────────────────
  // A cell (dayIndex, hour) is "past" when:
  //   date for that column < today   → whole column is past
  //   date == today AND hour <= currentLocalHour  → that cell is past
  // Uses local clock so a doctor in UTC-5 doesn't see their 10am as past at 15:00 UTC.
  const todayIso = toLocalIsoDate(new Date());
  const currentLocalHour = new Date().getHours();

  const isCellPast = useCallback(
    (dateIso: string, hour: number): boolean => {
      if (dateIso < todayIso) return true;
      if (dateIso === todayIso && hour <= currentLocalHour) return true;
      return false;
    },
    [todayIso, currentLocalHour],
  );

  // PAINT source: BE occurrences for the visible week (fixes D3-C infinite paint)
  const weekEnd = useMemo(() => addDays(calendarWeek, 6), [calendarWeek]);
  const { data: occurrences, isLoading: occurrencesLoading } =
    useAvailabilityOccurrences(doctorId, calendarWeek, weekEnd);

  // EDIT source: full blocks data — only for BloquePopover (not for painting)
  const { data: blocks, isLoading: blocksLoading } =
    useAvailabilityBlocks(doctorId);

  const isLoading = occurrencesLoading || blocksLoading;

  const [show24h, setShow24h] = useState(false);
  const [popoverState, setPopoverState] = useState<{
    block: AvailabilityBlock | null;
    draft: { dayOfWeek: number; startTime: string; endTime: string } | null;
    anchor: BloquePopoverAnchor;
    isExisting: boolean;
    /** ISO date of the clicked occurrence — for recurrent-block scoped deletes */
    occurrenceDate?: string;
  } | null>(null);

  // Drag-to-create state (bug7 r3 D-2: single state + coordinate math —
  // los window listeners viven en el useEffect de abajo)
  const [drag, setDrag] = useState<{
    day: number;
    anchorHour: number;
    currentHour: number;
  } | null>(null);
  const dayColumnRefs = useRef<(HTMLDivElement | null)[]>([]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 8 },
    }),
  );

  const startHour = show24h ? FULL_START_HOUR : BASE_START_HOUR;
  const endHour = show24h ? FULL_END_HOUR : BASE_END_HOUR;
  const hours = Array.from(
    { length: endHour - startHour },
    (_, i) => startHour + i,
  );

  // ── Build blocks lookup map (blockId → AvailabilityBlock) ─────────────────
  // Used to resolve the full block when an occurrence is clicked → BloquePopover

  const blocksMap = useMemo(() => {
    const map = new Map<string, AvailabilityBlock>();
    for (const block of blocks ?? []) {
      map.set(block.id, block);
    }
    return map;
  }, [blocks]);

  // ── Group occurrences by day column (0=Mon..6=Sun) ─────────────────────────
  // This replaces the deleted client-side expansion (blocksByDay + recurrentBlockVisibleInWeek)

  const occurrencesByDay = useMemo(() => {
    const byDay: AvailabilityOccurrence[][] = Array.from(
      { length: 7 },
      () => [],
    );
    for (const occ of occurrences ?? []) {
      const dayIndex = occurrenceDayOfWeek(occ.occurrenceDate, calendarWeek);
      // bug7 r4: DISCARD out-of-window occurrences (don't clamp into Sunday).
      if (dayIndex < 0 || dayIndex > 6) continue;
      byDay[dayIndex]?.push(occ);
    }
    return byDay;
  }, [occurrences, calendarWeek]);

  // ── Week navigation ────────────────────────────────────────────────────────

  const goToPrevWeek = useCallback(() => {
    setCalendarWeek(addDays(calendarWeek, -7));
  }, [calendarWeek, setCalendarWeek]);

  const goToNextWeek = useCallback(() => {
    setCalendarWeek(addDays(calendarWeek, 7));
  }, [calendarWeek, setCalendarWeek]);

  // ── Click-to-open popover for existing block ──────────────────────────────

  const handleOccurrenceClick = useCallback(
    (occurrence: AvailabilityOccurrence, event: React.MouseEvent) => {
      event.stopPropagation();
      // Look up the full AvailabilityBlock from blocks data for the popover
      const block = blocksMap.get(occurrence.blockId) ?? null;
      setPopoverState({
        block,
        draft: null,
        anchor: { x: event.clientX, y: event.clientY },
        isExisting: true,
        // Thread the occurrence date for recurrent-block scoped deletes (round-5 bug7 #1)
        occurrenceDate: occurrence.occurrenceDate,
      });
    },
    [blocksMap],
  );

  // ── Drag-to-create (bug7 r3 D-2 — GCal clone) ─────────────────────────────
  // mousedown en celda VACÍA ancla el drag (los bloques existentes interceptan
  // el click → editar, paridad GCal). El movimiento se sigue con listeners de
  // WINDOW + coordenadas contra el rect de la columna ancla: el rango sigue
  // creciendo aunque el puntero pase sobre bloques existentes o salga de la
  // grilla, y soltar en cualquier lado abre el editor con el rango arrastrado.

  const handleCellMouseDown = useCallback(
    (dayIndex: number, hour: number, e: React.MouseEvent) => {
      // Only left-click drag
      if (e.button !== 0) return;
      // Past-cell guard: never start a drag on a past cell
      const dateIso = getDateForDayOfWeek(calendarWeek, dayIndex);
      if (isCellPast(dateIso, hour)) return;
      // GCal parity: sin selección de texto durante el gesto
      e.preventDefault();
      setDrag({ day: dayIndex, anchorHour: hour, currentHour: hour });
      setDragDraft({ dayOfWeek: dayIndex, startHour: hour, endHour: hour + 1 });
    },
    [setDragDraft, calendarWeek, isCellPast],
  );

  useEffect(() => {
    if (!drag) return;

    const hourCount = endHour - startHour;

    const onMove = (e: MouseEvent) => {
      const column = dayColumnRefs.current[drag.day];
      if (!column) return;
      const rect = column.getBoundingClientRect();
      const hour = hourFromClientY(e.clientY, rect.top, startHour, hourCount);
      if (hour === drag.currentHour) return;
      setDrag({ ...drag, currentHour: hour });
      setDragDraft({
        dayOfWeek: drag.day,
        startHour: Math.min(drag.anchorHour, hour),
        endHour: Math.max(drag.anchorHour, hour) + 1,
      });
    };

    const onUp = (e: MouseEvent) => {
      const startH = Math.min(drag.anchorHour, drag.currentHour);
      const endH = Math.max(drag.anchorHour, drag.currentHour) + 1;

      const startTime = `${String(startH).padStart(2, "0")}:00`;
      const endTime = `${String(Math.min(endH, endHour)).padStart(2, "0")}:00`;

      setDrag(null);
      setDragDraft(null);

      // Open BloquePopover with draft (new block, not yet saved)
      setPopoverState({
        block: null,
        draft: {
          dayOfWeek: drag.day,
          startTime,
          endTime,
        },
        anchor: { x: e.clientX, y: e.clientY },
        isExisting: false,
      });
    };

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [drag, startHour, endHour, setDragDraft]);

  const handlePopoverClose = useCallback(() => {
    setPopoverState(null);
  }, []);

  // Compute drag overlay for visual feedback
  const dragOverlay = drag
    ? {
        day: drag.day,
        startH: Math.min(drag.anchorHour, drag.currentHour),
        endH: Math.max(drag.anchorHour, drag.currentHour) + 1,
      }
    : null;

  // ── dnd-kit callbacks (for pointer sensor) ────────────────────────────────
  const handleDragStart = useCallback((_event: DragStartEvent) => {
    // handled via mouse events
  }, []);

  const handleDragEnd = useCallback((_event: DragEndEvent) => {
    // handled via mouse events
  }, []);

  if (isLoading) {
    return (
      <div data-testid="calendar-skeleton" className="p-4 space-y-2">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  return (
    <DndContext
      sensors={sensors}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div data-testid="availability-calendar" className="flex flex-col h-full">
        {/* ── Header: week nav + 24h toggle ─────────────────────────────────── */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-border/40 gap-2 flex-shrink-0">
          <div className="flex items-center gap-1">
            <Button
              data-testid="week-nav-prev"
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={goToPrevWeek}
              aria-label="Semana anterior"
            >
              ‹
            </Button>
            <span
              className="text-xs font-medium text-muted-foreground min-w-[160px] text-center"
              data-testid="week-label"
            >
              {formatWeekLabel(calendarWeek)}
            </span>
            <Button
              data-testid="week-nav-next"
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={goToNextWeek}
              aria-label="Semana siguiente"
            >
              ›
            </Button>
          </div>
          <Button
            data-testid="toggle-24h"
            variant={show24h ? "secondary" : "ghost"}
            size="sm"
            className="h-7 text-xs"
            onClick={() => setShow24h((v) => !v)}
            aria-pressed={show24h}
          >
            {show24h ? "Vista reducida" : "Mostrar 24 horas"}
          </Button>
        </div>

        {/* ── Grid ──────────────────────────────────────────────────────────── */}
        {/* bug-horarios-toolbar-sticky: min-h-0 lets this flex-1 item shrink
            below its content height so `overflow-auto` actually engages. Without
            it, the default `min-height: auto` keeps the grid at its full content
            height (24h = 24×48px = 1152px), the scroll never clamps here, and the
            overflow bubbles up — dragging the header (flex-shrink-0) + the page
            toolbar with it. The day-header row stays fixed via `sticky top-0`. */}
        <div
          className="flex-1 min-h-0 overflow-auto"
          role="grid"
          aria-label="Calendario de disponibilidad"
        >
          {/* Day header row */}
          <div className="flex sticky top-0 z-10 bg-background border-b border-border/40">
            {/* Time gutter */}
            <div className="w-12 flex-shrink-0" />
            {/* Day columns */}
            {DAY_LABELS.map((label, i) => {
              const dateIso = getDateForDayOfWeek(calendarWeek, i);
              const date = new Date(dateIso + "T00:00:00");
              const dayNum = date.getDate();
              const isPastDay = dateIso < todayIso;
              return (
                <div
                  key={i}
                  data-testid={`day-col-${i}`}
                  className={cn(
                    "flex-1 min-w-0 text-center py-1 border-l border-border/30",
                    isPastDay && "opacity-50",
                  )}
                >
                  <span className="text-xs font-medium text-muted-foreground block">
                    {label}
                  </span>
                  <span className={cn("text-sm font-semibold block", isPastDay && "text-muted-foreground")}>
                    {dayNum}
                  </span>
                </div>
              );
            })}
          </div>

          {/* Time rows — select-none: GCal parity, sin selección de texto al arrastrar */}
          <div className="relative flex select-none">
            {/* Time gutter */}
            <div className="w-12 flex-shrink-0 relative">
              {hours.map((h) => (
                <div
                  key={h}
                  data-testid={`hour-label-${h}`}
                  className="text-right pr-1 text-xs text-muted-foreground"
                  style={{ height: `${HOUR_HEIGHT}px` }}
                >
                  {h < 10 ? `0${h}` : `${h}`}:00
                </div>
              ))}
            </div>

            {/* Day columns with cells */}
            {DAY_LABELS.map((_, dayIndex) => {
              const colDateIso = getDateForDayOfWeek(calendarWeek, dayIndex);
              const isColPastDay = colDateIso < todayIso;
              return (
              <div
                key={dayIndex}
                ref={(el) => {
                  dayColumnRefs.current[dayIndex] = el;
                }}
                className={cn(
                  "flex-1 min-w-0 border-l border-border/30 relative",
                  isColPastDay && "opacity-75",
                )}
                style={{ height: `${hours.length * HOUR_HEIGHT}px` }}
              >
                {/* Hour cells (droppable areas) */}
                {hours.map((h, hourIndex) => {
                  const isDragTarget =
                    dragOverlay &&
                    dragOverlay.day === dayIndex &&
                    h >= dragOverlay.startH &&
                    h < dragOverlay.endH;
                  const cellIsPast = isCellPast(colDateIso, h);

                  return (
                    <div
                      key={h}
                      className={cn(
                        "absolute left-0 right-0 border-b border-border/20",
                        isDragTarget && "bg-agent-lisa-soft",
                      )}
                      style={{
                        top: `${hourIndex * HOUR_HEIGHT}px`,
                        height: `${HOUR_HEIGHT}px`,
                      }}
                      role="gridcell"
                      aria-label={`${DAY_LABELS[dayIndex]} ${String(h).padStart(2, "0")}:00`}
                    >
                      <DroppableCell
                        dayIndex={dayIndex}
                        hour={h}
                        onMouseDown={handleCellMouseDown}
                        isPast={cellIsPast}
                      />
                    </div>
                  );
                })}

                {/* Occurrences overlay — paint from BE projection (D3-C fix) */}
                <div className="absolute inset-0 pointer-events-none">
                  {(occurrencesByDay[dayIndex] ?? []).map((occ) => (
                    <div
                      key={`${occ.blockId}-${occ.occurrenceDate}`}
                      className="pointer-events-auto absolute left-0 right-0"
                      style={{
                        top: `${(timeToHours(occ.startTime) - startHour) * HOUR_HEIGHT}px`,
                        height: `${Math.max(
                          (timeToHours(occ.endTime) - timeToHours(occ.startTime)) * HOUR_HEIGHT,
                          20,
                        )}px`,
                      }}
                    >
                      <CalendarBlock
                        occurrence={occ}
                        onOccurrenceClick={handleOccurrenceClick}
                      />
                    </div>
                  ))}
                </div>

                {/* Drag overlay visual */}
                {dragOverlay && dragOverlay.day === dayIndex && (
                  <div
                    className="absolute left-0.5 right-0.5 bg-agent-lisa-soft border border-agent-lisa rounded pointer-events-none z-10"
                    style={{
                      top: `${(dragOverlay.startH - startHour) * HOUR_HEIGHT}px`,
                      height: `${(dragOverlay.endH - dragOverlay.startH) * HOUR_HEIGHT}px`,
                    }}
                    aria-hidden
                  />
                )}
              </div>
              );
            })}
          </div>
        </div>

        {/* ── Hint text ─────────────────────────────────────────────────────── */}
        <div className="px-3 py-1.5 border-t border-border/40 flex-shrink-0">
          <p className="text-xs text-muted-foreground">
            Arrastra para crear un bloque de disponibilidad · Haz clic en un bloque para editarlo o eliminarlo
          </p>
        </div>

        {/* ── BloquePopover ─────────────────────────────────────────────────── */}
        {popoverState && (
          <BloquePopover
            doctorId={doctorId}
            block={popoverState.block}
            draft={popoverState.draft}
            isOpen={!!popoverState}
            onClose={handlePopoverClose}
            anchor={popoverState.anchor}
            isExisting={popoverState.isExisting}
            calendarWeek={calendarWeek}
            occurrenceDate={popoverState.occurrenceDate}
          />
        )}
      </div>
    </DndContext>
  );
}
