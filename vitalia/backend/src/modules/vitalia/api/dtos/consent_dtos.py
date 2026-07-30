# cap: crm.crm-consent-optout
# story-origin: TBD
"""Consent DTOs — Pydantic v2 request/response models.

Per 03-arch-be.md § 7.2 + Tessl pii-sanitisation:
  - signed_ip, signed_user_agent, template_snapshot_md NOT in response (internal only).
  - signed_name NOT exposed post-signing (legal record stored, not surfaced in API).
  - consent_url: short-lived signed URL (expires 24h).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Request DTOs ──────────────────────────────────────────────────────────────


class RequestConsentRequest(BaseModel):
    """POST /bookings/{id}/consent-sign (initial request phase)."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    patient_id: UUID
    consent_template_slug: str = Field(min_length=1, max_length=64)
    delivery_channels: list[str] = Field(
        default_factory=lambda: ["whatsapp", "email"],
        description="Delivery channels: whatsapp | email",
    )
    expiry_hours: int = Field(default=24, ge=1, le=720)


# ── Response DTOs ─────────────────────────────────────────────────────────────


class ConsentRecordResponse(BaseModel):
    """Single consent record (audit-safe — no raw PII).

    PII allowlist: signed_ip / signed_user_agent / signed_name NOT returned.
    consent_url NOT returned post-signing (one-time use).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    patient_id: UUID
    booking_id: UUID | None = None
    consent_template_slug: str
    template_version: str
    status: str
    expires_at: datetime
    signed_at: datetime | None = None
    signature_method: str | None = None
    delivery_channels: list[str]
    created_at: datetime


class ConsentRecordListResponse(BaseModel):
    """Response for GET /compliance/consent-records."""

    model_config = ConfigDict(from_attributes=True)

    records: list[ConsentRecordResponse]
    total: int
