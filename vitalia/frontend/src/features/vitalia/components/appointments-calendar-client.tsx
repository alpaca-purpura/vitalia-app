// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * AppointmentsCalendarClient — calendar view of upcoming bookings.
 *
 * Groups bookings by date. Shows status badge per booking.
 * Uses useBookings hook (no @luana/core/scheduling dependency — not yet available).
 *
 * @architecture-group vitalia-ui-strings
 */
"use client";

import { useMemo } from "react";
import { cn } from "@/lib/cn";
import { useBookings } from "@/features/vitalia/api/use-bookings";
import type { BookingSummary } from "@/features/vitalia/types/booking.types";

export interface AppointmentsCalendarClientProps {
  statusFilter?: string;
  className?: string;
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDateHeader(iso: string): string {
  return new Date(iso).toLocaleDateString("es", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("es", {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function groupByDate(
  bookings: BookingSummary[],
): Map<string, BookingSummary[]> {
  const map = new Map<string, BookingSummary[]>();
  for (const booking of bookings) {
    const dateKey = booking.slot_iso.slice(0, 10); // "YYYY-MM-DD"
    const existing = map.get(dateKey);
    if (existing) {
      existing.push(booking);
    } else {
      map.set(dateKey, [booking]);
    }
  }
  // Sort keys ascending
  return new Map([...map.entries()].sort(([a], [b]) => a.localeCompare(b)));
}

const STATUS_LABEL: Record<string, string> = {
  pending_payment: "Pago pendiente",
  awaiting_consent: "Esperando consentimiento",
  confirmed_deposit: "Depósito confirmado",
  confirmed_full: "Confirmada",
  cancelled: "Cancelada",
  completed: "Completada",
};

const STATUS_CLASS: Record<string, string> = {
  pending_payment: "bg-yellow-100 text-yellow-700",
  awaiting_consent: "bg-orange-100 text-orange-700",
  confirmed_deposit: "bg-blue-100 text-blue-700",
  confirmed_full: "bg-green-100 text-green-700",
  cancelled: "bg-gray-100 text-gray-500",
  completed: "bg-gray-100 text-gray-600",
};

function BookingCard({ booking }: { booking: BookingSummary }) {
  const statusLabel = STATUS_LABEL[booking.status] ?? booking.status;
  const statusClass =
    STATUS_CLASS[booking.status] ?? "bg-gray-100 text-gray-600";

  return (
    <div
      className="flex items-center gap-3 rounded-md border border-gray-100 bg-white px-3 py-2.5 hover:bg-gray-50 transition-colors"
      role="listitem"
    >
      <div className="text-center w-14 shrink-0">
        <p className="text-sm font-semibold text-gray-800">
          {formatTime(booking.slot_iso)}
        </p>
        <p className="text-xs text-gray-400">{booking.duration_minutes} min</p>
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs text-gray-500 font-mono truncate">
          Booking {booking.id.slice(0, 8)}...
        </p>
      </div>
      <span
        className={cn(
          "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium shrink-0",
          statusClass,
        )}
        aria-label={`Estado: ${statusLabel}`}
      >
        {statusLabel}
      </span>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export function AppointmentsCalendarClient({
  statusFilter,
  className,
}: AppointmentsCalendarClientProps) {
  const { data, isLoading, isError } = useBookings(
    statusFilter ? { status: statusFilter } : undefined,
  );

  const grouped = useMemo(() => {
    const bookings = data?.bookings ?? [];
    return groupByDate(bookings);
  }, [data?.bookings]);

  if (isError) {
    return (
      <div
        className={cn(
          "rounded-lg border border-red-200 bg-red-50 p-6 text-center",
          className,
        )}
        role="alert"
      >
        <p className="text-sm text-red-700">
          Error al cargar citas. Intenta recargar la página.
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className={cn("flex flex-col gap-4", className)}
        role="status"
        aria-busy={true}
        aria-live="polite"
      >
        {[0, 1, 2].map((i) => (
          <div key={i} className="space-y-2">
            <div className="h-4 w-40 rounded bg-gray-200 animate-pulse" />
            <div className="h-12 w-full rounded-md bg-gray-100 animate-pulse" />
          </div>
        ))}
      </div>
    );
  }

  if (grouped.size === 0) {
    return (
      <div
        className={cn(
          "rounded-lg border border-dashed border-gray-200 p-8 text-center",
          className,
        )}
        role="status"
      >
        <p className="text-sm text-gray-500">Sin citas programadas.</p>
      </div>
    );
  }

  return (
    <div
      className={cn("flex flex-col gap-6", className)}
      aria-label="Calendario de citas"
    >
      {[...grouped.entries()].map(([dateKey, dayBookings]) => (
        <section key={dateKey} className="space-y-2">
          <h3 className="text-sm font-semibold text-gray-700 capitalize">
            {formatDateHeader(dayBookings[0]!.slot_iso)}
          </h3>
          <div role="list" className="flex flex-col gap-2">
            {dayBookings.map((booking) => (
              <BookingCard key={booking.id} booking={booking} />
            ))}
          </div>
        </section>
      ))}

      {data?.total !== undefined && data.total > 0 && (
        <p className="text-xs text-gray-400 text-right">
          {data.total} cita{data.total !== 1 ? "s" : ""} en total
        </p>
      )}
    </div>
  );
}
