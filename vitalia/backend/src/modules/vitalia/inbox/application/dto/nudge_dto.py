# cap: inbox.adrian-inbox
# story-origin: vitalia-fase2-adrian-inbox T-2
"""NudgeRequest / NudgeResponse DTOs — inbox nudge endpoint (RN-13).

Pydantic v2 models. No PHI fields in response (PII allowlist satisfied by
only including structural outcome fields: UUIDs + sent_at + flags).

References:
- 03-arch-be.md § 3 (DTO spec)
- T-2 acceptance validator fn-be-nudge
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NudgeRequest(BaseModel):
    """Request body for POST /conversations/{id}/nudge."""

    model_config = ConfigDict(from_attributes=True)

    reason: str | None = None
    """Optional reason for the nudge (forwarded to activity event description_es)."""

    idempotency_key: str | None = None
    """Optional client-provided idempotency key for dedup.
    If omitted, NudgeService uses the natural key (tenant, conv, 'nudge', day).
    """


class NudgeResponse(BaseModel):
    """Response for POST /conversations/{id}/nudge.

    nudge_sent=False when the natural-key dedup detects a same-day repeat.
    message_id is None when nudge_sent=False (no new message created).
    """

    model_config = ConfigDict(from_attributes=True)

    conversation_id: UUID
    """Conversation that received the nudge."""

    message_id: UUID | None = None
    """Message UUID of the outbound re-engagement message.
    None when nudge_sent=False (idempotency dedup fired).
    """

    nudge_sent: bool
    """True if an outbound message was sent; False if same-day dedup prevented it."""

    activity_event_id: UUID | None = None
    """Activity event row UUID (nudge_sent or dedup-existing)."""

    sent_at: datetime
    """Timestamp of the nudge (or the existing same-day nudge when nudge_sent=False)."""
