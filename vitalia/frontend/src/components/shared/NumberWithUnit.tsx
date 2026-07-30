// cap: lisa.servicios
// story-origin: vitalia-fase2-lisa-servicios T-5
//
// NumberWithUnit — vitalia-local shared molecule: a numeric input paired with
// a trailing unit. The unit is either a static label (`unit`) or a selectable
// dropdown (`units` + `unitValue` + `onUnitChange`). Reusable across vitalia
// surfaces (duración de cita, sesiones, ventanas de recurrencia, precios con
// sufijo). Composed from the @luana/ui-kit Input + Select primitives.
//
// LIFT CANDIDATE: this is generic enough to graduate to @luana/ui-kit via the
// /pm-luana promotion gate; built vitalia-local for this story per scope
// (core/@luana/ui-kit/src is forbidden-to-touch).
"use client";

import { Input } from "@luana/ui-kit";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@luana/ui-kit";
import { cn } from "@/lib/cn";

interface BaseProps {
  value: number;
  onChange: (value: number) => void;
  min?: number;
  step?: number;
  disabled?: boolean;
  placeholder?: string;
  className?: string;
  "aria-label"?: string;
}

interface StaticUnitProps extends BaseProps {
  /** A fixed, non-selectable unit label rendered after the input. */
  unit: string;
  units?: never;
  unitValue?: never;
  onUnitChange?: never;
}

interface SelectableUnitProps extends BaseProps {
  unit?: never;
  /** Selectable unit options rendered as a trailing dropdown. */
  units: string[];
  unitValue: string;
  onUnitChange: (unit: string) => void;
}

export type NumberWithUnitProps = StaticUnitProps | SelectableUnitProps;

export function NumberWithUnit(props: NumberWithUnitProps) {
  const {
    value,
    onChange,
    min,
    step,
    disabled,
    placeholder,
    className,
    "aria-label": ariaLabel,
  } = props;

  const handleNumber = (raw: string) => {
    if (raw === "") return; // let the field be momentarily empty without emitting
    const parsed = Number(raw);
    if (Number.isNaN(parsed)) return;
    if (min !== undefined && parsed < min) return; // clamp: never emit below min
    onChange(parsed);
  };

  return (
    <div className={cn("flex items-center gap-1.5", className)}>
      <Input
        type="number"
        inputMode="numeric"
        value={Number.isFinite(value) ? String(value) : ""}
        min={min}
        step={step}
        disabled={disabled}
        placeholder={placeholder}
        aria-label={ariaLabel}
        onChange={(e) => handleNumber(e.target.value)}
        className="w-24"
      />
      {"unit" in props && props.unit !== undefined ? (
        <span className="shrink-0 text-sm text-muted-foreground">{props.unit}</span>
      ) : (
        <Select
          value={props.unitValue}
          onValueChange={(v) => props.onUnitChange?.(v)}
          disabled={disabled}
        >
          <SelectTrigger className="w-32 shrink-0">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {props.units?.map((u) => (
              <SelectItem key={u} value={u}>
                {u}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}
    </div>
  );
}
