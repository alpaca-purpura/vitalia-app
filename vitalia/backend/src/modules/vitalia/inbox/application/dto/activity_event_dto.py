# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""ActivityEvent DTOs — vitalia inbox application layer.

downstream-regression-na: brand-local vitalia inbox DTO
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ActivityEventItem(BaseModel):
    """Single activity event in the activity stream."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_kind: str
    description_es: str
    agent_id: str
    occurred_at: datetime
    # payload_sanitized intentionally excluded from response (internal debug only)


class ActivityStreamResponse(BaseModel):
    """Response for GET /inbox/conversations/{conv_id}/activity-stream."""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID
    events: list[ActivityEventItem]
    limit: int
    since_minutes: int
