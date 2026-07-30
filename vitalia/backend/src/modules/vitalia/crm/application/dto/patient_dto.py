# cap: crm.crm-consent-optout
# story-origin: TBD
"""Patient DTOs — PII allowlist enforced via response_model= on all routes.

Only fields listed in PatientResponse are returned to clients.
PHI fields (diagnosis, treatment_plan, etc.) are excluded unless explicitly
added in a future PHI-gated DTO variant with stricter auth.

T-BE-5: added PatientInlineCreateRequest/Response, PatientSearchItem, PatientSearchResponse
for inline patient create + typeahead search. ALL responses use masked fields only
(name_masked, phone_masked) — raw PHI NEVER returned via these DTOs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PatientResponse(BaseModel):
    """Patient response — PII allowlisted fields only.

    PHI fields beyond these are NOT exposed via this DTO.
    Richer clinical data requires a separate MedicalRecordResponse
    under PHI-gated endpoints.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    name: str
    email: str | None = None
    phone: str | None = None
    marketing_opt_out_at: datetime | None = None
    created_at: datetime


class PatientPatchRequest(BaseModel):
    """Request model for PATCH /patients/{id}."""

    model_config = ConfigDict(from_attributes=True)

    phone: str | None = None
    email: str | None = None
    address: str | None = None


class OptOutRequest(BaseModel):
    """Request model for POST /patients/{id}/opt-out."""

    model_config = ConfigDict(from_attributes=True)

    reason: str


class OptOutResponse(BaseModel):
    """Response model for POST /patients/{id}/opt-out."""

    model_config = ConfigDict(from_attributes=True)

    patient_id: UUID
    opted_out: bool
    message: str


# ---------------------------------------------------------------------------
# T-BE-5: Inline patient create + typeahead search DTOs
# All use MASKED fields only — raw PHI (name, phone, email) NEVER returned.
# ---------------------------------------------------------------------------

_CHANNEL_LITERAL = Literal["whatsapp", "instagram", "web", "phone", "walk_in", "other"]


class PatientInlineCreateRequest(BaseModel):
    """Request model for POST /api/v1/crm/patients (inline minimal create).

    PHI fields (name, phone, email) transmitted in POST body — NEVER in URL params.
    Dual filter (tenant_id + clinic_id) applied by the service layer via headers.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., min_length=1, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=254)
    channel: _CHANNEL_LITERAL
    note: str | None = Field(default=None, max_length=500)


class PatientInlineCreateResponse(BaseModel):
    """Response for POST /api/v1/crm/patients — MASKED fields only.

    HIPAA-lite: raw name/phone/email NEVER returned. Use masked variants.
    is_duplicate=True signals RN-9 dedup (phone already exists → offer "use existing?").
    """

    model_config = ConfigDict(from_attributes=True)

    patient_id: UUID
    name_masked: str  # e.g. "M. López" — first initial + last name
    phone_masked: str | None = None  # e.g. "+51 9***" or None
    is_duplicate: bool = False
    created_at: datetime


class PatientSearchItem(BaseModel):
    """Single masked patient result for typeahead search.

    HIPAA-lite: raw PHI (name, phone, email) NEVER included.
    """

    model_config = ConfigDict(from_attributes=True)

    patient_id: UUID
    name_masked: str
    phone_masked: str | None = None
    channel_first: str | None = None
    created_at: datetime


class PatientSearchResponse(BaseModel):
    """Paginated response for GET /api/v1/crm/patients?q= typeahead search.

    Cursor-based pagination for 1500+ row datasets.
    next_cursor: UUID str of the last item — pass as ?cursor= for next page.
    total_approx: approximate count (window function — may be slightly off).
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[PatientSearchItem]
    next_cursor: UUID | None = None
    total_approx: int = 0
