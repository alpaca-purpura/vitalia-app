# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""SendMessage DTOs — vitalia inbox application layer.

Pydantic v2 DTOs for send-message endpoint.
Per 03-arch-be.md § 4.3 verbatim shapes.

PHI note: MessageResponse never includes raw PHI fields (transcription_text
is scrubbed of identifiers before returning to caller via sanitize_payload
at the service layer — only the UI-safe preview text is returned).

downstream-regression-na: brand-local vitalia inbox DTO (no cross-brand consumers)
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SendMessageRequest(BaseModel):
    """Request body for POST /inbox/conversations/{conv_id}/messages."""

    model_config = ConfigDict(from_attributes=True)

    body_text: str | None = Field(None, max_length=4000)
    media_url: str | None = None
    media_kind: Literal["audio", "image", "video", "document"] | None = None
    media_duration_s: int | None = Field(None, ge=0, le=300)
    handler_mode_override: Literal["ai", "human"] | None = None
    idempotency_key: str | None = Field(None, max_length=64)


class MessageResponse(BaseModel):
    """Response for a single message (send / retract result)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_type: Literal["patient", "agent_ai", "agent_human", "system"]
    sender_user_id: UUID | None = None
    body_text: str | None = None
    media_kind: Literal["audio", "image", "video", "document", "sticker"] | None = None
    media_url: str | None = None
    media_duration_s: int | None = None
    transcription_text: str | None = None
    transcription_confidence: float | None = None
    retracted_at: datetime | None = None
    retract_succeeded: bool | None = None
    handler_mode: Literal["ai", "human"]
    sent_at: datetime
    action_receipt_expires_at: datetime | None = None
