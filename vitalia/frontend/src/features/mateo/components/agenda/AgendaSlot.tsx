// cap: scheduling.mateo-agenda
// story-origin: vitalia-fase1-s10-TBD
/**
 * AgendaSlot — bloque de turno en la grilla de agenda.
 * F1-S10 vitalia-fase1-empty-states — T-7
 *
 * Mockup parity: valeria-agenda-placeholder.html (ratificado Chris batch 2 · 2026-05-26)
 *
 * Server Component — puramente presentacional.
 * Named export (NO default) per FSD-Lite enforce.
 * No hex colors — Tailwind semantic tokens only.
 * Spanish neutro LatAm — sin voseo.
 * PHI masking: patient names son ficticios (no PHI real).
 *
 * 4 status variants via border-left + background gradient:
 *   paid    → green border + green gradient
 *   deposit → agent-adrian border + agent-adrian gradient
 *   unpaid  → amber border + amber gradient
 *   noshow  → red border + red gradient + line-through name
 *
 * 4 origin icons:
 *   walk-in  → 🚶
 *   phone    → 📞
 *   proactive → ✉
 *   web      → 🌐
 *
 * spec_anchor: 03-arch.md § 3.2 Agenda + 06-tickets.yaml T-7
 * downstream-regression-na: brand-local feature/valeria; no cross-brand consumers
 */

import { cn } from "@/lib/utils";

export type SlotStatus = "paid" | "deposit" | "unpaid" | "noshow";
export type SlotOrigin = "walk-in" | "phone" | "proactive" | "web";

export interface AgendaSlotProps {
  /** Patient fictional name (NO PHI real). */
  patient: string;
  /** Service description, e.g. "Limpieza dental". */
  service: string;
  /** Doctor name, e.g. "Dr. C. Mendoza". */
  doctor: string;
  /** Payment status. */
  status: SlotStatus;
  /** Appointment origin. */
  origin?: SlotOrigin;
  /** Optional clinical note (NO PHI). */
  note?: string;
  className?: string;
}

/** Origin icon map */
const ORIGIN_ICONS: Record<SlotOrigin, string> = {
  "walk-in": "🚶",
  phone: "📞",
  proactive: "✉",
  web: "🌐",
};

/** Status pill config */
const STATUS_CONFIG: Record<
  SlotStatus,
  { pill: string; pillClass: string; blockClass: string }
> = {
  paid: {
    pill: "✓ PAG",
    pillClass:
      "bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-300",
    blockClass:
      "border-l-[3px] border-green-500 bg-gradient-to-br from-green-500/10 to-green-500/5",
  },
  deposit: {
    pill: "30%",
    pillClass: "bg-agent-adrian-soft text-agent-adrian dark:bg-agent-adrian/20",
    blockClass:
      "border-l-[3px] border-agent-adrian bg-gradient-to-br from-agent-adrian/10 to-agent-adrian/5",
  },
  unpaid: {
    pill: "SIN PAGO",
    pillClass:
      "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-300",
    blockClass:
      "border-l-[3px] border-amber-500 bg-gradient-to-br from-amber-500/10 to-amber-500/5",
  },
  noshow: {
    pill: "⚠ NO-SHOW",
    pillClass: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300",
    blockClass:
      "border-l-[3px] border-red-500 bg-gradient-to-br from-red-500/10 to-red-500/5",
  },
};

/**
 * AgendaSlot — appointment block with patient, service, doctor, origin, status pill.
 * Server Component.
 */
export function AgendaSlot({
  patient,
  service,
  doctor,
  status,
  origin,
  note,
  className,
}: AgendaSlotProps) {
  const cfg = STATUS_CONFIG[status];
  const originIcon = origin ? ORIGIN_ICONS[origin] : undefined;

  return (
    <div
      className={cn(
        "h-full rounded-r-[4px] px-1.5 py-1",
        cfg.blockClass,
        className,
      )}
      data-testid="agenda-slot"
      data-status={status}
      data-origin={origin}
    >
      {/* Top row: patient name + origin icon + status pill */}
      <div className="flex items-center justify-between gap-1 min-w-0">
        <span
          className={cn(
            "text-[11px] font-semibold text-foreground truncate",
            status === "noshow" && "line-through text-muted-foreground",
          )}
        >
          {patient}
          {originIcon && (
            <span
              className="ml-0.5 text-[10px]"
              aria-label={`Origen: ${origin}`}
            >
              {originIcon}
            </span>
          )}
        </span>

        <span
          className={cn(
            "inline-flex items-center px-1.5 py-0.5 rounded-full text-[9px] font-semibold shrink-0",
            cfg.pillClass,
          )}
          data-testid={`slot-pill-${status}`}
        >
          {cfg.pill}
        </span>
      </div>

      {/* Detail row: service · doctor */}
      <div className="text-[10px] text-muted-foreground mt-0.5 truncate">
        {service} · {doctor}
      </div>

      {/* Optional note */}
      {note && (
        <div className="text-[10px] text-muted-foreground mt-0.5 italic truncate">
          {note}
        </div>
      )}
    </div>
  );
}
