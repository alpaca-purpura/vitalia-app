// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * BloquePopover.tsx — Popover for creating/editing/deleting availability blocks.
 *
 * D3-F rewrite: Google Calendar–style recurrence editor.
 *   - Select "Repetir" (Shadcn canónico §2.5 — NEVER native <select>):
 *     · No se repite
 *     · Todos los días
 *     · Cada semana el {día}
 *     · Cada 2 semanas el {día}
 *     · Personalizado…
 *   - "Personalizado…" sub-editor: "Repetir cada [N] semana(s)" +
 *     day chips L M X J V S D (a11y: tab/space/enter) +
 *     Termina: Nunca / El [fecha] / Después de [N] repeticiones
 *   - formatRecurrenceSummary always visible (RN-D3F-1: mirrors BE semantics)
 *   - Payload: days_of_week: number[] + interval: number (legacy day_of_week/freq dropped)
 *
 * Opens when:
 *   - User finishes drag-to-create (draft mode: new block, no id yet)
 *   - User clicks an existing block (edit/delete mode: block.id present)
 *
 * Recurrence is RESOLVED BY BACKEND via dateutil.rrule (D-2).
 * FE just sends the block spec; does NOT expand recurrence client-side.
 *
 * T-FE-recurrencia-editor vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-F + 03-arch-fe.md § BloquePopover
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { addLocalDays, toLocalIsoDate } from "@/lib/format/calendarDates";
import { toast } from "sonner";
import {
  useCreateBlock,
  useUpdateBlock,
  useDeleteBlock,
  type CreateBlockPayload,
  type UpdateBlockPayload,
} from "../../../../api/staff";

// D3-F payload fields (days_of_week/interval) live in the API contract types
// (audit Carril A 2026-06-12 — local parallel-builder extension folded into
// api/staff.ts CreateBlockPayload/UpdateBlockPayload: single contract source).
type CreateBlockPayloadD3F = CreateBlockPayload;

type UpdateBlockPayloadD3F = UpdateBlockPayload;
import { availabilityBlockSchema } from "../../../../types/staff-schema";
import type { RepeatPreset } from "../../../../types/staff-schema";
import type {
  AvailabilityBlock,
  RecurrentBlock,
} from "../../../../types/staff.types";
import type { AvailabilityBlockFormValues } from "../../../../types/staff-schema";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface BloquePopoverAnchor {
  x: number;
  y: number;
}

export interface BloquePopoverProps {
  doctorId: string;
  /** Existing block (edit/delete mode). Null for new block (draft mode). */
  block: AvailabilityBlock | null;
  /** Draft data from drag-to-create (only when block === null). */
  draft?: {
    dayOfWeek: number;
    startTime: string;
    endTime: string;
  } | null;
  isOpen: boolean;
  onClose: () => void;
  anchor: BloquePopoverAnchor;
  isExisting?: boolean;
  /** ISO date string of the Monday of the currently viewed week (for one_off specific_date) */
  calendarWeek?: string;
  /**
   * ISO date YYYY-MM-DD of the clicked occurrence.
   * Required for recurrent-block scoped deletes (round-5 bug7 follow-up #1).
   * Passed from AvailabilityCalendar when the user clicks a painted occurrence.
   */
  occurrenceDate?: string;
}

// ── Day chips constants ────────────────────────────────────────────────────────

/** Short chip labels for the day chips: 0=Mon..6=Sun */
const DAY_CHIP_LABELS = ["L", "M", "X", "J", "V", "S", "D"] as const;

/** Full Spanish day names for summary text — 0=Monday..6=Sunday */
const DAY_NAMES_FULL = [
  "lunes",
  "martes",
  "miércoles",
  "jueves",
  "viernes",
  "sábado",
  "domingo",
] as const;

function getDayLabel(dayIndex: number): string {
  return DAY_NAMES_FULL[dayIndex] ?? "";
}

// ── formatRecurrenceSummary (RN-D3F-1 — mirrors BE format_recurrence_summary) ──

/**
 * formatRecurrenceSummary — human-readable recurrence pattern summary.
 *
 * Semantics mirror BE recurrence_summary.py (RN-D3F-1: same output).
 * Decision tree:
 *   - kind=one_off            → "Bloque único"
 *   - daysOfWeek.length=1, interval=1 → "Se repite cada semana el {día}, …"
 *   - daysOfWeek.length=1, interval=2 → "Se repite cada 2 semanas el {día}, …"
 *   - interval=1, many days   → "Se repite todos los días, …" (when 7 days)
 *   - any other               → "Se repite cada {N} semana(s) {el/los días}, …"
 * End condition suffix:
 *   - open_ended → "indefinidamente"
 *   - end_date   → "hasta el {date}"
 *   - occurrences → "{N} veces"
 */
export function formatRecurrenceSummary(params: {
  repeatPreset: RepeatPreset;
  daysOfWeek: number[];
  interval: number;
  endConditionKind: "end_date" | "occurrences" | "open_ended";
  endDate?: string | null;
  occurrences?: number | null;
}): string {
  const { repeatPreset, daysOfWeek, interval, endConditionKind, endDate, occurrences } =
    params;

  if (repeatPreset === "none") return "Bloque único";

  // End condition
  let endSuffix = "";
  if (endConditionKind === "open_ended") {
    endSuffix = "indefinidamente";
  } else if (endConditionKind === "end_date") {
    endSuffix = endDate ? `hasta el ${endDate}` : "hasta una fecha";
  } else if (endConditionKind === "occurrences") {
    // bug7 round-6: "N repeticiones" = N ciclos completos del patrón (cada uno con
    // todos los días). El wording "repeticiones" coincide con el selector "Termina".
    endSuffix = occurrences
      ? `${occurrences} ${occurrences === 1 ? "repetición" : "repeticiones"}`
      : "N repeticiones";
  }

  const sortedDays = [...daysOfWeek].sort((a, b) => a - b);
  const dayNames = sortedDays.map((d) => getDayLabel(d));

  // "Todos los días" special case
  if (sortedDays.length === 7 && interval === 1) {
    return endSuffix
      ? `Se repite todos los días, ${endSuffix}`
      : "Se repite todos los días";
  }

  // Day list with "y" before last.
  // W1: use "los" (not "el") when >1 day — BE outputs "los lunes y jueves" for plural.
  let dayPhrase = "";
  if (dayNames.length === 1) {
    dayPhrase = `el ${dayNames[0] ?? ""}`;
  } else if (dayNames.length === 2) {
    dayPhrase = `los ${dayNames[0] ?? ""} y ${dayNames[1] ?? ""}`;
  } else {
    const allButLast = dayNames.slice(0, -1).join(", ");
    dayPhrase = `los ${allButLast} y ${dayNames[dayNames.length - 1] ?? ""}`;
  }

  // Interval phrase
  let intervalPhrase = "";
  if (interval === 1) {
    intervalPhrase = "cada semana";
  } else if (interval === 2) {
    intervalPhrase = "cada 2 semanas";
  } else {
    intervalPhrase = `cada ${interval} semanas`;
  }

  const base = `Se repite ${intervalPhrase} ${dayPhrase}`;
  return endSuffix ? `${base}, ${endSuffix}` : base;
}

// ── Preset → {daysOfWeek, interval} mapping ──────────────────────────────────

function presetToDaysAndInterval(
  preset: RepeatPreset,
  anchorDayOfWeek: number,
): { daysOfWeek: number[]; interval: number } {
  switch (preset) {
    case "daily":
      return { daysOfWeek: [0, 1, 2, 3, 4, 5, 6], interval: 1 };
    case "weekly":
      return { daysOfWeek: [anchorDayOfWeek], interval: 1 };
    case "biweekly":
      return { daysOfWeek: [anchorDayOfWeek], interval: 2 };
    case "custom":
    case "none":
      return { daysOfWeek: [anchorDayOfWeek], interval: 1 };
  }
}

function daysAndIntervalToPreset(
  daysOfWeek: number[],
  interval: number,
): RepeatPreset {
  if (daysOfWeek.length === 7 && interval === 1) return "daily";
  if (daysOfWeek.length === 1 && interval === 1) return "weekly";
  if (daysOfWeek.length === 1 && interval === 2) return "biweekly";
  return "custom";
}

// ── Date helpers ──────────────────────────────────────────────────────────────
// bug7 r4: getSpecificDate delegates to the TZ-stable SSoT (calendarDates) so a
// one_off's specific_date never drifts a day under a negative UTC offset.

function getSpecificDate(mondayIso: string, dayOfWeek: number): string {
  return addLocalDays(mondayIso, dayOfWeek);
}

// ── Default form values ───────────────────────────────────────────────────────

/**
 * bug7 r3 (caso 9): el BE serializa times como "HH:mm:ss" — el Zod schema
 * exige "HH:mm" estricto. Sin normalizar, EDITAR cualquier bloque existente
 * fallaba validación en silencio (onInvalid) y el PATCH nunca salía.
 */
function hhmm(t: string): string {
  return t.length >= 5 ? t.slice(0, 5) : t;
}

function buildDefaultValues(
  block: AvailabilityBlock | null,
  draft: BloquePopoverProps["draft"],
): AvailabilityBlockFormValues {
  if (block) {
    if (block.kind === "recurrent") {
      const rb = block as RecurrentBlock;
      // Support legacy blocks (dayOfWeek/freq fields) + new D3-F blocks (daysOfWeek/interval)
      const daysOfWeek =
        rb.daysOfWeek && rb.daysOfWeek.length > 0
          ? rb.daysOfWeek
          : rb.dayOfWeek !== undefined
            ? [rb.dayOfWeek]
            : [0];
      const interval =
        rb.interval > 0
          ? rb.interval
          : rb.freq === "biweekly"
            ? 2
            : 1;
      const repeatPreset = daysAndIntervalToPreset(daysOfWeek, interval);
      return {
        kind: "recurrent",
        repeatPreset,
        daysOfWeek,
        interval,
        startTime: hhmm(rb.startTime),
        endTime: hhmm(rb.endTime),
        endConditionKind: rb.endConditionKind,
        endDate: rb.endDate ?? null,
        occurrences: rb.occurrences ?? null,
      };
    }
    return {
      kind: "one_off",
      specificDate: block.specificDate,
      startTime: hhmm(block.startTime),
      endTime: hhmm(block.endTime),
    };
  }

  const anchorDay = draft?.dayOfWeek ?? 0;
  if (draft) {
    return {
      kind: "recurrent",
      repeatPreset: "weekly",
      daysOfWeek: [anchorDay],
      interval: 1,
      startTime: draft.startTime,
      endTime: draft.endTime,
      endConditionKind: "open_ended",
      endDate: null,
      occurrences: null,
    };
  }

  return {
    kind: "recurrent",
    repeatPreset: "weekly",
    daysOfWeek: [0],
    interval: 1,
    startTime: "09:00",
    endTime: "13:00",
    endConditionKind: "open_ended",
    endDate: null,
    occurrences: null,
  };
}

// ── DayChip — keyboard-accessible day toggle ──────────────────────────────────

interface DayChipProps {
  dayIndex: number;
  label: string;
  selected: boolean;
  onToggle: (dayIndex: number) => void;
}

function DayChip({ dayIndex, label, selected, onToggle }: DayChipProps) {
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLButtonElement>) => {
      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        onToggle(dayIndex);
      }
    },
    [dayIndex, onToggle],
  );

  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={selected}
      aria-label={DAY_NAMES_FULL[dayIndex]}
      data-testid={`day-chip-${dayIndex}`}
      onClick={() => onToggle(dayIndex)}
      onKeyDown={handleKeyDown}
      className={cn(
        "w-7 h-7 rounded-full text-xs font-semibold transition-colors",
        "focus:outline-none focus:ring-2 focus:ring-agent-lisa focus:ring-offset-1",
        selected
          ? "bg-agent-lisa text-black"
          : "bg-muted text-muted-foreground hover:bg-muted/70",
      )}
    >
      {label}
    </button>
  );
}

// ── BloquePopover ─────────────────────────────────────────────────────────────

export function BloquePopover({
  doctorId,
  block,
  draft,
  isOpen,
  onClose,
  anchor,
  isExisting = false,
  calendarWeek = toLocalIsoDate(new Date()),
  occurrenceDate,
}: BloquePopoverProps) {
  const popoverRef = useRef<HTMLDivElement>(null);
  const [showDeleteWarning, setShowDeleteWarning] = useState(false);
  const [showRecurrentDeleteDialog, setShowRecurrentDeleteDialog] = useState(false);
  const [preservedCount, setPreservedCount] = useState(0);

  const createBlock = useCreateBlock(doctorId);
  const updateBlock = useUpdateBlock(doctorId);
  const deleteBlock = useDeleteBlock(doctorId);

  const anchorDay = block?.kind === "recurrent"
    ? ((block as RecurrentBlock).daysOfWeek?.[0] ?? (block as RecurrentBlock).dayOfWeek ?? 0)
    : draft?.dayOfWeek ?? 0;

  const {
    control,
    handleSubmit,
    watch,
    reset,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<AvailabilityBlockFormValues>({
    resolver: zodResolver(availabilityBlockSchema),
    defaultValues: buildDefaultValues(block, draft),
  });

  const formKind = watch("kind");

  // Watch recurrent-specific fields only when kind=recurrent
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const formValues = watch() as Record<string, any>;
  const repeatPreset: RepeatPreset =
    formKind === "recurrent" ? (formValues.repeatPreset as RepeatPreset ?? "weekly") : "none";
  const daysOfWeek: number[] =
    formKind === "recurrent" ? (formValues.daysOfWeek as number[] ?? []) : [];
  const interval: number =
    formKind === "recurrent" ? (formValues.interval as number ?? 1) : 1;
  const endConditionKind =
    formKind === "recurrent"
      ? (formValues.endConditionKind as "end_date" | "occurrences" | "open_ended" ?? "open_ended")
      : "open_ended";
  const endDate = formKind === "recurrent" ? (formValues.endDate as string | null) : null;
  const occurrences = formKind === "recurrent" ? (formValues.occurrences as number | null) : null;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const errorsAny = errors as Record<string, any>;

  // Reset when block/draft changes
  useEffect(() => {
    reset(buildDefaultValues(block, draft));
  }, [block, draft, reset]);

  // Close on Escape
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    if (isOpen) {
      document.addEventListener("keydown", handler);
      return () => document.removeEventListener("keydown", handler);
    }
  }, [isOpen, onClose]);

  // Position popover near anchor, keep within viewport
  const [position, setPosition] = useState({ top: 0, left: 0 });
  useEffect(() => {
    if (!isOpen) return;
    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const pw = 336; // popover width
    const ph = 500; // estimated max popover height
    let left = anchor.x + 8;
    let top = anchor.y + 8;
    if (left + pw > vw - 16) left = Math.max(8, anchor.x - pw - 8);
    if (top + ph > vh - 16) top = Math.max(8, anchor.y - ph - 8);
    setPosition({ top, left });
  }, [anchor, isOpen]);

  // Handle preset change: update daysOfWeek + interval to match preset
  const handlePresetChange = useCallback(
    (preset: string) => {
      const p = preset as RepeatPreset;
      setValue("repeatPreset" as Parameters<typeof setValue>[0], p as never);
      if (p !== "custom") {
        const { daysOfWeek: newDays, interval: newInterval } =
          presetToDaysAndInterval(p, anchorDay);
        setValue("daysOfWeek" as Parameters<typeof setValue>[0], newDays as never);
        setValue("interval" as Parameters<typeof setValue>[0], newInterval as never);
      }
    },
    [setValue, anchorDay],
  );

  // Handle day chip toggle
  const handleDayToggle = useCallback(
    (dayIndex: number) => {
      const current = daysOfWeek.includes(dayIndex)
        ? daysOfWeek.filter((d) => d !== dayIndex)
        : [...daysOfWeek, dayIndex].sort((a, b) => a - b);
      // Must keep at least 1 day
      if (current.length === 0) return;
      setValue("daysOfWeek" as Parameters<typeof setValue>[0], current as never);
    },
    [daysOfWeek, setValue],
  );

  if (!isOpen) return null;

  // ── Submit handler ─────────────────────────────────────────────────────────

  const onSubmit = handleSubmit(
    async (values) => {
      try {
        if (values.kind === "one_off") {
          // One-off block
          if (isExisting && block) {
            // bug7 r3 D-3b: editar un one_off DEBE patchear (antes era un no-op
            // silencioso con toast de éxito mentiroso). El BE soporta PATCH
            // one_off (kind + specific_date + times).
            const oneOffUpdate: UpdateBlockPayloadD3F = {
              kind: "one_off",
              start_time: values.startTime,
              end_time: values.endTime,
              specific_date: values.specificDate,
            };
            await updateBlock.mutateAsync({
              blockId: block.id,
              payload: oneOffUpdate,
            });
          } else {
            const oneOffPayload: CreateBlockPayloadD3F = {
              kind: "one_off",
              start_time: values.startTime,
              end_time: values.endTime,
              specific_date: values.specificDate,
            };
            await createBlock.mutateAsync(oneOffPayload);
          }
        } else {
          // Recurrent block — D3-F payload: days_of_week[] + interval
          if (isExisting && block && block.kind === "recurrent") {
            const updatePayload: UpdateBlockPayloadD3F = {
              days_of_week: values.daysOfWeek,
              interval: values.interval,
              end_condition_kind: values.endConditionKind,
              end_date: values.endDate,
              occurrences: values.occurrences,
              start_time: values.startTime,
              end_time: values.endTime,
            };
            await updateBlock.mutateAsync({
              blockId: block.id,
              payload: updatePayload,
            });
          } else {
            // "No se repite" preset: create as one_off for the specific date
            if (values.repeatPreset === "none") {
              const specificDate = getSpecificDate(calendarWeek, anchorDay);
              const nonePayload: CreateBlockPayloadD3F = {
                kind: "one_off",
                start_time: values.startTime,
                end_time: values.endTime,
                specific_date: specificDate,
              };
              await createBlock.mutateAsync(nonePayload);
            } else {
              const recurrentPayload: CreateBlockPayloadD3F = {
                kind: "recurrent",
                days_of_week: values.daysOfWeek,
                interval: values.interval,
                start_time: values.startTime,
                end_time: values.endTime,
                end_condition_kind: values.endConditionKind,
                end_date: values.endDate ?? null,
                occurrences: values.occurrences ?? null,
              };
              await createBlock.mutateAsync(recurrentPayload);
            }
          }
        }
        toast.success("Bloque guardado");
        onClose();
      } catch (err) {
        console.error("Error saving block:", err);
        toast.error("No pudimos guardar el bloque. Intenta de nuevo.");
        // Popover stays open on error — do NOT call onClose() here
      }
    },
    // onInvalid: Zod validation failure — prevents silent no-op on invalid form
    () => {
      toast.error("Revisa los campos del bloque");
    },
  );

  // ── Delete handler ─────────────────────────────────────────────────────────

  const handleDeleteClick = () => {
    if (!block) return;
    if (block.kind === "recurrent") {
      setShowRecurrentDeleteDialog(true);
    } else {
      setShowDeleteWarning(true);
    }
  };

  // one_off: simple confirm → delete the whole block (no scope needed)
  const handleDeleteConfirm = async () => {
    if (!block) return;
    try {
      const result = await deleteBlock.mutateAsync({ blockId: block.id });
      setPreservedCount(result?.preservedAppointments ?? 0);
      setShowDeleteWarning(false);
      toast.success("Bloque eliminado");
      onClose();
    } catch (err) {
      console.error("Error deleting block:", err);
      setShowDeleteWarning(false);
      toast.error("No pudimos eliminar el bloque. Intenta de nuevo.");
    }
  };

  // recurrent: scope-specific delete handlers
  const handleDeleteOccurrence = async () => {
    if (!block) return;
    try {
      await deleteBlock.mutateAsync({
        blockId: block.id,
        scope: "occurrence",
        occurrenceDate: occurrenceDate,
      });
      setShowRecurrentDeleteDialog(false);
      toast.success("Turno eliminado");
      onClose();
    } catch (err) {
      console.error("Error deleting occurrence:", err);
      setShowRecurrentDeleteDialog(false);
      toast.error("No pudimos eliminar el turno. Intenta de nuevo.");
    }
  };

  const handleDeleteThisAndFuture = async () => {
    if (!block) return;
    try {
      await deleteBlock.mutateAsync({
        blockId: block.id,
        scope: "this_and_future",
        occurrenceDate: occurrenceDate,
      });
      setShowRecurrentDeleteDialog(false);
      toast.success("Turnos eliminados");
      onClose();
    } catch (err) {
      console.error("Error deleting this and future:", err);
      setShowRecurrentDeleteDialog(false);
      toast.error("No pudimos eliminar los turnos. Intenta de nuevo.");
    }
  };

  // Format occurrence date for display (es-419, e.g. "lun 22 jun")
  const formattedOccurrenceDate = occurrenceDate
    ? (() => {
        try {
          const d = new Date(`${occurrenceDate}T12:00:00`);
          return new Intl.DateTimeFormat("es-419", {
            weekday: "short",
            day: "numeric",
            month: "short",
          }).format(d);
        } catch {
          return occurrenceDate;
        }
      })()
    : null;

  const isPending =
    isSubmitting ||
    createBlock.isPending ||
    updateBlock.isPending ||
    deleteBlock.isPending;

  // ── Render helpers ─────────────────────────────────────────────────────────

  // Build preset label for the select trigger
  const anchorDayName = getDayLabel(anchorDay);
  function buildPresetLabel(preset: RepeatPreset, currentDays: number[], currentInterval: number): string {
    switch (preset) {
      case "none": return "No se repite";
      case "daily": return "Todos los días";
      case "weekly": return `Cada semana el ${anchorDayName}`;
      case "biweekly": return `Cada 2 semanas el ${anchorDayName}`;
      case "custom": {
        const sorted = [...currentDays].sort((a, b) => a - b);
        const names = sorted.map((d) => getDayLabel(d));
        const plural = names.length > 1 ? "los" : "el";
        const intervalStr = currentInterval === 1 ? "semana" : `${currentInterval} semanas`;
        return `Cada ${intervalStr} ${plural} ${names.join(", ")}`;
      }
    }
  }

  // Human summary (always visible when preset ≠ none)
  const humanSummary =
    formKind === "recurrent" && repeatPreset !== "none"
      ? formatRecurrenceSummary({
          repeatPreset,
          daysOfWeek,
          interval,
          endConditionKind,
          endDate,
          occurrences,
        })
      : null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Popover */}
      <div
        ref={popoverRef}
        role="dialog"
        aria-modal="true"
        aria-label={isExisting ? "Editar bloque de disponibilidad" : "Crear bloque de disponibilidad"}
        data-testid="bloque-popover"
        className={cn(
          "fixed z-50 w-84 rounded-lg border border-border bg-card shadow-lg",
          "p-4 space-y-3 overflow-y-auto max-h-[90vh]",
        )}
        style={{ top: position.top, left: position.left, width: "21rem" }}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold">
            {isExisting ? "Editar bloque" : "Nuevo bloque"}
          </h3>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground text-lg leading-none"
            aria-label="Cerrar"
          >
            ×
          </button>
        </div>

        <form onSubmit={onSubmit} className="space-y-3">
          {/* Time range */}
          <div className="flex gap-2 items-center">
            <div className="flex-1">
              <Label htmlFor="startTime" className="text-xs">
                Inicio
              </Label>
              <Controller
                control={control}
                name="startTime"
                render={({ field }) => (
                  <Input
                    {...field}
                    id="startTime"
                    type="time"
                    className="h-8 text-sm"
                    aria-invalid={!!errors.startTime}
                  />
                )}
              />
            </div>
            <span className="mt-5 text-muted-foreground">–</span>
            <div className="flex-1">
              <Label htmlFor="endTime" className="text-xs">
                Fin
              </Label>
              <Controller
                control={control}
                name="endTime"
                render={({ field }) => (
                  <Input
                    {...field}
                    id="endTime"
                    type="time"
                    className="h-8 text-sm"
                    aria-invalid={!!errors.endTime}
                  />
                )}
              />
            </div>
          </div>

          {/* Select "Repetir" — Shadcn canónico (§2.5: NEVER native <select>) */}
          <div>
            <Label className="text-xs mb-1 block">Repetir</Label>
            <Controller
              control={control}
              name={"repeatPreset" as Parameters<typeof control.register>[0]}
              render={({ field }) => (
                <Select
                  value={field.value as string}
                  onValueChange={(v) => {
                    field.onChange(v);
                    handlePresetChange(v);
                  }}
                >
                  <SelectTrigger
                    className="h-8 text-sm"
                    data-testid="select-repetir"
                  >
                    <SelectValue>
                      {buildPresetLabel(
                        field.value as RepeatPreset,
                        daysOfWeek,
                        interval,
                      )}
                    </SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="none">No se repite</SelectItem>
                    <SelectItem value="daily">Todos los días</SelectItem>
                    <SelectItem value="weekly">
                      Cada semana el {anchorDayName}
                    </SelectItem>
                    <SelectItem value="biweekly">
                      Cada 2 semanas el {anchorDayName}
                    </SelectItem>
                    <SelectItem value="custom">Personalizado…</SelectItem>
                  </SelectContent>
                </Select>
              )}
            />
          </div>

          {/* Personalizado sub-editor (only when custom preset) */}
          {formKind === "recurrent" && repeatPreset === "custom" && (
            <div
              className="rounded-md border border-border bg-muted/30 p-3 space-y-3"
              data-testid="custom-recurrence-editor"
            >
              {/* Interval: "Repetir cada [N] semana(s)" */}
              <div className="flex items-center gap-2">
                <Label className="text-xs whitespace-nowrap">Repetir cada</Label>
                <Controller
                  control={control}
                  name={"interval" as Parameters<typeof control.register>[0]}
                  render={({ field }) => (
                    <Input
                      type="number"
                      min={1}
                      max={52}
                      value={field.value as number}
                      onChange={(e) =>
                        field.onChange(
                          Math.max(1, Number(e.target.value) || 1),
                        )
                      }
                      className="h-7 w-14 text-sm text-center"
                      aria-label="Intervalo de semanas"
                      data-testid="input-interval"
                    />
                  )}
                />
                <span className="text-xs text-muted-foreground">
                  {interval === 1 ? "semana" : "semanas"}
                </span>
              </div>

              {/* Day chips: L M X J V S D */}
              <div>
                <Label className="text-xs mb-1.5 block">Días</Label>
                <Controller
                  control={control}
                  name={"daysOfWeek" as Parameters<typeof control.register>[0]}
                  render={() => (
                    <div
                      className="flex gap-1.5 flex-wrap"
                      role="group"
                      aria-label="Días de la semana"
                      data-testid="day-chips-group"
                    >
                      {DAY_CHIP_LABELS.map((label, idx) => (
                        <DayChip
                          key={idx}
                          dayIndex={idx}
                          label={label}
                          selected={daysOfWeek.includes(idx)}
                          onToggle={handleDayToggle}
                        />
                      ))}
                    </div>
                  )}
                />
                {errorsAny.daysOfWeek && (
                  <p className="text-xs text-destructive mt-0.5">
                    {errorsAny.daysOfWeek.message}
                  </p>
                )}
              </div>

              {/* End condition: Termina */}
              <div>
                <Label className="text-xs mb-1 block">Termina</Label>
                <Controller
                  control={control}
                  name={"endConditionKind" as Parameters<typeof control.register>[0]}
                  render={({ field }) => (
                    <Select
                      value={field.value as string}
                      onValueChange={field.onChange}
                    >
                      <SelectTrigger className="h-8 text-sm" data-testid="select-termina">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="open_ended">Nunca</SelectItem>
                        <SelectItem value="end_date">El (fecha)</SelectItem>
                        <SelectItem value="occurrences">
                          Después de N repeticiones
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>

              {/* Conditional: end date picker */}
              {endConditionKind === "end_date" && (
                <div>
                  <Label htmlFor="endDate" className="text-xs">
                    Fecha de fin
                  </Label>
                  <Controller
                    control={control}
                    name={"endDate" as Parameters<typeof control.register>[0]}
                    render={({ field }) => (
                      <Input
                        id="endDate"
                        type="date"
                        value={(field.value as string | null) ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        className="h-8 text-sm"
                        aria-invalid={!!errorsAny.endDate}
                      />
                    )}
                  />
                  {errorsAny.endDate && (
                    <p className="text-xs text-destructive mt-0.5">
                      {errorsAny.endDate.message}
                    </p>
                  )}
                </div>
              )}

              {/* Conditional: occurrences */}
              {endConditionKind === "occurrences" && (
                <div>
                  <Label htmlFor="occurrences" className="text-xs">
                    Número de repeticiones
                  </Label>
                  <Controller
                    control={control}
                    name={"occurrences" as Parameters<typeof control.register>[0]}
                    render={({ field }) => (
                      <Input
                        id="occurrences"
                        type="number"
                        min={1}
                        max={520}
                        value={(field.value as number | null) ?? ""}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value ? Number(e.target.value) : null,
                          )
                        }
                        className="h-8 text-sm"
                        aria-invalid={!!errorsAny.occurrences}
                        placeholder="Ej: 8"
                        data-testid="input-occurrences"
                      />
                    )}
                  />
                  {errorsAny.occurrences && (
                    <p className="text-xs text-destructive mt-0.5">
                      {errorsAny.occurrences.message}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}

          {/* End condition for non-custom presets (weekly/biweekly/daily) */}
          {formKind === "recurrent" &&
            repeatPreset !== "none" &&
            repeatPreset !== "custom" && (
              <div className="space-y-2">
                <Label className="text-xs mb-1 block">Termina</Label>
                <Controller
                  control={control}
                  name={"endConditionKind" as Parameters<typeof control.register>[0]}
                  render={({ field }) => (
                    <Select
                      value={field.value as string}
                      onValueChange={field.onChange}
                    >
                      <SelectTrigger className="h-8 text-sm" data-testid="select-termina-simple">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="open_ended">Nunca</SelectItem>
                        <SelectItem value="end_date">El (fecha)</SelectItem>
                        <SelectItem value="occurrences">
                          Después de N repeticiones
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />

                {endConditionKind === "end_date" && (
                  <Controller
                    control={control}
                    name={"endDate" as Parameters<typeof control.register>[0]}
                    render={({ field }) => (
                      <Input
                        id="endDateSimple"
                        type="date"
                        value={(field.value as string | null) ?? ""}
                        onChange={(e) =>
                          field.onChange(e.target.value || null)
                        }
                        className="h-8 text-sm"
                        aria-label="Fecha de fin"
                        aria-invalid={!!errorsAny.endDate}
                      />
                    )}
                  />
                )}

                {endConditionKind === "occurrences" && (
                  <Controller
                    control={control}
                    name={"occurrences" as Parameters<typeof control.register>[0]}
                    render={({ field }) => (
                      <Input
                        id="occurrencesSimple"
                        type="number"
                        min={1}
                        max={520}
                        value={(field.value as number | null) ?? ""}
                        onChange={(e) =>
                          field.onChange(
                            e.target.value ? Number(e.target.value) : null,
                          )
                        }
                        className="h-8 text-sm"
                        aria-label="Número de repeticiones"
                        placeholder="Ej: 8"
                        data-testid="input-occurrences-simple"
                      />
                    )}
                  />
                )}
              </div>
            )}

          {/* One-off: specific date */}
          {formKind === "one_off" && (
            <div>
              <Label htmlFor="specificDate" className="text-xs">
                Fecha puntual
              </Label>
              <Controller
                control={control}
                name="specificDate"
                render={({ field }) => (
                  <Input
                    {...field}
                    id="specificDate"
                    type="date"
                    className="h-8 text-sm"
                    aria-invalid={!!errorsAny.specificDate}
                  />
                )}
              />
            </div>
          )}

          {/* Human summary — always visible when recurrent (RN-D3F-1) */}
          {humanSummary && (
            <p
              className="text-xs text-muted-foreground bg-muted/40 rounded px-2 py-1.5 leading-snug"
              data-testid="recurrence-summary"
              aria-live="polite"
            >
              {humanSummary}
            </p>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-1">
            {isExisting && (
              <Button
                data-testid="btn-delete-block"
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 text-xs text-destructive hover:text-destructive hover:bg-destructive/10"
                onClick={handleDeleteClick}
                disabled={isPending}
              >
                Eliminar
              </Button>
            )}
            <div className={cn("flex gap-2 ml-auto")}>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="h-7 text-xs"
                onClick={onClose}
                disabled={isPending}
              >
                Cancelar
              </Button>
              <Button
                type="submit"
                size="sm"
                className="h-7 text-xs bg-agent-lisa hover:bg-agent-lisa/90 text-black"
                disabled={isPending}
                data-testid="btn-save-block"
              >
                {isPending
                  ? "Guardando..."
                  : isExisting
                    ? "Actualizar"
                    : "Crear bloque"}
              </Button>
            </div>
          </div>
        </form>
      </div>

      {/* SC-3b: Delete warning dialog — one_off blocks */}
      <Dialog
        open={showDeleteWarning}
        onOpenChange={(open) => !open && setShowDeleteWarning(false)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Eliminar bloque de disponibilidad</DialogTitle>
          </DialogHeader>
          <div className="text-sm text-muted-foreground space-y-2">
            {preservedCount > 0 ? (
              <p>
                Este bloque tiene{" "}
                <strong className="text-foreground">
                  {preservedCount} cita{preservedCount !== 1 ? "s" : ""} confirmada
                  {preservedCount !== 1 ? "s" : ""}
                </strong>
                . Si lo eliminas, esas citas seguirán vigentes pero el doctor
                dejará de estar disponible para nuevas reservas en ese horario.
              </p>
            ) : (
              <p>
                ¿Confirmas que deseas eliminar este bloque de disponibilidad?
                Los turnos futuros sin cita se liberarán.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowDeleteWarning(false)}
              disabled={deleteBlock.isPending}
            >
              Cancelar
            </Button>
            <Button
              data-testid="btn-delete-confirm"
              variant="destructive"
              size="sm"
              onClick={handleDeleteConfirm}
              disabled={deleteBlock.isPending}
            >
              {deleteBlock.isPending ? "Eliminando..." : "Sí, eliminar"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* SC-3b round-5: Recurrent delete scope dialog */}
      <Dialog
        open={showRecurrentDeleteDialog}
        onOpenChange={(open) => !open && setShowRecurrentDeleteDialog(false)}
      >
        <DialogContent data-testid="dialog-delete-scope">
          <DialogHeader>
            <DialogTitle>¿Eliminar este bloque repetido?</DialogTitle>
          </DialogHeader>
          <div className="text-sm text-muted-foreground">
            <p>
              Elige cuántos turnos deseas eliminar
              {formattedOccurrenceDate ? ` a partir del ${formattedOccurrenceDate}` : ""}.
            </p>
          </div>
          <DialogFooter className="flex-col gap-2 sm:flex-col">
            <Button
              data-testid="btn-delete-occurrence"
              variant="destructive"
              size="sm"
              onClick={handleDeleteOccurrence}
              disabled={deleteBlock.isPending}
              className="w-full justify-start"
            >
              {formattedOccurrenceDate
                ? `Solo este turno (${formattedOccurrenceDate})`
                : "Solo este turno"}
            </Button>
            <Button
              data-testid="btn-delete-this-and-future"
              variant="destructive"
              size="sm"
              onClick={handleDeleteThisAndFuture}
              disabled={deleteBlock.isPending}
              className="w-full justify-start"
            >
              Este y los siguientes
            </Button>
            <Button
              data-testid="btn-delete-scope-cancel"
              variant="ghost"
              size="sm"
              onClick={() => setShowRecurrentDeleteDialog(false)}
              disabled={deleteBlock.isPending}
              className="w-full"
            >
              Cancelar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
