"use client";

import * as React from "react";
import { cn } from "@luana/format/utils";
import { TimePicker } from "./TimePicker";

export interface TimeRange {
  /** "HH:mm" 24h, or "" when unset. */
  start: string;
  /** "HH:mm" 24h, or "" when unset. */
  end: string;
}

export interface TimeRangePreset {
  label: string;
  start: string;
  end: string;
}

/** Generic defaults — override via `presets` (pass `[]` to hide). */
export const DEFAULT_TIME_RANGE_PRESETS: TimeRangePreset[] = [
  { label: "Mañana", start: "09:00", end: "13:00" },
  { label: "Tarde", start: "14:00", end: "18:00" },
  { label: "Todo el día", start: "00:00", end: "23:59" },
];

interface TimeRangePickerProps {
  /** Controlled value. Partial allowed (one bound set, the other empty). */
  value?: Partial<TimeRange>;
  onChange: (value: TimeRange) => void;
  className?: string;
  /** Minute granularity for the ↑↓ arrows (default 5). */
  stepMinutes?: number;
  /** Accessible labels for each bound. */
  startLabel?: string;
  endLabel?: string;
  /** Visible separator between the two pickers. */
  separator?: React.ReactNode;
  /** Quick-pick chips. Defaults to {@link DEFAULT_TIME_RANGE_PRESETS}; pass `[]` to hide. */
  presets?: TimeRangePreset[];
  disabled?: boolean;
  /** Override the default "inicio debe ser anterior a fin" message. */
  errorMessage?: string;
}

/**
 * TimeRangePicker — selección de un rango horario (inicio–fin) en un solo día.
 *
 * Compone dos {@link TimePicker} segmentados (NO `<input type=time>` nativo) + presets
 * de acceso rápido + validación inicio<fin (`aria-invalid` + mensaje `role=alert`).
 * Comparación lexicográfica de "HH:mm" = cronológica por el zero-padding.
 *
 * Casos: horario de atención, ventanas de disponibilidad, franjas de campaña. NO para
 * elegir UN instante (→ `SmartDateTimePicker`) ni un rango de FECHAS (→ `Calendar mode="range"`).
 */
export function TimeRangePicker({
  value,
  onChange,
  className,
  stepMinutes = 5,
  startLabel = "Hora de inicio",
  endLabel = "Hora de fin",
  separator = "a",
  presets = DEFAULT_TIME_RANGE_PRESETS,
  disabled,
  errorMessage = "La hora de inicio debe ser anterior a la de fin.",
}: TimeRangePickerProps) {
  const start = value?.start ?? "";
  const end = value?.end ?? "";
  const invalid = start !== "" && end !== "" && start >= end;

  return (
    <div className={cn("flex flex-col gap-2", className)}>
      <div className="flex items-center gap-2">
        <TimePicker
          value={start}
          onChange={(start) => onChange({ start, end })}
          stepMinutes={stepMinutes}
          disabled={disabled}
          aria-label={startLabel}
          aria-invalid={invalid}
        />
        <span className="shrink-0 text-sm text-muted-foreground">{separator}</span>
        <TimePicker
          value={end}
          onChange={(end) => onChange({ start, end })}
          stepMinutes={stepMinutes}
          disabled={disabled}
          aria-label={endLabel}
          aria-invalid={invalid}
        />
      </div>
      {presets.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {presets.map((p) => {
            const active = p.start === start && p.end === end;
            return (
              <button
                key={p.label}
                type="button"
                disabled={disabled}
                onClick={() => onChange({ start: p.start, end: p.end })}
                aria-pressed={active}
                className={cn(
                  "rounded-full border px-2.5 py-0.5 text-xs font-medium transition-colors",
                  active
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-input text-muted-foreground hover:bg-muted",
                  disabled && "cursor-not-allowed opacity-50",
                )}
              >
                {p.label}
              </button>
            );
          })}
        </div>
      )}
      {invalid && (
        <p role="alert" className="text-xs text-destructive">
          {errorMessage}
        </p>
      )}
    </div>
  );
}
