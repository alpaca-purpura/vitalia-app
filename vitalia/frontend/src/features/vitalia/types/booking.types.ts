// cap: shell-organism.shell-vitalia
// story-origin: TBD
/**
 * Booking types — mirrors Pydantic booking_dtos.py Response DTOs.
 * snake_case preserved to match BE JSON field names.
 * ISO 8601 datetimes typed as string.
 * Decimal fields serialized as string from BE.
 */

export type BookingStatus =
  | "pending_payment"
  | "awaiting_consent"
  | "confirmed_deposit"
  | "confirmed_full"
  | "cancelled"
  | "completed";

export type PaymentStatus =
  | "pending"
  | "paid_deposit"
  | "paid_full"
  | "refunded"
  | "failed";

export type DeliveryChannel = "whatsapp" | "email" | "both";

// ── Request types ─────────────────────────────────────────────────────────────

export interface CreateBookingRequest {
  offer_id: string;
  doctor_id: string;
  patient_id: string;
  slot_iso: string;
  delivery_channel: DeliveryChannel;
  consent_template_slug?: string | null;
  requires_informed_consent?: boolean;
  requires_prepay?: boolean;
  deposit_only?: boolean;
}

export interface RescheduleBookingRequest {
  new_slot_iso: string;
  reason?: string | null;
}

export interface CancelBookingRequest {
  reason?: string | null;
}

export interface ConsentSignRequest {
  signed_name: string;
  signature_method: "typed_name" | "signature_pad";
  consent_token: string;
}

// ── Response types ────────────────────────────────────────────────────────────

export interface SlotItem {
  slot_iso: string;
  duration_minutes: number;
  doctor_id: string;
}

export interface CreateBookingResponse {
  booking_id: string;
  status: string;
  is_idempotent_hit: boolean;
  payment_url: string | null;
  consent_url: string | null;
  expires_at: string | null;
  currency: string | null;
}

export interface BookingSummary {
  id: string;
  offer_id: string;
  doctor_id: string;
  patient_id: string;
  slot_iso: string;
  duration_minutes: number;
  status: string;
  payment_status: string;
  currency: string | null;
  created_at: string;
}

export interface BookingListResponse {
  bookings: BookingSummary[];
  total: number;
}

export interface RescheduleBookingResponse {
  booking_id: string;
  old_slot_iso: string;
  new_slot_iso: string;
  status: string;
}

export interface CancelBookingResponse {
  booking_id: string;
  status: string;
  cancelled_at: string;
}

export interface ConsentSignResponse {
  consent_record_id: string;
  status: string;
  signed_at: string;
}

export interface AvailableSlotsResponse {
  slots: SlotItem[];
  doctor_id: string;
  offer_id: string;
  window_start: string;
  window_days: number;
}
