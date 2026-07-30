# cap: crm.crm-consent-optout
# story-origin: TBD
"""Conversation domain entity — PHI dual-filter (tenant_id + clinic_id).

Domain layer — pure Python dataclass, no ORM imports.

Per hipaa-lite.md: every PHI entity requires tenant_id AND clinic_id.
Per 03-arch-be.md § 3.1: Conversation is PHI (contains patient data + channel info).

SC-01 happy path: Adrián decides mode (handler_mode='ai', proposal_required=False).
SC-03 OCC: updated_at field used for If-Match optimistic concurrency.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

# downstream-regression-na: brand-local vitalia CRM domain entity

ChannelType = Literal["whatsapp", "instagram", "facebook_messenger", "web", "walk_in", "phone"]
ConversationStatus = Literal["active", "paused", "closed", "archived"]
HandlerMode = Literal["ai", "human"]
StageDecision = Literal["interesado", "considerando", "listo", "decidio_no"] | None

# Exported constants for tests and arch fitness checks
VALID_CHANNELS: frozenset[str] = frozenset({"whatsapp", "instagram", "facebook_messenger", "web", "walk_in", "phone"})
VALID_STATUSES: frozenset[str] = frozenset({"active", "paused", "closed", "archived"})
VALID_HANDLER_MODES: frozenset[str] = frozenset({"ai", "human"})
VALID_STAGE_DECISIONS: frozenset[str] = frozenset({"interesado", "considerando", "listo", "decidio_no"})


@dataclass
class Conversation:
    """Conversation domain entity — PHI dual-filter.

    PHI obligations (hipaa-lite.md § Regla cardinal):
    1. tenant_id + clinic_id dual filter mandatory on every query.
    2. Audit log row written pre-response on mutations.
    3. Sanitization applied before traces.
    4. Encryption at-rest for sensitive fields.

    Segmented 3-modos (01-spec § 5):
    - Adrián decide:   handler_mode='ai'    + proposal_required=False
    - Adrián consulta: handler_mode='ai'    + proposal_required=True
    - Yo escribo:      handler_mode='human' + proposal_required=False

    OCC conflict (SC-03):
    - updated_at is the OCC token used in If-Match header validation.
    - RetractMessageService + SetModeService check this before mutation.
    """

    # Identity (PHI dual-filter keys)
    id: UUID
    tenant_id: UUID
    clinic_id: UUID

    # Relations
    lead_id: UUID
    patient_id: UUID | None  # None until lead converts to patient

    # Channel
    channel: str  # ChannelType literal validated at infra layer
    channel_external_id: str | None  # WA/IG conversation external ref

    # State
    status: str  # ConversationStatus
    handler_mode: str  # HandlerMode: 'ai' | 'human'
    proposal_required: bool  # True = 'Adrián consulta' HITL mode
    pause_until: datetime | None  # 60min pause window (auto-resumes)

    # Escalation flags
    help_needed: bool
    help_needed_reason: str | None

    # Media tracking
    unread_media_count: int

    # Denormalized for list rendering performance
    last_message_at: datetime | None
    last_message_preview: str | None  # truncated for list rendering
    messages_count: int

    # Pipeline stage (consultive selling)
    stage_decision: str | None  # StageDecision enum

    # Engine cross-reference
    linked_offer_id: UUID | None

    # Timestamps
    created_at: datetime
    updated_at: datetime  # OCC token for If-Match optimistic concurrency (SC-03)
    deleted_at: datetime | None = None  # Soft delete only — never hard delete
