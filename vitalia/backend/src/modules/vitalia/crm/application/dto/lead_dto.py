# cap: crm.crm-consent-optout
# story-origin: TBD
"""Lead DTOs — non-PHI, all authenticated roles can read.

Extended by T-inbox-be-5: LeadListResponse, LeadCreateRequest, LeadUpdateRequest.
Extended by T-BE-2 (vitalia-fase2-adrian-embudo): funnel fields on LeadResponse + LeadCreateRequest.

Note: cap header stays crm-consent-optout (original cap for inbox); funnel extends this DTO.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class LeadResponse(BaseModel):
    """Lead response model — non-PHI fields only.

    Funnel fields added in T-BE-2 (vitalia-fase2-adrian-embudo):
    stage, score, temperature, operated_by, channel, estimated_value, currency,
    service_interest, buying_signals, stage_entered_at, is_frozen, frozen_reason,
    deposit_status, version.

    currency: NEVER hardcoded — from data source (RN-15). None = tenant locale at FE.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    name: str
    email: str | None = None
    phone: str | None = None
    source: str | None = None
    status: str
    created_at: datetime

    # Funnel fields (T-BE-2 extension)
    stage: str = "interesado"
    score: int = 0
    temperature: str = "cold"
    operated_by: str = "agent"
    channel: str | None = None
    estimated_value: Decimal | None = None
    currency: str | None = None  # tenant locale — NEVER hardcoded 'USD' or 'MXN'
    service_interest: str | None = None
    assigned_doctor_id: UUID | None = None  # U2: detail shows assigned doctor (FE Resumen Doctor row)
    buying_signals: list[str] = Field(default_factory=list)
    stage_entered_at: datetime | None = None
    is_frozen: bool = False
    frozen_reason: str | None = None
    deposit_status: str | None = None
    version: int = 1


class LeadListResponse(BaseModel):
    """Paginated list of leads — non-PHI."""

    model_config = ConfigDict(from_attributes=True)

    items: list[LeadResponse]
    total: int
    limit: int
    offset: int


class LeadCreateRequest(BaseModel):
    """Request body for POST /crm/leads.

    Extended in T-BE-2: stage, channel, service_interest, tags, estimated_value, currency.
    """

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(max_length=200)
    email: str | None = Field(None, max_length=254)
    phone: str | None = Field(None, max_length=32)
    source: str | None = Field(None, max_length=64)
    status: str = Field(default="new", max_length=32)
    notes: str | None = Field(None, max_length=2000)
    marketing_opt_in: bool = False

    # Funnel fields (T-BE-2 extension)
    stage: str = Field(default="interesado", max_length=64)
    channel: str | None = Field(None, max_length=32)
    service_interest: str | None = Field(None, max_length=200)
    tags: list[str] = Field(default_factory=list)
    estimated_value: Decimal | None = None
    currency: str | None = Field(None, max_length=8)


class LeadUpdateRequest(BaseModel):
    """Request body for PATCH /crm/leads/{lead_id} — all fields optional."""

    model_config = ConfigDict(from_attributes=True)

    name: str | None = Field(None, max_length=200)
    email: str | None = Field(None, max_length=254)
    phone: str | None = Field(None, max_length=32)
    source: str | None = Field(None, max_length=64)
    status: str | None = Field(None, max_length=32)
    notes: str | None = Field(None, max_length=2000)
    marketing_opt_in: bool | None = None
