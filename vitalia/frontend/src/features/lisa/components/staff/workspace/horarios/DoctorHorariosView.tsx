// cap: clinics.lisa.doctores
// story-origin: vitalia-fase2-lisa-doctores
/**
 * DoctorHorariosView.tsx — "use client" root for doctor horarios workspace tab.
 *
 * Per ADR-vitalia-004 § 3: Client Component root (interactivity: calendar drag, week nav, toggles).
 * Receives doctorId from SSR page. Hydrates blocks via React Query.
 * Zustand manages UI state (calendarWeek, dragDraft).
 *
 * Contains:
 *   - Section heading + info
 *   - Semana|Mes toggle pills (D3-E — default: Semana)
 *   - AvailabilityCalendar (week grid + drag-to-create + week nav + 24h toggle)
 *   - MonthCalendar (month 6×7 grid — read-only nav, no writes)
 *
 * D3-E: Semana|Mes toggle — drag-create lives only in week view (RN-D3E-2).
 *       Clicking a day in month view → switch to Semana of that week.
 *
 * T-FE-vista-mes vitalia-fase2-lisa-doctores
 * spec_anchor: 01-spec.md § D3-E + 03-arch-fe.md § FSD-Lite layout
 * downstream-regression-na: brand-local vitalia FE component; no cross-brand consumers
 */

"use client";

import React, { useState, useCallback } from "react";
import { cn } from "@/lib/utils";
import { AvailabilityCalendar } from "./AvailabilityCalendar";
import { MonthCalendar } from "./MonthCalendar";
import { useStaffUiStore } from "../../../../store/staff-ui-store";

// ── Types ─────────────────────────────────────────────────────────────────────

type CalendarView = "semana" | "mes";

export interface DoctorHorariosViewProps {
  doctorId: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

export function DoctorHorariosView({ doctorId }: DoctorHorariosViewProps) {
  // Toggle state: "semana" (default, drag-create) | "mes" (read-only nav)
  const [view, setView] = useState<CalendarView>("semana");

  // Zustand: setCalendarWeek — called when user clicks a day in month view
  const setCalendarWeek = useStaffUiStore((s) => s.setCalendarWeek);

  /**
   * Called by MonthCalendar when user clicks a day.
   * Switches to Semana view + sets the Zustand calendarWeek to the Monday of that week.
   */
  const handleSwitchToWeek = useCallback(
    (mondayIso: string) => {
      setCalendarWeek(mondayIso);
      setView("semana");
    },
    [setCalendarWeek],
  );

  return (
    <div
      data-testid="horarios-view"
      // bug-horarios-toolbar-sticky: overflow-hidden makes THIS leaf the scroll
      // boundary. The parent EntityWorkspaceLayout content slot is
      // `flex-1 min-h-0 overflow-auto` (core @luana/ui-kit, N3 canon — not ours
      // to touch). Without overflow-hidden here, the calendar grid grows tall
      // (24h = 24×48px) past the slot's box, the SLOT scrolls, and the toolbar
      // franjas (heading + calendar header) ride along. Clamping this root forces
      // the inner grid's own `flex-1 overflow-auto` to absorb the scroll, so the
      // two flex-shrink-0 toolbars + day-header stay fixed (parity with N2/N3).
      className="flex flex-col h-full min-h-0 overflow-hidden"
      aria-label="Gestión de disponibilidad del doctor"
    >
      {/* ── Section heading + toggle ────────────────────────────────────── */}
      <div className="px-5 pt-5 pb-3 flex-shrink-0">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-base font-semibold text-foreground">
              Disponibilidad
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Define los horarios en que este doctor puede atender pacientes.
              Los cambios se guardan automáticamente.
            </p>
          </div>

          {/* Semana | Mes pills toggle */}
          <div
            role="group"
            aria-label="Vista del calendario"
            className="flex items-center rounded-md border border-border/60 p-0.5 gap-0.5 flex-shrink-0 self-start mt-0.5"
          >
            <button
              data-testid="toggle-semana"
              role="radio"
              aria-checked={view === "semana"}
              onClick={() => setView("semana")}
              className={cn(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1",
                view === "semana"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent",
              )}
            >
              Semana
            </button>
            <button
              data-testid="toggle-mes"
              role="radio"
              aria-checked={view === "mes"}
              onClick={() => setView("mes")}
              className={cn(
                "rounded px-2.5 py-1 text-xs font-medium transition-colors",
                "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-1",
                view === "mes"
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:text-foreground hover:bg-accent",
              )}
            >
              Mes
            </button>
          </div>
        </div>
      </div>

      {/* ── Calendar (week or month) ─────────────────────────────────────── */}
      <div className="flex-1 min-h-0 border border-border/40 rounded-lg mx-5 mb-5 overflow-hidden relative">
        {view === "semana" ? (
          <AvailabilityCalendar doctorId={doctorId} />
        ) : (
          <MonthCalendar
            doctorId={doctorId}
            onSwitchToWeek={handleSwitchToWeek}
          />
        )}
      </div>
    </div>
  );
}
