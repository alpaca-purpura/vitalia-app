/**
 * BookingWidgetRoot — orchestrates the 4-step booking widget flow.
 *
 * Steps: CalendarSlotPicker → ConsentStep (if required) → PaymentStep → SuccessStep
 * Communicates with parent via postMessage (postmessage-protocol.ts SSoT).
 *
 * Security (D11):
 * - Origin validation via createOriginValidator (only ALLOWED_ORIGINS can send)
 * - Signed patient JWT from URL params (pre-issued by BE for clinic_slug)
 * - NEVER stores patient PII in localStorage/sessionStorage/URL params
 *
 * Per 03-arch-fe.md § 9 + spec § 5.4 + spec § 17 Q5=B.
 * Spanish neutro LatAm. No voseo.
 */

import { useState, useEffect, useCallback } from "react";
import { CalendarSlotPicker } from "./CalendarSlotPicker";
import { ConsentStep } from "./ConsentStep";
import { PaymentStep } from "./PaymentStep";
import { SuccessStep } from "./SuccessStep";
import { postMessageToParent, createOriginValidator } from "../postmessage-protocol";
import type { SlotItem } from "./CalendarSlotPicker";

// ── Step machine ──────────────────────────────────────────────────────────────

type BookingStep =
  | "slot_selection"
  | "consent_required"
  | "payment_processing"
  | "payment_succeeded"
  | "error";

// ── API response types (standalone — mirrors booking.types.ts) ────────────────

interface AvailabilityResponse {
  slots: SlotItem[];
}

interface CreateBookingResponse {
  booking_id: string;
  status: string;
  checkout_url: string | null;
  requires_consent: boolean;
  consent_template_markdown: string | null;
  amount: string;
  currency: string;
  is_deposit_only: boolean;
}

interface ConsentSignResponse {
  signed: boolean;
  booking_id: string;
}

// ── Config resolved from URL params ──────────────────────────────────────────

interface WidgetConfig {
  clinicSlug: string;
  offerId: string;
  doctorId: string | null;
  /** Pre-signed patient JWT from BE (HMAC-signed, short-lived) */
  patientToken: string | null;
  /** Parent origin from URL param for targeted postMessage */
  parentOrigin: string;
  /** Allowed origins list from data-allowed-origins attribute */
  allowedOrigins: readonly string[];
}

function resolveWidgetConfig(): WidgetConfig {
  const params = new URLSearchParams(window.location.search);

  // Also check embed mount div attributes (when initialized via widget-entry)
  const mountEl = document.getElementById("vitalia-booking-widget");

  const clinicSlug =
    params.get("clinic_slug") ??
    mountEl?.getAttribute("data-clinic-slug") ??
    "";

  const offerId =
    params.get("offer_id") ??
    mountEl?.getAttribute("data-offer-id") ??
    "";

  const doctorId =
    params.get("doctor_id") ??
    mountEl?.getAttribute("data-doctor-id") ??
    null;

  const patientToken =
    params.get("patient_token") ??
    null;

  const parentOrigin =
    params.get("parent_origin") ??
    document.referrer.split("/").slice(0, 3).join("/") ??
    "*";

  const rawAllowedOrigins =
    params.get("allowed_origins") ??
    mountEl?.getAttribute("data-allowed-origins") ??
    "*";

  const allowedOrigins: string[] =
    rawAllowedOrigins === "*" ? ["*"] : rawAllowedOrigins.split(",").map((s) => s.trim()).filter(Boolean);

  return { clinicSlug, offerId, doctorId, patientToken, parentOrigin, allowedOrigins };
}

// ── Booking API calls ─────────────────────────────────────────────────────────

const API_BASE = "/api/v1/vitalia";

async function fetchAvailableSlots(
  clinicSlug: string,
  offerId: string,
  doctorId: string | null,
  patientToken: string | null
): Promise<SlotItem[]> {
  const params = new URLSearchParams({ offer_id: offerId });
  if (doctorId) params.set("doctor_id", doctorId);

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (patientToken) headers["Authorization"] = `Bearer ${patientToken}`;

  const response = await fetch(
    `${API_BASE}/public/${clinicSlug}/availability?${params.toString()}`,
    { headers, signal: AbortSignal.timeout(10_000) }
  );

  if (!response.ok) throw new Error(`Availability fetch failed: ${response.status}`);
  const data = (await response.json()) as AvailabilityResponse;
  return data.slots;
}

async function createBooking(
  clinicSlug: string,
  offerId: string,
  selectedSlot: SlotItem,
  patientToken: string | null
): Promise<CreateBookingResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (patientToken) headers["Authorization"] = `Bearer ${patientToken}`;

  const body = JSON.stringify({
    offer_id: offerId,
    doctor_id: selectedSlot.doctor_id,
    slot_iso: selectedSlot.slot_iso,
  });

  const response = await fetch(`${API_BASE}/public/${clinicSlug}/bookings`, {
    method: "POST",
    headers,
    body,
    signal: AbortSignal.timeout(15_000),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => "");
    throw new Error(`Booking creation failed: ${response.status} ${errorText}`);
  }

  return (await response.json()) as CreateBookingResponse;
}

async function signConsent(
  clinicSlug: string,
  bookingId: string,
  signedName: string,
  patientToken: string | null
): Promise<ConsentSignResponse> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (patientToken) headers["Authorization"] = `Bearer ${patientToken}`;

  const body = JSON.stringify({
    signed_name: signedName,
    signature_method: "typed_name",
  });

  const response = await fetch(
    `${API_BASE}/public/${clinicSlug}/bookings/${bookingId}/consent`,
    {
      method: "POST",
      headers,
      body,
      signal: AbortSignal.timeout(10_000),
    }
  );

  if (!response.ok) throw new Error(`Consent sign failed: ${response.status}`);
  return (await response.json()) as ConsentSignResponse;
}

// ── Component ─────────────────────────────────────────────────────────────────

export interface BookingWidgetRootProps {
  /** Injected config (override for testing; uses URL params if omitted) */
  config?: Partial<WidgetConfig>;
}

export function BookingWidgetRoot({ config: configOverride }: BookingWidgetRootProps) {
  const config = { ...resolveWidgetConfig(), ...configOverride };
  const validateOrigin = createOriginValidator(config.allowedOrigins);

  const [step, setStep] = useState<BookingStep>("slot_selection");
  const [slots, setSlots] = useState<SlotItem[]>([]);
  const [selectedSlot, setSelectedSlot] = useState<SlotItem | null>(null);
  const [bookingResult, setBookingResult] = useState<CreateBookingResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Notify parent that widget is loaded
  useEffect(() => {
    postMessageToParent({ type: "widget:loaded" }, config.parentOrigin);
  }, [config.parentOrigin]);

  // Notify parent of height on render changes
  useEffect(() => {
    const height = document.documentElement.scrollHeight;
    postMessageToParent({ type: "widget:resize", height }, config.parentOrigin);
  });

  // Listen for incoming postMessages from parent (future: allow parent to pre-fill)
  useEffect(() => {
    function handleMessage(event: MessageEvent): void {
      if (!validateOrigin(event.origin)) return; // D11 origin spoofing prevention
      // Reserved for future parent→widget commands
    }

    window.addEventListener("message", handleMessage);
    return () => window.removeEventListener("message", handleMessage);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // Load available slots on mount
  useEffect(() => {
    if (!config.clinicSlug || !config.offerId) {
      setErrorMessage("Configuración del widget incompleta.");
      setStep("error");
      return;
    }

    let cancelled = false;
    setIsLoading(true);

    fetchAvailableSlots(config.clinicSlug, config.offerId, config.doctorId, config.patientToken)
      .then((fetchedSlots) => {
        if (cancelled) return;
        setSlots(fetchedSlots);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const message = err instanceof Error ? err.message : "Error al cargar horarios.";
        setErrorMessage(message);
        setStep("error");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [config.clinicSlug, config.offerId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSelectSlot = useCallback(
    async (slot: SlotItem) => {
      setSelectedSlot(slot);
      setIsLoading(true);
      setErrorMessage(null);

      try {
        const result = await createBooking(
          config.clinicSlug,
          config.offerId,
          slot,
          config.patientToken
        );
        setBookingResult(result);

        if (result.requires_consent) {
          setStep("consent_required");
        } else {
          setStep("payment_processing");
        }
      } catch (err: unknown) {
        const message =
          err instanceof Error ? err.message : "No se pudo reservar el horario.";

        // Check for race condition (slot taken)
        if (message.includes("409") || message.toLowerCase().includes("conflict")) {
          setErrorMessage("Este horario ya no está disponible. Elige otro.");
        } else {
          setErrorMessage(message);
        }
      } finally {
        setIsLoading(false);
      }
    },
    [config.clinicSlug, config.offerId, config.patientToken]
  );

  const handleSignConsent = useCallback(
    async (signedName: string) => {
      if (!bookingResult) return;
      setIsLoading(true);
      setErrorMessage(null);

      try {
        await signConsent(
          config.clinicSlug,
          bookingResult.booking_id,
          signedName,
          config.patientToken
        );
        setStep("payment_processing");
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Error al firmar el consentimiento.";
        setErrorMessage(message);
      } finally {
        setIsLoading(false);
      }
    },
    [bookingResult, config.clinicSlug, config.patientToken]
  );

  const handlePaymentRedirect = useCallback(
    (url: string) => {
      // Notify parent window to open checkout in new tab
      postMessageToParent({ type: "widget:payment-redirect", url }, config.parentOrigin);

      // Also open directly in case parent is the same origin
      window.open(url, "_blank", "noopener,noreferrer");
    },
    [config.parentOrigin]
  );

  const handleBookingConfirmed = useCallback(() => {
    if (!bookingResult) return;
    postMessageToParent(
      { type: "widget:booking-confirmed", booking_id: bookingResult.booking_id },
      config.parentOrigin
    );
    setStep("payment_succeeded");
  }, [bookingResult, config.parentOrigin]);

  // ── Render ────────────────────────────────────────────────────────────────

  if (step === "error") {
    return (
      <div
        className="flex flex-col items-center justify-center h-full px-6 py-8 text-center"
        role="alert"
      >
        <p className="text-sm text-red-600 font-medium mb-2">
          No se pudo cargar el widget de reserva.
        </p>
        {errorMessage && (
          <p className="text-xs text-gray-400">{errorMessage}</p>
        )}
      </div>
    );
  }

  if (step === "payment_succeeded" && bookingResult && selectedSlot) {
    return (
      <SuccessStep
        bookingId={bookingResult.booking_id}
        slotIso={selectedSlot.slot_iso}
        offerName={config.offerId}
        onClose={() => {
          postMessageToParent({ type: "widget:loaded" }, config.parentOrigin);
        }}
      />
    );
  }

  if (step === "payment_processing" && bookingResult && selectedSlot) {
    return (
      <PaymentStep
        amount={bookingResult.amount}
        currency={bookingResult.currency}
        offerName={config.offerId}
        slotIso={selectedSlot.slot_iso}
        isDepositOnly={bookingResult.is_deposit_only}
        checkoutUrl={bookingResult.checkout_url}
        onPaymentRedirect={handlePaymentRedirect}
        onBack={() => setStep("slot_selection")}
        isLoading={isLoading}
        errorMessage={errorMessage}
      />
    );
  }

  if (step === "consent_required" && bookingResult) {
    return (
      <ConsentStep
        consentMarkdown={bookingResult.consent_template_markdown ?? ""}
        onSign={handleSignConsent}
        onBack={() => setStep("slot_selection")}
        isLoading={isLoading}
      />
    );
  }

  // Default: slot_selection step
  return (
    <CalendarSlotPicker
      slots={slots}
      selectedSlot={selectedSlot}
      onSelectSlot={handleSelectSlot}
      isLoading={isLoading}
      errorMessage={errorMessage}
    />
  );
}
