# cap: crm.crm-consent-optout
# story-origin: TBD
"""Message domain entity — PHI dual-filter.

Domain layer — pure Python dataclass, no ORM imports.

Per hipaa-lite.md: PHI dual-filter (tenant_id + clinic_id) mandatory.
Per 03-arch-be.md § 3.2: Message entity tracks retraction state + Whisper transcription.

SC-01: agent_ai messages get ActionReceipt for 5min undo window.
SC-02: transcription_confidence < 0.5 triggers graceful fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

# downstream-regression-na: brand-local vitalia CRM domain entity

SenderType = Literal["patient", "agent_ai", "agent_human", "system"]
MediaKind = Literal["audio", "image", "video", "document", "sticker"] | None

# Exported constants for tests and arch fitness checks
VALID_SENDER_TYPES: frozenset[str] = frozenset({"patient", "agent_ai", "agent_human", "system"})
VALID_MEDIA_KINDS: frozenset[str] = frozenset({"audio", "image", "video", "document", "sticker"})


@dataclass
class Message:
    """Message domain entity — PHI dual-filter.

    PHI obligations (hipaa-lite.md § Regla cardinal):
    1. tenant_id + clinic_id dual filter mandatory on every query.
    2. Audit log row written pre-response on mutations (send, retract).
    3. Sanitization: transcription_text may contain PHI — sanitize before traces.
    4. media_phi_flagged = True triggers enhanced logging + PHI guardrail.

    Retraction state machine (SC-01 Action Receipts):
    - Initial:   retracted_at=None, retract_succeeded=None
    - Retracted: retracted_at=<timestamp>, retract_succeeded=True/False
    - Fallback:  retract_succeeded=False = 'marcar erróneo' (email channel)

    SC-02 Whisper fallback:
    - transcription_confidence < 0.5 → service triggers graceful degradation
    - transcription_text=None + confidence=0 = complete fallback
    """

    # Identity (PHI dual-filter keys)
    id: UUID
    tenant_id: UUID
    clinic_id: UUID

    # Relations
    conversation_id: UUID
    channel: str  # mirror of conversation.channel for query convenience

    # External reference (WA wamid / IG msg id)
    external_message_id: str | None

    # Sender
    sender_type: str  # SenderType literal
    sender_user_id: UUID | None  # populated if sender_type='agent_human'

    # Content
    body_text: str | None
    media_kind: str | None  # MediaKind literal — None if text-only
    media_url: str | None
    media_duration_s: int | None  # for audio messages
    media_phi_flagged: bool  # True if image/audio may contain PHI

    # Whisper STT (SC-02)
    transcription_text: str | None
    transcription_confidence: float | None  # 0.0-1.0; < 0.5 = fallback

    # Retraction state (SC-01 Action Receipts)
    retracted_at: datetime | None
    retracted_by_user_id: UUID | None
    retracted_reason: str | None
    retract_succeeded: bool | None  # None=not attempted, True=OK, False=fallback

    # Context snapshot at send time
    handler_mode: str  # snapshot of conversation.handler_mode at send time

    # AI cost tracking (internal — not user-facing)
    cache_hit_rate: float | None
    llm_cost_usd: float | None  # NUMERIC(10,6) at DB layer

    # Delivery timeline
    sent_at: datetime
    delivered_at: datetime | None
    read_at: datetime | None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None = None  # Soft delete only — never hard delete
