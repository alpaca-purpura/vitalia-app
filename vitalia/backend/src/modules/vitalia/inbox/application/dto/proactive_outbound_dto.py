# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""ProactiveOutbound DTOs — vitalia inbox application layer.

downstream-regression-na: brand-local vitalia inbox DTO
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProactiveOutboundRequest(BaseModel):
    """Request body for POST /inbox/proactive-outbound."""

    model_config = ConfigDict(from_attributes=True)

    lead_id: UUID
    template_id: str = Field(max_length=64)
    variables: dict[str, str] = Field(default_factory=dict)
    channel: str = Field(default="whatsapp", max_length=32)


class ProactiveOutboundResponse(BaseModel):
    """Response after proactive outbound send."""

    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID
    message_id: UUID
    template_id: str
    channel: str
    sent_at: datetime
    compliance_checked: bool = True
