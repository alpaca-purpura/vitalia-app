# cap: agentic.lucas-recommendation-tool
# story-origin: TBD
"""Lucas application DTOs — Pydantic v2 response models.

Used by internal route and for serialization.
response_model= MANDATORY on all routes that use these DTOs (arch fitness).
ConfigDict(from_attributes=True) enables ORM → DTO mapping.

No PHI fields in any DTO — analytics/recommendations data only.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StageRecommendationDTO(BaseModel):
    """DTO for StageRecommendation entity response."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    stage: str
    recommendation_kind: str
    title: str
    body: str
    priority: int
    status: str
    expires_at: dt.datetime
    created_at: dt.datetime
    updated_at: dt.datetime


class AttributionMatrixSnapshotDTO(BaseModel):
    """DTO for AttributionMatrixSnapshot entity response."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    period_start: dt.date
    period_end: dt.date
    channel_breakdown: dict[str, Any]
    total_attributed_revenue: Decimal
    currency: str | None  # ISO-4217; None until locale resolved
    computed_at: dt.datetime


class ReferralsLeaderboardSnapshotDTO(BaseModel):
    """DTO for ReferralsLeaderboardSnapshot entity response."""

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    period_start: dt.date
    period_end: dt.date
    top_referrers: list[dict[str, Any]]
    total_referrals: int
    total_converted: int
    computed_at: dt.datetime
