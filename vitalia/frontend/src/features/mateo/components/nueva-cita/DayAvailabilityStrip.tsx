// cap: scheduling.mateo-agenda
/**
 * DayAvailabilityStrip.tsx — Multi-doctor swimlane timeline for T-D3.
 * T-D3 vitalia-fase2-mateo-nueva-cita delta (EXTENDS T-FE-3 1-doctor strip).
 *
 * Inversion: previously 1 doctor selected → strip shows. Now:
 *   service + day → strip shows ALL doctors (N swimlanes).
 *   Click a lane → selects that doctor (onSelectDoctor callback).
 *   Selected lane → amber (--agent-mateo) border highlight.
 *   Hour selected → vertical time-cursor across all lanes.
 *   blocks:[] for a doctor → "Sin horario" (RN-4).
 *   doctors:[] → empty state.
 *
 * Time range: 07:00–21:00 local. Blocks outside are hidden.
 * HIPAA: doctor_label = professional name only. No patient PHI.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch-delta-availability.md § 4 strip-1→N + § 6 design
 */

"use client";

import * as React from "react";
import { cn } from "@/lib/cn";
import type { ServiceDayDoctor, DayBlockItem } from "../../types/agenda-schema";

// ── Constants ──────────────────────────────────────────────────────────────

const STRIP_START_HOUR = 7;
const STRIP_END_HOUR = 21;
const STRIP_MINUTES = (STRIP_END_HOUR - STRIP_START_HOUR) * 60; // 840
const AXIS_HOURS = [8, 10, 12, 14, 16, 18, 20];

// ── Helpers ────────────────────────────────────────────────────────────────

/**
 * Convert ISO to minutes-since-strip-start in the given timezone.
 * H1 fix: Intl.DateTimeFormat for local time (not UTC arithmetic).
 */
function isoToStripMinutes(iso: string, timezone: string): number {
  try {
    const parts = new Intl.DateTimeFormat("en", {
      timeZone: timezone,
      hour: "numeric",
      minute: "numeric",
      hourCycle: "h23",
    }).formatToParts(new Date(iso));
    const h = parseInt(parts.find((p) => p.type === "hour")?.value ?? "0", 10);
    const m = parseInt(parts.find((p) => p.type === "minute")?.value ?? "0", 10);
    const total = h * 60 + m;
    const stripStart = STRIP_START_HOUR * 60;
    return Math.max(0, Math.min(STRIP_MINUTES, total - stripStart));
  } catch {
    return 0;
  }
}

function minutesToPct(minutes: number): number {
  return (minutes / STRIP_MINUTES) * 100;
}

function blockToPct(
  block: DayBlockItem,
  timezone: string,
): { left: number; width: number } | null {
  const startMin = isoToStripMinutes(block.startTime, timezone);
  const endMin = isoToStripMinutes(block.endTime, timezone);
  if (startMin >= endMin || endMin <= 0 || startMin >= STRIP_MINUTES) return null;
  return { left: minutesToPct(startMin), width: minutesToPct(endMin - startMin) };
}

function isoToHHMM(iso: string, timezone: string): string {
  try {
    return new Intl.DateTimeFormat("es", {
      timeZone: timezone,
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    }).format(new Date(iso));
  } catch {
    return "";
  }
}

// ── Props ──────────────────────────────────────────────────────────────────

export interface DayAvailabilityStripProps {
  /** N doctors with their blocks for the day (from useServiceDayStrips). */
  doctors: ServiceDayDoctor[];
  isPending?: boolean;
  isError?: boolean;
  dateLocal: string;                   // YYYY-MM-DD
  selectedStartIso: string | null;     // drives time-cursor + slot highlight
  selectedEndIso: string | null;
  selectedDoctorId: string | null;     // which lane is selected (amber border)
  onSelectDoctor: (doctorId: string) => void;
  timezone?: string;
}

// ── Swimlane ───────────────────────────────────────────────────────────────

interface SwimLaneProps {
  doctor: ServiceDayDoctor;
  isSelected: boolean;
  onSelect: () => void;
  selectedStartIso: string | null;
  selectedEndIso: string | null;
  timeCursorPct: number | null;
  timezone: string;
}

function SwimLane({
  doctor,
  isSelected,
  onSelect,
  selectedStartIso,
  selectedEndIso,
  timeCursorPct,
  timezone,
}: SwimLaneProps) {
  const hasBlocks = doctor.blocks.length > 0;

  // Selected slot pct (only on the selected doctor's lane)
  const selectedPct =
    isSelected && selectedStartIso && selectedEndIso
      ? (() => {
          const s = isoToStripMinutes(selectedStartIso, timezone);
          const e = isoToStripMinutes(selectedEndIso, timezone);
          if (s >= e) return null;
          return { left: minutesToPct(s), width: minutesToPct(e - s) };
        })()
      : null;

  const busyBlocks = doctor.blocks.filter((b) => b.kind === "busy");

  return (
    <div
      data-testid={`swimlane-${doctor.doctorId}`}
      className={cn(
        "flex items-center gap-2 cursor-pointer rounded px-1 py-0.5 transition-colors",
        isSelected
          ? "border border-[hsl(var(--agent-mateo))] bg-[hsl(var(--agent-mateo)/8)]"
          : "border border-transparent hover:border-border hover:bg-muted/30",
      )}
      role="button"
      tabIndex={0}
      aria-pressed={isSelected}
      aria-label={`Seleccionar médico: ${doctor.doctorLabel}`}
      onClick={onSelect}
      onKeyDown={(e) => {
        if (e.key === "Enter" || e.key === " ") {
          e.preventDefault();
          onSelect();
        }
      }}
    >
      {/* Label — fixed width */}
      <span
        className="w-24 shrink-0 truncate text-xs font-medium text-foreground"
        title={doctor.doctorLabel}
      >
        {doctor.doctorLabel}
      </span>

      {/* Timeline bar */}
      <div className="relative flex-1 h-4 overflow-hidden rounded bg-muted">
        {!hasBlocks ? (
          /* Sin horario (RN-4) */
          <span className="absolute inset-0 flex items-center justify-center text-xs text-muted-foreground">
            Sin horario
          </span>
        ) : (
          <>
            {/* Working/busy blocks */}
            {doctor.blocks.map((block, i) => {
              const pct = blockToPct(block, timezone);
              if (!pct) return null;
              return (
                <div
                  key={i}
                  data-testid={`swimlane-${doctor.doctorId}-block-${i}`}
                  className={cn(
                    "absolute inset-y-0",
                    block.kind === "working_hours"
                      ? "bg-success/25"
                      : block.kind === "busy"
                        ? "bg-destructive/50"
                        : "bg-muted-foreground/20",
                  )}
                  style={{ left: `${pct.left}%`, width: `${pct.width}%` }}
                />
              );
            })}

            {/* Selected slot highlight (amber) — only on selected lane */}
            {selectedPct ? (
              <div
                data-testid={`swimlane-${doctor.doctorId}-selected`}
                className="absolute inset-y-0 bg-[hsl(var(--agent-mateo)/50)] ring-1 ring-[hsl(var(--agent-mateo))]"
                style={{ left: `${selectedPct.left}%`, width: `${selectedPct.width}%` }}
                aria-hidden="true"
              />
            ) : null}

            {/* Time cursor — vertical line at current hora (advisory) */}
            {timeCursorPct !== null ? (
              <div
                data-testid={`swimlane-${doctor.doctorId}-cursor`}
                className="absolute inset-y-0 w-px bg-[hsl(var(--agent-mateo))]"
                style={{ left: `${timeCursorPct}%` }}
                aria-hidden="true"
              />
            ) : null}
          </>
        )}
      </div>

      {/* Busy labels (compact, only when selected) */}
      {isSelected && busyBlocks.length > 0 ? (
        <span className="shrink-0 text-xs text-muted-foreground">
          {busyBlocks.map((b, i) => (
            <span key={i}>
              {isoToHHMM(b.startTime, timezone)}–{isoToHHMM(b.endTime, timezone)}
            </span>
          ))}
        </span>
      ) : null}
    </div>
  );
}

// ── Component ──────────────────────────────────────────────────────────────

/**
 * DayAvailabilityStrip — N-doctor swimlane timeline (T-D3).
 *
 * Receives doctors[] from parent (NuevaCitaView calls useServiceDayStrips).
 * Swimlanes are keyboard-accessible (Enter/Space to select).
 */
export function DayAvailabilityStrip({
  doctors,
  isPending = false,
  isError = false,
  dateLocal,
  selectedStartIso,
  selectedEndIso,
  selectedDoctorId,
  onSelectDoctor,
  timezone = "America/Lima",
}: DayAvailabilityStripProps) {
  if (isPending) {
    return (
      <div
        data-testid="day-strip-loading"
        className="flex flex-col gap-1"
        aria-busy={true}
        aria-label="Cargando disponibilidad del día..."
      >
        {[0, 1, 2].map((i) => (
          <div key={i} className="h-6 w-full animate-pulse rounded bg-muted" />
        ))}
      </div>
    );
  }

  if (isError) {
    return (
      <div
        data-testid="day-strip-error"
        className="text-xs text-muted-foreground"
      >
        No se pudo cargar la disponibilidad del día.
      </div>
    );
  }

  if (doctors.length === 0) {
    return (
      <div
        data-testid="day-strip-empty"
        className="rounded-md border border-dashed border-border bg-muted/20 px-3 py-3 text-xs text-muted-foreground"
      >
        No hay médicos asignados a este servicio para la fecha seleccionada.
      </div>
    );
  }

  // Time-cursor pct: position of selectedStartIso within the strip
  const timeCursorPct =
    selectedStartIso
      ? (() => {
          const min = isoToStripMinutes(selectedStartIso, timezone);
          return minutesToPct(min);
        })()
      : null;

  return (
    <div data-testid="day-strip" className="flex flex-col gap-1">
      {/* Header */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-foreground">
          Vista del día · {dateLocal}
        </span>
        <span className="text-xs text-muted-foreground">07:00–21:00</span>
      </div>

      {/* Swimlanes */}
      <div
        role="group"
        aria-label={`Médicos disponibles para el ${dateLocal}`}
        className="flex flex-col gap-0.5"
      >
        {doctors.map((doc) => (
          <SwimLane
            key={doc.doctorId}
            doctor={doc}
            isSelected={doc.doctorId === selectedDoctorId}
            onSelect={() => onSelectDoctor(doc.doctorId)}
            selectedStartIso={selectedStartIso}
            selectedEndIso={selectedEndIso}
            timeCursorPct={timeCursorPct}
            timezone={timezone}
          />
        ))}
      </div>

      {/* Shared hour axis */}
      <div className="ml-[calc(6rem+0.5rem)] relative h-3 w-full" aria-hidden="true">
        {AXIS_HOURS.map((h) => {
          const posMin = (h - STRIP_START_HOUR) * 60;
          const pct = minutesToPct(posMin);
          return (
            <span
              key={h}
              className="absolute -translate-x-1/2 text-xs text-muted-foreground"
              style={{ left: `${pct}%` }}
            >
              {String(h).padStart(2, "0")}
            </span>
          );
        })}
      </div>

      {/* Legend */}
      <div className="ml-[calc(6rem+0.5rem)] flex items-center gap-3 mt-0.5" aria-hidden="true">
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <span className="inline-block h-2 w-4 rounded-sm bg-success/40" />
          Atención
        </span>
        <span className="flex items-center gap-1 text-xs text-muted-foreground">
          <span className="inline-block h-2 w-4 rounded-sm bg-destructive/50" />
          Ocupado
        </span>
        {selectedDoctorId ? (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <span className="inline-block h-2 w-4 rounded-sm bg-[hsl(var(--agent-mateo)/50)]" />
            Cita nueva
          </span>
        ) : null}
      </div>
    </div>
  );
}
