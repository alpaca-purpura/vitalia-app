# cap: treatments.treatment-followup-workflow
# story-origin: TBD
"""Treatment DTOs — Pydantic v2 request/response models.

Per 03-arch-be.md § 6.5 + § 7.1 + Tessl pii-sanitisation:
  - Patient PII masked in treatment responses (patient_id UUID only).
  - langgraph_checkpoint_id is internal state — NOT returned in list responses.
  - Medical history summary text is clinically relevant — kept verbatim per 05-guidelines § 1.6.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ── Request DTOs ──────────────────────────────────────────────────────────────


class ManualHandoffRequest(BaseModel):
    """POST /treatments/{id}/manual-handoff — clinic owner takes conversation."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    reason: str | None = Field(default=None, max_length=500)


class StartFollowupRequest(BaseModel):
    """POST /treatments/{id}/start-followup — trigger LangGraph workflow."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    plan_template_slug: str = Field(
        min_length=1,
        max_length=64,
        description="Treatment plan slug (e.g. 'dental_implant', 'psychology_individual')",
    )
    procedure_date: datetime = Field(description="Procedure date (UTC) for D+5/14/90 tick offsets")


# ── Response DTOs ─────────────────────────────────────────────────────────────


class TreatmentSummary(BaseModel):
    """Treatment summary item for list response.

    PII allowlist: patient_id UUID only (no name/phone/email).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    patient_id: UUID
    doctor_id: UUID
    plan_template_slug: str
    current_step: str
    started_at: datetime
    last_response_at: datetime | None = None
    next_scheduled_at: datetime | None = None
    adherence_score: int | None = None


class TreatmentListResponse(BaseModel):
    """Response for GET /treatments."""

    model_config = ConfigDict(from_attributes=True)

    treatments: list[TreatmentSummary]
    total: int


class TreatmentDetailResponse(BaseModel):
    """Response for GET /treatments/{id}.

    Includes latest conversation summary (medical text — clinically relevant, kept verbatim).
    langgraph_checkpoint_id NOT returned (internal state).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    patient_id: UUID
    doctor_id: UUID
    plan_template_slug: str
    current_step: str
    started_at: datetime
    last_response_at: datetime | None = None
    next_scheduled_at: datetime | None = None
    adherence_score: int | None = None
    paused_reason: str | None = None
    created_at: datetime
    updated_at: datetime


class TreatmentFollowupStateResponse(BaseModel):
    """Response for GET /treatments/{id}/followup — workflow state."""

    model_config = ConfigDict(from_attributes=True)

    treatment_id: UUID
    current_step: str
    adherence_score: int | None = None
    last_response_at: datetime | None = None
    next_scheduled_at: datetime | None = None
    paused_reason: str | None = None


class ManualHandoffResponse(BaseModel):
    """Response for POST /treatments/{id}/manual-handoff."""

    model_config = ConfigDict(from_attributes=True)

    treatment_id: UUID
    status: str
    handoff_at: datetime


class ReleaseHandoffResponse(BaseModel):
    """Response for POST /treatments/{id}/release-handoff."""

    model_config = ConfigDict(from_attributes=True)

    treatment_id: UUID
    status: str
    released_at: datetime


# ── Patient DTOs ──────────────────────────────────────────────────────────────


class PatientSummary(BaseModel):
    """Patient list item — PII masked per 03-arch-be.md § 7.2.

    name_last_initial: last name 1 char only ("G.") per HIPAA-lite.
    phone_masked: "+54***5555". email_masked: "j***@***.com".
    Full name/phone/email NOT returned in any response.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name_first: str
    name_last_initial: str = Field(description="Last name initial only: 'G.' per HIPAA-lite mask")
    phone_masked: str = Field(description="+54***5555")
    email_masked: str = Field(description="j***@***.com")
    clinic_type: str | None = None
    created_at: datetime


class PatientListResponse(BaseModel):
    """Response for GET /patients."""

    model_config = ConfigDict(from_attributes=True)

    patients: list[PatientSummary]
    total: int


class PatientDetailResponse(BaseModel):
    """Response for GET /patients/{id}.

    Includes medical_history_summary (clinically relevant text — kept verbatim).
    Raw full_last_name / phone / email NOT exposed.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name_first: str
    name_last_initial: str = Field(description="Last name initial only: 'G.'")
    phone_masked: str
    email_masked: str
    medical_history_summary: str | None = None
    clinic_type: str | None = None
    created_at: datetime
    updated_at: datetime


class UploadMedicalPdfRequest(BaseModel):
    """POST /patients/{id}/upload-medical-pdf — triggers MedicalKBExtractor async."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    file_name: str = Field(min_length=1, max_length=255)
    content_type: str = Field(
        pattern=r"^application/pdf$",
        description="Must be application/pdf",
    )
    base64_content: str = Field(description="Base64-encoded PDF content")


class UploadMedicalPdfResponse(BaseModel):
    """Response for POST /patients/{id}/upload-medical-pdf."""

    model_config = ConfigDict(from_attributes=True)

    patient_id: UUID
    extraction_job_id: str
    status: str
    estimated_completion_seconds: int
