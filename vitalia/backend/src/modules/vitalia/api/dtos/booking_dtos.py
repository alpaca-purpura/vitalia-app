# cap: booking.booking-widget-embed
# story-origin: TBD
"""Booking DTOs — Pydantic v2 request/response models.

Per 03-arch-be.md § 6.4 + § 7.1 + Tessl pii-sanitisation:
  - Patient PII NOT exposed in booking responses (patient_id UUID only).
  - payment_url / consent_url are short-lived signed URLs.
  - currency: str | None = None (from offer/booking, NEVER hardcoded).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Request DTOs ──────────────────────────────────────────────────────────────


class CreateBookingRequest(BaseModel):
    """POST /bookings — create booking with advisory lock + idempotency.

    Creates booking in status pending_payment | awaiting_consent | confirmed_deposit
    based on offer flags. Advisory lock on (doctor_id, slot_iso) prevents double-booking.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    offer_id: UUID
    doctor_id: UUID
    patient_id: UUID
    slot_iso: datetime = Field(description="Desired appointment slot (UTC ISO-8601)")
    delivery_channel: str = Field(
        pattern=r"^(whatsapp|email|both)$",
        description="Channel for consent/confirmation delivery",
    )
    consent_template_slug: str | None = None
    requires_informed_consent: bool = False
    requires_prepay: bool = True
    deposit_only: bool = True


class RescheduleBookingRequest(BaseModel):
    """POST /bookings/{id}/reschedule — release old slot + reserve new slot."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    new_slot_iso: datetime = Field(description="New slot (UTC ISO-8601)")
    reason: str | None = Field(default=None, max_length=500)


class CancelBookingRequest(BaseModel):
    """POST /bookings/{id}/cancel — soft-cancel booking."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    reason: str | None = Field(default=None, max_length=500)


class ConfirmPaymentRequest(BaseModel):
    """POST /bookings/{id}/confirm-payment — webhook-driven payment confirmation."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    gateway_payment_id: str
    gateway: str = Field(pattern=r"^(mercadopago|stripe_connect|tokenized_recurring)$")
    amount: Decimal
    currency: str = Field(min_length=3, max_length=3, description="ISO 4217")
    status: str = Field(pattern=r"^(succeeded|failed)$")


class ConsentSignRequest(BaseModel):
    """POST /bookings/{id}/consent-sign — capture patient signature."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    signed_name: str = Field(min_length=2, max_length=255)
    signature_method: str = Field(pattern=r"^(typed_name|signature_pad)$")
    consent_token: str = Field(description="HMAC-signed token from consent URL")


# ── Slot (value object in response) ──────────────────────────────────────────


class SlotItem(BaseModel):
    """Available slot in availability response."""

    model_config = ConfigDict(from_attributes=True)

    slot_iso: datetime
    duration_minutes: int
    doctor_id: UUID


# ── Response DTOs ─────────────────────────────────────────────────────────────


class CreateBookingResponse(BaseModel):
    """Response for POST /bookings.

    PII allowlist: patient_id UUID only (no name/phone/email in response).
    """

    model_config = ConfigDict(from_attributes=True)

    booking_id: UUID
    status: str
    is_idempotent_hit: bool
    payment_url: str | None = None
    consent_url: str | None = None
    expires_at: datetime | None = None
    currency: str | None = None  # ISO 4217 — from offer, NEVER hardcoded


class BookingSummary(BaseModel):
    """Booking summary item for list response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    doctor_id: UUID
    patient_id: UUID
    slot_iso: datetime
    duration_minutes: int
    status: str
    payment_status: str
    currency: str | None = None
    created_at: datetime


class BookingListResponse(BaseModel):
    """Response for GET /bookings (list)."""

    model_config = ConfigDict(from_attributes=True)

    bookings: list[BookingSummary]
    total: int


class RescheduleBookingResponse(BaseModel):
    """Response for POST /bookings/{id}/reschedule."""

    model_config = ConfigDict(from_attributes=True)

    booking_id: UUID
    old_slot_iso: datetime
    new_slot_iso: datetime
    status: str


class CancelBookingResponse(BaseModel):
    """Response for POST /bookings/{id}/cancel."""

    model_config = ConfigDict(from_attributes=True)

    booking_id: UUID
    status: str
    cancelled_at: datetime


class ConfirmPaymentResponse(BaseModel):
    """Response for POST /bookings/{id}/confirm-payment."""

    model_config = ConfigDict(from_attributes=True)

    booking_id: UUID
    payment_status: str
    booking_status: str
    currency: str | None = None


class ConsentSignResponse(BaseModel):
    """Response for POST /bookings/{id}/consent-sign."""

    model_config = ConfigDict(from_attributes=True)

    consent_record_id: UUID
    status: str
    signed_at: datetime


class AvailableSlotsResponse(BaseModel):
    """Response for GET /bookings/available-slots."""

    model_config = ConfigDict(from_attributes=True)

    slots: list[SlotItem]
    doctor_id: UUID
    offer_id: UUID
    window_start: datetime
    window_days: int
