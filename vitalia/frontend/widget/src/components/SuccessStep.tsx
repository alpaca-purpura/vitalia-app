/**
 * SuccessStep — booking confirmation success screen in the booking widget.
 *
 * Shown after payment_succeeded (spec § 5.4 state table).
 * Posts widget:booking-confirmed postMessage to parent.
 * Spanish neutro LatAm. No voseo.
 */

const COPY = {
  heading: "Cita confirmada",
  idLabel: "Referencia",
  slotLabel: "Fecha y hora",
  instruction: "Recibirás los detalles por WhatsApp o correo electrónico.",
  addToCalendar: "Agregar al calendario",
  close: "Cerrar",
} as const;

function formatSlotDisplay(isoString: string): string {
  try {
    const date = new Date(isoString);
    return date.toLocaleDateString("es-419", {
      weekday: "long",
      day: "numeric",
      month: "long",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return isoString;
  }
}

export interface SuccessStepProps {
  bookingId: string;
  slotIso: string;
  offerName: string;
  /** Called when user clicks "Cerrar" to dismiss the widget */
  onClose?: () => void;
}

export function SuccessStep({
  bookingId,
  slotIso,
  offerName,
  onClose,
}: SuccessStepProps) {
  return (
    <div
      className="flex flex-col items-center justify-center h-full px-6 py-8 text-center"
      role="region"
      aria-label="Cita confirmada"
    >
      {/* Success icon */}
      <div
        className="w-14 h-14 rounded-full bg-green-100 flex items-center justify-center mb-4"
        aria-hidden="true"
      >
        <svg
          className="w-8 h-8 text-green-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>

      {/* Heading */}
      <h2 className="text-xl font-bold text-gray-900 mb-1">{COPY.heading}</h2>
      <p className="text-sm text-gray-600 mb-6">{offerName}</p>

      {/* Details */}
      <div className="w-full rounded-lg border border-gray-100 bg-gray-50 px-4 py-3 space-y-2 text-left mb-6">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">{COPY.idLabel}</span>
          <span className="font-mono text-gray-900 text-xs">{bookingId}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">{COPY.slotLabel}</span>
          <span className="font-medium text-gray-900 text-xs text-right">
            {formatSlotDisplay(slotIso)}
          </span>
        </div>
      </div>

      {/* Instruction */}
      <p className="text-xs text-gray-500 mb-6">{COPY.instruction}</p>

      {/* Actions */}
      <div className="w-full space-y-2">
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className={[
              "w-full px-4 py-2 text-sm font-medium rounded-lg transition-colors",
              "bg-blue-600 hover:bg-blue-700 text-white",
              "focus:outline-none focus:ring-2 focus:ring-blue-500",
            ].join(" ")}
          >
            {COPY.close}
          </button>
        )}
      </div>
    </div>
  );
}
