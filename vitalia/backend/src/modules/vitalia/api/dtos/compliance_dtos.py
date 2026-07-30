# cap: compliance.compliance-hipaa-lite-audit
# story-origin: TBD
"""Compliance DTOs — Pydantic v2 request/response models.

Per 03-arch-be.md § 6.7 + § 7.1 + Tessl pii-sanitisation:
  - payload_redacted: JSONB field — already sanitized at write time (ComplianceEventService).
  - actor_id exposed as UUID only (no actor PII name/email).
  - Export endpoint returns text/csv — not typed here (StreamingResponse).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ComplianceEventItem(BaseModel):
    """Single compliance/audit event — PII-sanitized payload only.

    payload_redacted is pre-sanitized by ComplianceEventService before DB write.
    No raw PII in this DTO.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    severity: str  # "info" | "medium" | "high"
    patient_id: UUID | None = None
    booking_id: UUID | None = None
    payload_redacted: dict = Field(default_factory=dict)
    actor_id: UUID | None = None
    actor_type: str | None = None  # "clinic_owner" | "sales_agent" | "system" | "patient"
    created_at: datetime


class ComplianceEventListResponse(BaseModel):
    """Response for GET /medical-compliance/events."""

    model_config = ConfigDict(from_attributes=True)

    events: list[ComplianceEventItem]
    total: int
    page: int
    page_size: int
