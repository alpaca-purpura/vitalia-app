# cap: copilot.valeria-wizard-onboarding-agentic
# story-origin: TBD
"""DTOs for Valeria wizard onboarding API endpoints.

Pydantic v2 models with ConfigDict(from_attributes=True).
All monetary fields include currency (none here — wizard config only).
Spanish neutro LatAm on user-facing strings (hipaa-lite.md: no PHI in DTOs).

PII allowlist (per tessl pii-sanitisation rule):
- None — wizard config only (clinic name, vertical, location, tone)
- No patient identifiers, diagnoses, or medical data
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Slot DTOs
# ---------------------------------------------------------------------------


class WizardSlotDTO(BaseModel):
    """Serialization of a WizardSlot value object.

    Maps domain entity WizardSlot → API response (read-only).
    """

    model_config = ConfigDict(from_attributes=True)

    slot_id: str
    value: Optional[Any] = None
    confidence: float = Field(ge=0.0, le=1.0)
    confirmed_at: Optional[datetime] = None
    source: str


# ---------------------------------------------------------------------------
# Create/start draft request+response
# ---------------------------------------------------------------------------


class StartDraftRequest(BaseModel):
    """Request body for POST /onboarding/drafts (start a new wizard session)."""

    model_config = ConfigDict(extra="forbid")

    mode: str = Field(default="libre", pattern="^(libre|guiado)$")
    clinic_id: Optional[UUID] = None


class StartDraftResponse(BaseModel):
    """Response for a newly created OnboardingDraft."""

    model_config = ConfigDict(from_attributes=True)

    draft_id: UUID
    tenant_id: UUID
    mode: str
    slots_required: dict[str, WizardSlotDTO]
    slots_optional: dict[str, WizardSlotDTO]
    created_at: datetime


# ---------------------------------------------------------------------------
# Extract tenant context
# ---------------------------------------------------------------------------


class ExtractRequest(BaseModel):
    """Request body for POST /onboarding/drafts/{draft_id}/extract."""

    model_config = ConfigDict(extra="forbid")

    url: Optional[str] = Field(default=None, description="URL del sitio de la clínica")
    text_content: Optional[str] = Field(default=None, description="Contenido de documento o texto libre")


class ExtractResponse(BaseModel):
    """Response after extracting tenant context into wizard slots."""

    model_config = ConfigDict(from_attributes=True)

    draft_id: UUID
    slots_required: dict[str, WizardSlotDTO]
    slots_optional: dict[str, WizardSlotDTO]
    slots_updated: int


# ---------------------------------------------------------------------------
# Confirm slot
# ---------------------------------------------------------------------------


class ConfirmSlotRequest(BaseModel):
    """Request body for POST /onboarding/drafts/{draft_id}/slots/{slot_id}/confirm."""

    model_config = ConfigDict(extra="forbid")

    value: Any = Field(description="Valor confirmado para el slot")
    source: str = Field(
        default="user_text",
        pattern="^(extracted|user_text|user_correction)$",
    )


class ConfirmSlotResponse(BaseModel):
    """Response after confirming a wizard slot."""

    model_config = ConfigDict(from_attributes=True)

    draft_id: UUID
    slot_id: str
    confirmed_at: datetime
    value: Any
    all_required_confirmed: bool


# ---------------------------------------------------------------------------
# Simulate personality
# ---------------------------------------------------------------------------


class SimulateRequest(BaseModel):
    """Request body for POST /onboarding/drafts/{draft_id}/simulate."""

    model_config = ConfigDict(extra="forbid")

    scenario: str = Field(
        default="primera_respuesta",
        description="Escenario de simulación de personalidad",
    )


class SimulateResponse(BaseModel):
    """Response from personality simulation."""

    model_config = ConfigDict(from_attributes=True)

    sample_text: str
    scenario: str
    generated_at: str
    cache_hit: bool


# ---------------------------------------------------------------------------
# Complete onboarding
# ---------------------------------------------------------------------------


class CompleteRequest(BaseModel):
    """Request body for POST /onboarding/drafts/{draft_id}/complete."""

    model_config = ConfigDict(extra="forbid")


class CompleteResponse(BaseModel):
    """Response after completing the onboarding wizard."""

    model_config = ConfigDict(from_attributes=True)

    tenant_activated: bool
    redirect_url: str


# ---------------------------------------------------------------------------
# Get draft (read)
# ---------------------------------------------------------------------------


class DraftResponse(BaseModel):
    """Full OnboardingDraft response for GET /onboarding/drafts/{draft_id}."""

    model_config = ConfigDict(from_attributes=True)

    draft_id: UUID
    tenant_id: UUID
    user_id: UUID
    clinic_id: Optional[UUID] = None
    mode: str
    slots_required: dict[str, WizardSlotDTO]
    slots_optional: dict[str, WizardSlotDTO]
    consent_voice_activation: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
