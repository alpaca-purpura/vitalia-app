// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase1-s10-TBD
"use client";
/**
 * AgendaToolbar — barra de navegación period + toggle Día|Semana|Mes + CTA Crear cita.
 * F1-S10 vitalia-fase1-empty-states — T-7
 *
 * Mockup parity: valeria-agenda-placeholder.html (ratificado Chris batch 2 · 2026-05-26)
 *
 * Client Component — usa useState para period toggle + dropdown CTA.
 * Named export (NO default) per FSD-Lite enforce.
 * No hex colors — Tailwind semantic tokens only.
 * Spanish neutro LatAm — sin voseo.
 *
 * F2 anchor: period nav y CTA dropdown se cablearán con date arithmetic real + API mutations.
 *
 * spec_anchor: 03-arch.md § 3.2 Agenda + 06-tickets.yaml T-7
 * downstream-regression-na: brand-local feature/valeria; no cross-brand consumers
 */

import { useState, useRef, useEffect } from "react";
import { cn } from "@/lib/utils";

export type PeriodMode = "day" | "week" | "month";

export interface AgendaToolbarProps {
  /** Week range label — hardcoded mock F1, real date F2. */
  weekLabel?: string;
  /** Currently active period mode. */
  periodMode?: PeriodMode;
  /** Callback when period mode changes. */
  onPeriodChange?: (mode: PeriodMode) => void;
  /** Navigate to previous period. */
  onPrevWeek?: () => void;
  /** Navigate to next period. */
  onNextWeek?: () => void;
  /** Navigate to today. */
  onToday?: () => void;
  /** Open create appointment. */
  onCreateAppointment?: () => void;
  className?: string;
}

const PERIOD_LABELS: { value: PeriodMode; label: string }[] = [
  { value: "day", label: "Día" },
  { value: "week", label: "Semana" },
  { value: "month", label: "Mes" },
];

/** CTA dropdown items — 3 appointment origins. */
const CTA_ITEMS = [
  {
    icon: "🚶",
    label: "Walk-in",
    sublabel: "Paciente presente ahora",
  },
  {
    icon: "📞",
    label: "Reserva por teléfono",
    sublabel: "Fecha futura",
  },
  {
    icon: "✉",
    label: "Reagendar proactivamente",
    sublabel: "Desde un lead caliente",
  },
] as const;

/**
 * AgendaToolbar — period navigation + mode toggle + CTA Crear cita dropdown.
 * Client Component.
 */
export function AgendaToolbar({
  weekLabel = "Semana 26-31 May 2026",
  periodMode: externalPeriodMode,
  onPeriodChange,
  onPrevWeek,
  onNextWeek,
  onToday,
  onCreateAppointment,
  className,
}: AgendaToolbarProps) {
  // Internal period state (F1 visual only; F2 wires real date arithmetic)
  const [internalPeriod, setInternalPeriod] = useState<PeriodMode>("week");
  const activePeriod = externalPeriodMode ?? internalPeriod;

  // CTA dropdown state
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    function handleOutsideClick(e: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    if (dropdownOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, [dropdownOpen]);

  function handlePeriodChange(mode: PeriodMode) {
    setInternalPeriod(mode);
    onPeriodChange?.(mode);
  }

  return (
    <div
      className={cn(
        "flex items-center justify-between flex-wrap gap-3 px-4 py-3 border-b border-border",
        className,
      )}
      data-testid="agenda-toolbar"
    >
      {/* Left: period navigation + mode toggle */}
      <div className="flex items-center gap-2 flex-wrap">
        {/* Previous period */}
        <button
          type="button"
          onClick={onPrevWeek}
          aria-label="Período anterior"
          className="h-7 w-7 flex items-center justify-center rounded-md border border-border bg-background text-foreground text-sm hover:bg-muted transition-colors"
        >
          ‹
        </button>

        {/* Week label */}
        <span className="text-sm font-semibold text-foreground">
          {weekLabel}
        </span>

        {/* Next period */}
        <button
          type="button"
          onClick={onNextWeek}
          aria-label="Período siguiente"
          className="h-7 w-7 flex items-center justify-center rounded-md border border-border bg-background text-foreground text-sm hover:bg-muted transition-colors"
        >
          ›
        </button>

        {/* Period mode toggle (Día / Semana / Mes) */}
        <div
          role="group"
          aria-label="Modo de período"
          className="ml-2 inline-flex bg-muted rounded-md p-0.5"
        >
          {PERIOD_LABELS.map(({ value, label }) => (
            <button
              key={value}
              type="button"
              role="radio"
              aria-checked={activePeriod === value}
              onClick={() => handlePeriodChange(value)}
              data-testid={`period-toggle-${value}`}
              className={cn(
                "px-3 py-1 rounded text-xs font-medium transition-colors",
                activePeriod === value
                  ? "bg-background text-foreground shadow-sm font-semibold"
                  : "text-muted-foreground hover:text-foreground",
              )}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Hoy button */}
        <button
          type="button"
          onClick={onToday}
          className="text-xs px-2 py-1 rounded-md border border-border bg-background text-foreground hover:bg-muted transition-colors"
          data-testid="agenda-today-btn"
        >
          📅 Hoy
        </button>
      </div>

      {/* Right: CTA Crear cita dropdown */}
      <div className="relative" ref={dropdownRef}>
        <button
          type="button"
          onClick={() => {
            setDropdownOpen((prev) => !prev);
            onCreateAppointment?.();
          }}
          aria-haspopup="true"
          aria-expanded={dropdownOpen}
          data-testid="agenda-cta-crear-cita"
          className={cn(
            "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-semibold transition-colors",
            "bg-agent-valeria-soft text-agent-valeria",
            "border border-agent-valeria",
            "hover:bg-agent-valeria hover:text-white",
          )}
        >
          + Crear cita
          <span className="text-[10px]">▾</span>
        </button>

        {/* Dropdown menu */}
        {dropdownOpen && (
          <div
            role="menu"
            className="absolute right-0 mt-1 z-20 rounded-lg border border-border bg-background shadow-md p-1 min-w-[240px]"
            data-testid="agenda-cta-dropdown"
          >
            {CTA_ITEMS.map((item) => (
              <button
                key={item.label}
                type="button"
                role="menuitem"
                onClick={() => setDropdownOpen(false)}
                className="w-full text-left px-3 py-2 rounded-md hover:bg-muted flex items-start gap-2 text-xs transition-colors"
              >
                <span className="text-base shrink-0" aria-hidden="true">
                  {item.icon}
                </span>
                <div>
                  <div className="font-semibold text-foreground">
                    {item.label}
                  </div>
                  <div className="text-muted-foreground text-[10px]">
                    {item.sublabel}
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
