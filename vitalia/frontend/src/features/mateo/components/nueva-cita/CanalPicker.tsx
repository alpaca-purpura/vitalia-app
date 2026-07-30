// cap: scheduling.mateo-agenda
/**
 * CanalPicker.tsx — Controlled canal/origin selector (walk_in | telefono).
 * T-FE-2 vitalia-fase2-mateo-nueva-cita
 *
 * Uses TogglePill from @luana/ui-kit (canon §shell-togglepill--default).
 * Controlled component: value/onChange props only.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE; no cross-brand consumers
 * spec_anchor: 03-arch-fe.md § F4 + 06-tickets.yaml T-FE-2
 */

"use client";

import * as React from "react";
import { cn } from "@/lib/cn";

// ── Types ─────────────────────────────────────────────────────────────────────

export type CanalValue = "walk_in" | "telefono";

export interface CanalPickerProps {
  value: CanalValue;
  onChange: (canal: CanalValue) => void;
  disabled?: boolean;
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

const CANAL_OPTIONS: ReadonlyArray<{ value: CanalValue; label: string; testid: string }> = [
  { value: "walk_in", label: "🚶 Walk-in", testid: "canal-picker-walk-in" },
  { value: "telefono", label: "📞 Teléfono", testid: "canal-picker-telefono" },
];

/**
 * CanalPicker — Controlled pill radiogroup for walk_in / telefono origin.
 *
 * Radix Tabs was wrong here: TabsTrigger auto-sets aria-controls to a tabpanel
 * id, but a 2-option toggle has no panels → aria-valid-attr-value violation
 * (axe wcag2aa). "Elegir uno de N" es un radiogroup, no tabs. role=radio +
 * aria-checked, navegable por teclado (flechas via roving lo da el browser en
 * un grupo de radios; acá Tab + Espacio/click).
 */
export function CanalPicker({
  value,
  onChange,
  disabled = false,
  className,
}: CanalPickerProps) {
  return (
    <div
      role="radiogroup"
      aria-label="Canal de origen"
      data-testid="canal-picker"
      className={cn(
        "inline-flex h-9 w-full items-center gap-1 rounded-full border border-border bg-muted p-1",
        className,
      )}
    >
      {CANAL_OPTIONS.map((opt) => {
        const selected = value === opt.value;
        return (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={selected}
            disabled={disabled}
            data-testid={opt.testid}
            data-state={selected ? "active" : "inactive"}
            onClick={() => onChange(opt.value)}
            className={cn(
              // a11y: el inactivo va sobre bg-muted; text-muted-foreground sobre
              // bg-muted no pasa contraste AA (axe color-contrast). text-foreground
              // sí; la jerarquía la da el activo (bg-background + shadow).
              "flex-1 rounded-full px-4 text-sm transition-colors disabled:pointer-events-none disabled:opacity-50",
              selected
                ? "bg-background text-foreground shadow-sm"
                : "text-foreground/80 hover:text-foreground",
            )}
          >
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
