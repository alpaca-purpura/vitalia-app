# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Frozen leads DTOs — Recuperar sub-tab (congelados + decidio_no + diagnose).

API layer Pydantic v2 models.
Frozen leads = leads with is_frozen=True OR stage='decidio_no'.
Diagnose: deterministic recommendation for reactivation.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class FrozenLeadDTO(BaseModel):
    """Frozen lead card for the Recuperar sub-tab list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str  # masked at FE via PiiMaskedSpan
    channel: str | None
    stage: str
    frozen_reason: str | None
    frozen_at: datetime | None
    diagnosis: str | None = None  # pre-computed if diagnose was called
    closure_reason: str | None = None  # for decidio_no


class FrozenListResponse(BaseModel):
    """Response for GET /crm/frozen — two lists: recently frozen + decidio_no."""

    model_config = ConfigDict(from_attributes=True)

    recien_congelados: list[FrozenLeadDTO]  # is_frozen=True, not decidio_no
    decidio_no: list[FrozenLeadDTO]  # stage=decidio_no


class DiagnoseResponse(BaseModel):
    """Response for POST /crm/leads/{id}/diagnose.

    Deterministic recommendation based on frozen_reason + stage + signals.
    """

    model_config = ConfigDict(from_attributes=True)

    recommendation_es: str  # Spanish neutro LatAm (sin voseo), 1-2 sentences
    suggested_action: str  # reactivate | schedule_call | send_discount | wait


class ReactivateRequest(BaseModel):
    """Request body for POST /crm/leads/{id}/reactivate."""

    model_config = ConfigDict(from_attributes=True)

    objective: str | None = Field(
        None,
        max_length=500,
        description="Context for reactivation (e.g. new promotion, new service). NON-PHI.",
    )
