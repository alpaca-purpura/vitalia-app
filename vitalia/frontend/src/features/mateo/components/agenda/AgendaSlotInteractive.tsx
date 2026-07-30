// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase2-s1-TBD
"use client";

/**
 * AgendaSlotInteractive.tsx — Interactive appointment slot cell for calendar grids.
 * T-13 vitalia-fase2-valeria-agenda · F2-S1
 *
 * Extends the T-7 AgendaSlot (display-only) with:
 *   - onClick handler → opens AppointmentDrawer
 *   - keyboard navigation (focus-visible ring, Enter/Space via native <button>)
 *   - border-left status colors from CSS semantic tokens
 *   - origin badge emojis with ARIA labels
 *   - PHI-masked patient name (server-masked, never raw PHI)
 *   - aria-haspopup="dialog" (announces drawer intent to screen readers)
 *   - Full aria-label with masked name + service + status (SC-10)
 *
 * Visual contract: mockup slot-states-matrix.html
 * HIPAA-lite: patientNameMasked only (no raw PHI on FE)
 * Spanish neutro LatAm — sin voseo.
 *
 * Named exports only — NO default exports (FSD-Lite boundary enforcement).
 * downstream-regression-na: brand-local FE component; no cross-brand consumers
 * spec_anchor: 03-arch.md § 6.5 + 06-tickets.yaml T-13
 */

import { cn } from "@/lib/cn";
import type { AgendaSlot, SlotPaymentStatus, AppointmentOrigin } from "../../types/agenda.types";

// ── Status → border class map (mockup slot-states-matrix.html colors) ─────────

/**
 * Border-left 3px per payment status.
 * Colors reference vitalia CSS custom property color shortcuts (no raw hex/hsl literals).
 * Defined in globals.css: --vitalia-success-color, --vitalia-warning-color, etc.
 */
const STATUS_BORDER: Record<SlotPaymentStatus, string> = {
  paid:    "border-l-[3px] border-l-[color:var(--vitalia-success-color)]",
  deposit: "border-l-[3px] border-l-[color:var(--vitalia-warning-color)]",
  unpaid:  "border-l-[3px] border-l-[color:var(--vitalia-danger-color)]",
  no_show: "border-l-[3px] border-l-[color:var(--vitalia-muted-status-color)]",
};

const STATUS_BG: Record<SlotPaymentStatus, string> = {
  paid:    "vt-bg-success-12",
  deposit: "vt-bg-warning-12",
  unpaid:  "vt-bg-danger-12",
  no_show: "bg-card opacity-60",
};

// ── Origin badge config (mockup: 👤 walk_in, 📞 telefono, 🤖 proactivo_adrian, ➕ existing) ──

const ORIGIN_BADGE: Record<AppointmentOrigin, { icon: string; ariaLabel: string }> = {
  walk_in:          { icon: "👤", ariaLabel: "Walk-in" },
  phone:            { icon: "📞", ariaLabel: "Teléfono" },
  proactive_adrian: { icon: "🤖", ariaLabel: "Proactivo Adrián" },
  existing_patient: { icon: "➕", ariaLabel: "Paciente existente" },
};

// ── Time formatter (local display, not toLocaleDateString) ────────────────────

function formatSlotTime(isoString: string): string {
  try {
    const d = new Date(isoString);
    const h = String(d.getHours()).padStart(2, "0");
    const m = String(d.getMinutes()).padStart(2, "0");
    return `${h}:${m}`;
  } catch {
    return "--:--";
  }
}

// ── Props ─────────────────────────────────────────────────────────────────────

export interface AgendaSlotInteractiveProps {
  /** Slot data (PHI-masked server-side). */
  slot: AgendaSlot;
  /** Called with appointmentId when slot is clicked. */
  onClick: () => void;
  className?: string;
}

// ── Component ─────────────────────────────────────────────────────────────────

/**
 * Interactive appointment slot cell.
 *
 * Renders as a <button> with:
 * - 3px colored border-left (payment status)
 * - PHI-masked patient name + origin badge
 * - Service label + time
 * - Full ARIA label for screen readers
 * - focus-visible ring for keyboard navigation
 */
export function AgendaSlotInteractive({
  slot,
  onClick,
  className,
}: AgendaSlotInteractiveProps) {
  const badge = ORIGIN_BADGE[slot.origin];
  const isNoShow = slot.paymentStatus === "no_show";
  const startTime = formatSlotTime(slot.startTime);

  const ariaLabel = [
    `Slot ${startTime}`,
    slot.patientNameMasked,
    slot.serviceLabel,
    `estado ${slot.paymentStatus}`,
  ].join(" · ");

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        // Base
        "w-full rounded-md px-2 py-1.5 text-left text-sm",
        "transition-colors hover:brightness-95 active:scale-[0.99]",
        // Focus visible ring (keyboard nav - SC-10)
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
        // Status border + background
        STATUS_BORDER[slot.paymentStatus],
        STATUS_BG[slot.paymentStatus],
        className,
      )}
      role="button"
      aria-haspopup="dialog"
      aria-label={ariaLabel}
      data-status={slot.paymentStatus}
      data-testid="agenda-slot-interactive"
    >
      {/* Row 1: Patient name + origin badge */}
      <div className="flex items-start justify-between gap-1">
        <span
          className={cn(
            "truncate text-[11px] font-semibold leading-tight",
            isNoShow ? "line-through text-muted-foreground" : "text-foreground",
          )}
        >
          {slot.patientNameMasked}
        </span>

        <span
          className="shrink-0 text-[11px]"
          aria-label={badge.ariaLabel}
          role="img"
        >
          {badge.icon}
        </span>
      </div>

      {/* Row 2: Service + time */}
      <div className="mt-0.5 truncate text-[10px] text-muted-foreground">
        {slot.serviceLabel} · {startTime}
      </div>
    </button>
  );
}
