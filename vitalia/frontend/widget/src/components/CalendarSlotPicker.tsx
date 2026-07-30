/**
 * CalendarSlotPicker — calendar slot selection step for the booking widget.
 *
 * Renders available time slots from the vitalia/api/bookings/availability endpoint.
 * Standalone component: no Next.js imports, no Clerk auth (public booking flow).
 *
 * Accessibility: keyboard nav (Enter/Space on slot buttons), aria-pressed for selected.
 */

import { cn } from "../lib/cn";

export interface SlotItem {
  slot_iso: string;
  duration_minutes: number;
  doctor_id: string;
}

export interface CalendarSlotPickerProps {
  slots: SlotItem[];
  selectedSlot: SlotItem | null;
  onSelectSlot: (slot: SlotItem) => void;
  isLoading: boolean;
  /** Optional error message shown above slot grid */
  errorMessage?: string | null;
}

/**
 * Format ISO UTC string to local time display (HH:mm).
 * Widget runs in patient's browser — display in local time.
 */
function formatSlotTime(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", hour12: false });
  } catch {
    return isoString;
  }
}

/**
 * Format ISO UTC date to local date display (e.g. "Mié 20 may").
 */
function formatSlotDate(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString("es-419", {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
  } catch {
    return isoString;
  }
}

/**
 * Group slots by calendar date (YYYY-MM-DD key in local timezone).
 */
function groupByDate(slots: SlotItem[]): Map<string, SlotItem[]> {
  const groups = new Map<string, SlotItem[]>();
  for (const slot of slots) {
    const date = new Date(slot.slot_iso);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
    const existing = groups.get(key) ?? [];
    existing.push(slot);
    groups.set(key, existing);
  }
  return groups;
}

export function CalendarSlotPicker({
  slots,
  selectedSlot,
  onSelectSlot,
  isLoading,
  errorMessage,
}: CalendarSlotPickerProps) {
  // Loading state
  if (isLoading) {
    return (
      <div aria-busy="true" aria-label="Cargando horarios disponibles" className="space-y-4 p-4">
        {/* Skeleton rows */}
        {Array.from({ length: 3 }).map((_, i) => (
          <div
            key={`skeleton-${i}`}
            className="h-10 bg-gray-100 rounded-lg animate-pulse"
            aria-hidden="true"
          />
        ))}
      </div>
    );
  }

  // Empty state
  if (slots.length === 0) {
    return (
      <div role="status" className="flex flex-col items-center justify-center py-12 px-4 text-center">
        <p className="text-gray-500 text-sm">
          No hay horarios disponibles para los próximos días.
        </p>
        <p className="text-gray-400 text-xs mt-1">
          Comunícate con la clínica para más opciones.
        </p>
      </div>
    );
  }

  const grouped = groupByDate(slots);

  return (
    <div className="space-y-5 p-4">
      {errorMessage && (
        <div role="alert" className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-800">
          {errorMessage}
        </div>
      )}

      <div className="text-sm font-semibold text-gray-700 mb-2">
        Selecciona un horario
      </div>

      {Array.from(grouped.entries()).map(([dateKey, dateSlots]) => (
        <div key={dateKey} className="space-y-2">
          {/* Date header */}
          <div className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            {formatSlotDate(dateSlots[0].slot_iso)}
          </div>

          {/* Slot buttons grid */}
          <div className="grid grid-cols-3 gap-2">
            {dateSlots.map((slot) => {
              const isSelected = selectedSlot?.slot_iso === slot.slot_iso;
              return (
                <button
                  key={slot.slot_iso}
                  type="button"
                  onClick={() => onSelectSlot(slot)}
                  aria-pressed={isSelected}
                  aria-label={`Horario ${formatSlotTime(slot.slot_iso)} - ${slot.duration_minutes} minutos`}
                  className={cn(
                    "rounded-lg border px-3 py-2 text-sm font-medium transition-colors",
                    "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1",
                    isSelected
                      ? "bg-blue-600 text-white border-blue-600"
                      : "bg-white text-gray-800 border-gray-200 hover:border-blue-300 hover:bg-blue-50"
                  )}
                >
                  {formatSlotTime(slot.slot_iso)}
                </button>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
