# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""ConversationList DTOs — vitalia inbox application layer.

downstream-regression-na: brand-local vitalia inbox DTO
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationListFilters(BaseModel):
    """Query filters for conversation list endpoints."""

    model_config = ConfigDict(from_attributes=True)

    status: str | None = None
    channel: str | None = None
    handler_mode: str | None = None
    help_needed: bool | None = None
    unread_media: bool | None = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)


class ConversationListItem(BaseModel):
    """Single item in the inbox list."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID
    patient_id: UUID | None = None
    channel: str
    status: str
    handler_mode: Literal["ai", "human"]
    help_needed: bool
    unread_media_count: int
    last_message_at: datetime | None = None
    last_message_preview: str | None = None
    messages_count: int
    stage_decision: str | None = None
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """Paginated list of conversations."""

    model_config = ConfigDict(from_attributes=True)

    items: list[ConversationListItem]
    total: int
    limit: int
    offset: int
