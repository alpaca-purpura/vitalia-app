# cap: agentic.lucas-recommendation-tool
# story-origin: TBD
"""Lucas domain entity — StageRecommendation.

Pure Python domain entity. No SQLAlchemy, no FastAPI imports.

Maps conceptually to LucasStageRecommendationModel (persistence/models/stage_recommendation.py)
but domain owns the invariants. Repository translates to/from ORM model.

HIPAA-lite: no PHI fields. This entity holds analytics recommendations only.
Dual filter: every repository query uses BOTH tenant_id + clinic_id.
Soft-delete: deleted_at is set on removal — never hard delete.

Status lifecycle: 'open' → 'approved' | 'rejected' | 'expired' | 'undone' | 'skipped_budget'.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class StageRecommendation:
    """Domain entity for a Lucas stage-based recommendation.

    Carries both tenant_id and clinic_id for HIPAA-lite dual filter compliance
    (vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo).

    No PHI fields — this entity holds analytics-derived recommendations only.
    """

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    stage: str
    recommendation_kind: str
    title: str
    body: str
    rationale_json: dict[str, Any]
    priority: int
    status: str
    expires_at: dt.datetime
    created_at: dt.datetime
    updated_at: dt.datetime
    deleted_at: dt.datetime | None
    approved_by_user_id: UUID | None
    approved_at: dt.datetime | None
    undo_until: dt.datetime | None
