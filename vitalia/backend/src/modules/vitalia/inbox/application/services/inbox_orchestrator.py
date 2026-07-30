# cap: copilot.inbox-tools-extensions
# story-origin: TBD
"""InboxOrchestrator — vitalia inbox application layer.

Top-level read service composing Lead + Conversation + Message + ActivityEvent.

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter on all PHI repos
2. sanitize_payload applied to any event payload field
3. No audit log required for reads (orchestrator is observability, not mutation)
4. PHI fields not leaked via response_model (enforced at API layer)

Per 03-arch-be.md § 6.1:
- Compose lead + conv + messages + activity for GET /crm/conversations/{id}
- ConversationDetailResponse: conversation state + last N messages + activity stream

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.vitalia.inbox.application.services.activity_event_service import (
    ActivityEventService,
    ActivityStreamItem,
)

if TYPE_CHECKING:
    from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
        ActionReceiptRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
        ConversationRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
        MessageRepository,
    )

logger = structlog.get_logger()

# Default number of messages to include in conversation detail
_DEFAULT_MESSAGES_LIMIT = 50

# Default activity stream limit
_DEFAULT_ACTIVITY_LIMIT = 8


class ConversationNotFoundError(Exception):
    """Raised when conversation does not exist for tenant+clinic."""

    def __init__(self, conversation_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Conversation {conversation_id} not found or access denied")
        self.conversation_id = conversation_id


@dataclass
class MessageSummary:
    """Minimal message representation for conversation detail view."""

    id: UUID
    conversation_id: UUID
    sender_type: str
    sender_user_id: UUID | None
    body_text: str | None
    media_kind: str | None
    media_url: str | None
    media_duration_s: int | None
    transcription_text: str | None
    transcription_confidence: float | None
    retracted_at: datetime | None
    retract_succeeded: bool | None
    handler_mode: str
    sent_at: datetime
    action_receipt_expires_at: datetime | None


@dataclass
class ConversationDetail:
    """Full conversation detail composed from multiple repos."""

    id: UUID
    tenant_id: UUID
    clinic_id: UUID
    lead_id: UUID
    patient_id: UUID | None
    channel: str
    status: str
    handler_mode: str
    proposal_required: bool
    pause_until: datetime | None
    help_needed: bool
    last_message_at: datetime | None
    messages_count: int
    updated_at: datetime
    messages: list[MessageSummary] = field(default_factory=list)
    activity_stream: list[ActivityStreamItem] = field(default_factory=list)


class InboxOrchestrator:
    """Top-level read service composing lead+conv+msg+activity.

    Used by GET /api/v1/vitalia/crm/conversations/{id} for ConversationDetailResponse.

    PHI dual-filter: ALL repo calls include tenant_id AND clinic_id.
    Read-only: no mutations. Composed from existing repos and services.
    """

    def __init__(
        self,
        *,
        conv_repo: ConversationRepository,
        msg_repo: MessageRepository,
        receipt_repo: ActionReceiptRepository,
        activity_service: ActivityEventService,
    ) -> None:
        """Initialize InboxOrchestrator.

        Args:
            conv_repo: ConversationRepository (dual-filter enforced).
            msg_repo: MessageRepository (dual-filter enforced).
            receipt_repo: ActionReceiptRepository for action_receipt_expires_at.
            activity_service: ActivityEventService for activity stream.
        """
        self._conv_repo = conv_repo
        self._msg_repo = msg_repo
        self._receipt_repo = receipt_repo
        self._activity_service = activity_service

    async def get_conversation_detail(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        messages_limit: int = _DEFAULT_MESSAGES_LIMIT,
        activity_limit: int = _DEFAULT_ACTIVITY_LIMIT,
    ) -> ConversationDetail:
        """Compose conversation detail from multiple domain repos.

        PHI dual-filter: conv + msg + activity repos all use tenant_id + clinic_id.

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            conversation_id: Target conversation UUID.
            messages_limit: Max messages to include (default 50).
            activity_limit: Max activity events to include (default 8).

        Returns:
            ConversationDetail with composed data.

        Raises:
            ConversationNotFoundError: If conversation not found for tenant+clinic.
        """
        # Fetch conversation (dual-filter applied by repo)
        conv = await self._conv_repo.get_by_id(
            id=conversation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )
        if conv is None:
            raise ConversationNotFoundError(conversation_id)

        # Fetch messages (dual-filter applied by repo)
        raw_messages = await self._msg_repo.list_for_conversation(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            limit=messages_limit,
        )

        # For each message, fetch action_receipt_expires_at if available
        messages: list[MessageSummary] = []
        for msg in raw_messages:
            action_receipt_expires_at: datetime | None = None
            try:
                receipt = await self._receipt_repo.get_active_for_message(
                    message_id=msg.id,
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                )
                if receipt is not None:
                    action_receipt_expires_at = receipt.expires_at
            except Exception:
                # Soft-fail: action receipt unavailable (non-critical for detail view)
                logger.warning(
                    "inbox_orchestrator.receipt_fetch_failed",
                    message_id=str(msg.id),
                    conversation_id=str(conversation_id),
                )

            messages.append(
                MessageSummary(
                    id=msg.id,
                    conversation_id=msg.conversation_id,
                    sender_type=msg.sender_type,
                    sender_user_id=msg.sender_user_id,
                    body_text=msg.body_text,
                    media_kind=msg.media_kind,
                    media_url=msg.media_url,
                    media_duration_s=msg.media_duration_s,
                    transcription_text=msg.transcription_text,
                    transcription_confidence=msg.transcription_confidence,
                    retracted_at=msg.retracted_at,
                    retract_succeeded=msg.retract_succeeded,
                    handler_mode=msg.handler_mode,
                    sent_at=msg.sent_at,
                    action_receipt_expires_at=action_receipt_expires_at,
                )
            )

        # Fetch activity stream (dual-filter via ActivityEventService)
        activity_result = await self._activity_service.get_stream(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conversation_id,
            limit=activity_limit,
        )

        logger.debug(
            "inbox_orchestrator.detail_fetched",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
            messages_count=len(messages),
            activity_count=len(activity_result.events),
        )

        return ConversationDetail(
            id=conv.id,
            tenant_id=conv.tenant_id,
            clinic_id=conv.clinic_id,
            lead_id=conv.lead_id,
            patient_id=conv.patient_id,
            channel=conv.channel,
            status=conv.status,
            handler_mode=conv.handler_mode,
            proposal_required=conv.proposal_required,
            pause_until=conv.pause_until,
            help_needed=conv.help_needed,
            last_message_at=conv.last_message_at,
            messages_count=conv.messages_count,
            updated_at=conv.updated_at,
            messages=messages,
            activity_stream=activity_result.events,
        )
