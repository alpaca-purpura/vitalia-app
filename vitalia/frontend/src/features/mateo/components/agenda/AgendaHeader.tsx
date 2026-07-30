// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AgendaHeader.tsx — View toggle + date navigation + freshness indicator.
 * T-12 vitalia-fase2-valeria-agenda · F2-S1
 *
 * Toolbar row at top of Valeria Agenda sub-tab.
 * Persists view + date to URL params via useAgendaFilters().
 *
 * Composition:
 *   [Dia | Semana | Mes] toggle  ·  [< Apr 2026 >] date nav  ·  [Actualizado hace X]
 *
 * T-13 will enhance with CrearCitaButton + export menu.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.4 + 06-tickets.yaml T-12
 */

import { ChevronLeft, ChevronRight, RefreshCw } from "lucide-react";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";
import { useAgendaFilters } from "../../hooks/useAgendaFilters";
import { useTenantLocale } from "@/hooks/useTenantLocale";
import { formatTenantDate } from "@/lib/format/formatTenantDate";
import type { AgendaView } from "../../types/agenda.types";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AgendaHeaderProps {
  tenantId: string;
  freshnessLabel: string;
  className?: string;
}

// ── View toggle config ─────────────────────────────────────────────────────────

const VIEW_OPTIONS: { value: AgendaView; label: string }[] = [
  { value: "dia", label: "Día" },
  { value: "semana", label: "Semana" },
  { value: "mes", label: "Mes" },
];

// ── Date navigation helpers ────────────────────────────────────────────────────

function parseDate(dateStr: string): Date {
  // Parse YYYY-MM-DD as local date (avoid UTC offset issues)
  const [year, month, day] = dateStr.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function formatDate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function stepDate(dateStr: string, view: AgendaView, direction: -1 | 1): string {
  const date = parseDate(dateStr);
  switch (view) {
    case "dia":
      date.setDate(date.getDate() + direction);
      break;
    case "semana":
      date.setDate(date.getDate() + direction * 7);
      break;
    case "mes":
      date.setMonth(date.getMonth() + direction);
      break;
  }
  return formatDate(date);
}

function formatDisplayDate(
  dateStr: string,
  view: AgendaView,
  timezone: string,
  locale: string,
): string {
  switch (view) {
    case "dia": {
      const isoDay = `${dateStr}T12:00:00`;
      return formatTenantDate(isoDay, timezone, locale);
    }
    case "semana": {
      // Show Monday of the week: "Sem. del 12 may. 2026"
      const date = parseDate(dateStr);
      const dayOfWeek = date.getDay();
      const diff = dayOfWeek === 0 ? -6 : 1 - dayOfWeek; // Monday
      date.setDate(date.getDate() + diff);
      const isoMonday = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}T12:00:00`;
      const formatted = new Intl.DateTimeFormat(locale, {
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: timezone,
      }).format(new Date(isoMonday));
      return `Sem. del ${formatted}`;
    }
    case "mes": {
      const isoMid = `${dateStr.slice(0, 7)}-15T12:00:00`;
      return new Intl.DateTimeFormat(locale, {
        month: "long",
        year: "numeric",
        timeZone: timezone,
      }).format(new Date(isoMid));
    }
  }
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Agenda toolbar with view toggle, date navigation, and freshness indicator.
 *
 * Persists view + date to URL params (useAgendaFilters handles URL sync).
 * T-13 will add CrearCitaButton + export menu on the right side.
 */
export function AgendaHeader({
  tenantId: _tenantId, // reserved for T-13 actions (export, create appointment)
  freshnessLabel,
  className,
}: AgendaHeaderProps) {
  const { view, date, setView, setDate } = useAgendaFilters();
  const { timezone, locale } = useTenantLocale();

  const handlePrev = () => setDate(stepDate(date, view, -1));
  const handleNext = () => setDate(stepDate(date, view, 1));
  const handleToday = () =>
    setDate(new Date().toISOString().slice(0, 10));

  return (
    <header
      className={cn(
        "flex flex-wrap items-center gap-3 border-b bg-background px-4 py-2",
        className,
      )}
      role="toolbar"
      aria-label="Controles de agenda"
    >
      {/* View toggle */}
      <div
        className="flex rounded-md border"
        role="group"
        aria-label="Modo de vista"
      >
        {VIEW_OPTIONS.map(({ value, label }) => (
          <Button
            key={value}
            variant="ghost"
            size="sm"
            className={cn(
              "rounded-none px-3 first:rounded-l-md last:rounded-r-md",
              view === value && "bg-muted font-medium",
            )}
            aria-pressed={view === value}
            onClick={() => setView(value)}
          >
            {label}
          </Button>
        ))}
      </div>

      {/* Date navigation */}
      <nav
        className="flex items-center gap-1"
        aria-label="Navegación de fecha"
      >
        <Button
          variant="ghost"
          size="icon"
          onClick={handlePrev}
          aria-label="Período anterior"
        >
          <ChevronLeft className="h-4 w-4" aria-hidden="true" />
        </Button>

        <Button
          variant="ghost"
          size="sm"
          className="min-w-[160px] text-center font-medium"
          onClick={handleToday}
          aria-label="Ir a hoy"
        >
          {formatDisplayDate(date, view, timezone, locale)}
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={handleNext}
          aria-label="Período siguiente"
        >
          <ChevronRight className="h-4 w-4" aria-hidden="true" />
        </Button>
      </nav>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Freshness indicator */}
      <div
        className="flex items-center gap-1.5 text-xs text-muted-foreground"
        aria-live="polite"
        aria-label="Última actualización"
      >
        <RefreshCw className="h-3 w-3" aria-hidden="true" />
        <span>{freshnessLabel}</span>
      </div>

      {/* T-13 will add CrearCitaButton here */}
    </header>
  );
}
