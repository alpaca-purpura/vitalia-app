# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""SetMode DTOs — vitalia inbox application layer.

downstream-regression-na: brand-local vitalia inbox DTO
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SetModeRequest(BaseModel):
    """Request body for POST /inbox/conversations/{conv_id}/mode."""

    model_config = ConfigDict(from_attributes=True)

    mode: Literal["ai", "human"]
    proposal_required: bool = False
    expected_updated_at: datetime  # OCC If-Match equivalent


class ConversationResponse(BaseModel):
    """Slim conversation response for mode/pause mutations."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    handler_mode: Literal["ai", "human"]
    proposal_required: bool
    status: str
    pause_until: datetime | None = None
    help_needed: bool
    updated_at: datetime
