# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Transition DTOs — stage change request/response + timeline shapes.

API layer Pydantic v2 models.
reason: commercial context for RN-4.1 override wire (NON-PHI).
Timeline: commercial micro-log entries — NEVER clinical data (RN-2 firewall).
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.modules.vitalia.crm.application.dto.lead_dto import LeadResponse


class StageTransitionRequest(BaseModel):
    """Request body for PATCH /crm/leads/{id}/stage."""

    model_config = ConfigDict(from_attributes=True)

    to_stage: str = Field(description="Target funnel stage slug.")
    reason: str | None = Field(
        None,
        max_length=500,
        description="Commercial override context (NON-PHI). Required for backward/jump transitions.",
    )
    note: str | None = Field(None, max_length=500, description="Optional additional note.")
    version: int = Field(description="Current lead version for optimistic lock (SC-5).")
    triggered_by: str = Field(
        default="manual_override",
        description="Trigger actor slug (manual_override | webhook | reactivation | auto_freeze).",
    )


class TransitionDTO(BaseModel):
    """Transition record returned in response."""

    model_config = ConfigDict(from_attributes=True)

    from_stage: str | None
    to_stage: str
    triggered_by: str
    reason: str | None
    occurred_at: datetime


class StageTransitionResponse(BaseModel):
    """Response for successful stage transition."""

    model_config = ConfigDict(from_attributes=True)

    lead: LeadResponse
    transition: TransitionDTO


class TimelineEntry(BaseModel):
    """Single entry in the commercial activity timeline (Historial tab).

    description_es: Spanish neutro, 3rd person, NON-PHI. NEVER clinical data.
    RN-2: clinical data stays in PHI-gated Inbox module.
    """

    model_config = ConfigDict(from_attributes=True)

    actor: str  # agent | human | lead | system
    kind: str  # message | stage_move | info_sent | deposit | note
    description_es: str
    occurred_at: datetime
    signal: str | None = None  # associated buying_signal if applicable


class TimelineResponse(BaseModel):
    """Response for GET /crm/leads/{id}/transitions (timeline/historial)."""

    model_config = ConfigDict(from_attributes=True)

    events: list[TimelineEntry]
