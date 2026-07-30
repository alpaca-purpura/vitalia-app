# cap: adrian.inbox
# story-origin: vitalia-fase2-adrian-inbox
"""conversation_detail_dto.py — Compound conversation detail response.

The Adrián inbox thread (`InboxThread` / `useConversationDetail`) consumes the
FULL compound for a single conversation:

    { conversation, lead, messages, action_receipts, tools_state }

This mirrors the FE `ConversationDetail` type (features/adrian/types/inbox.types.ts).
The crm `GET /conversations/{id}` endpoint returns this (was returning the lean
`ConversationListItem` → thread could not render: `detail.messages` undefined).

PHI: `lead.name/email/phone` are decrypted server-side (pgcrypto) and gated by
`_INBOX_OPERATOR_ROLES` + dual filter tenant_id+clinic_id at the endpoint.

downstream-regression-na: brand-local vitalia inbox DTO; no cross-brand consumers
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.modules.vitalia.crm.application.dto.lead_dto import LeadResponse


class ConversationDetailConversation(BaseModel):
    """Conversation entity — full field set the FE `Conversation` type declares.

    Superset of `ConversationListItem` (adds tenant_id/clinic_id/proposal_required/
    pause_until/help_needed_reason/linked_offer_id which the thread header needs).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    lead_id: UUID | None = None
    tenant_id: UUID
    clinic_id: UUID
    patient_id: UUID | None = None
    channel: str
    status: str
    handler_mode: Literal["ai", "human"]
    proposal_required: bool
    pause_until: datetime | None = None
    help_needed: bool
    help_needed_reason: str | None = None
    unread_media_count: int
    last_message_at: datetime | None = None
    last_message_preview: str | None = None
    messages_count: int
    stage_decision: str | None = None
    linked_offer_id: UUID | None = None
    updated_at: datetime


class ConversationDetailMessage(BaseModel):
    """Single message in the thread — mirrors FE `Message`."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID
    sender_type: str
    sender_user_id: UUID | None = None
    body_text: str | None = None
    media_kind: str | None = None
    media_url: str | None = None
    media_duration_s: int | None = None
    transcription_text: str | None = None
    transcription_confidence: float | None = None
    retracted_at: datetime | None = None
    retract_succeeded: bool | None = None
    handler_mode: Literal["ai", "human"]
    sent_at: datetime
    action_receipt_expires_at: datetime | None = None


class ConversationDetailResponse(BaseModel):
    """Compound conversation detail for the inbox thread (FE `ConversationDetail`)."""

    conversation: ConversationDetailConversation
    lead: LeadResponse | None = None
    messages: list[ConversationDetailMessage]
    action_receipts: list[dict] = []
    tools_state: dict | None = None
