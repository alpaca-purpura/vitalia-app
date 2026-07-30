# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""RetractMessage DTOs — vitalia inbox application layer.

downstream-regression-na: brand-local vitalia inbox DTO
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class RetractMessageRequest(BaseModel):
    """Request body for POST /inbox/conversations/{conv_id}/messages/{msg_id}/revert."""

    model_config = ConfigDict(from_attributes=True)

    reason: str | None = None


class RetractMessageResponse(BaseModel):
    """Response after retract attempt."""

    model_config = ConfigDict(from_attributes=True)

    message_id: UUID
    retracted_at: datetime | None = None
    retract_succeeded: bool
    fallback_applied: bool = False
    retract_reason: str | None = None
