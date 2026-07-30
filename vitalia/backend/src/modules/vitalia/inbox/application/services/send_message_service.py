# cap: inbox.adrian-inbox
# story-origin: vitalia-fase2-adrian-inbox T-1
"""SendMessageService — vitalia inbox application layer.

SC-01 happy path: human/ai message send with idempotency + audit log + outbox event.
SC-3 (T-1 Slice 2): PHI compliance gate via optional ComplianceService(PhiChannelPolicy).
  When compliance blocks outbound PHI on unencrypted channel:
  - Replaces PHI body_text with portal-redirect microcopy
  - Writes activity event 'compliance_block_outbound_phi' (no raw PHI in description_es)
  - Writes audit row 'compliance_block_outbound_phi' pre-response
  The agent voice instruction is the primary guard; this service check is the infra fallback.

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter mandatory (via repos)
2. Audit log row written sync pre-response
3. No PHI in structlog traces (sanitize_payload applied by audit_writer)
4. Encryption at-rest handled by infra

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import structlog
from luana_core_platform.domain.events import DomainEvent

from src.modules.vitalia.crm.domain.events import MessageSent

if TYPE_CHECKING:
    from luana_core_idempotency.infrastructure.redis_store import IdempotencyStore
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
        ActionReceiptRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
        ActivityEventRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
        ConversationRepository,
    )
    from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
        MessageRepository,
    )

logger = structlog.get_logger()

# 5-minute action receipt window (per arch spec §6.3)
_ACTION_RECEIPT_WINDOW_MINUTES = 5

# Portal redirect microcopy SSoT (SC-3/RN-7 hipaa-lite.md § Voice patterns).
# Spanish neutro LatAm — no voseo (spanish-text.md).
_PORTAL_REDIRECT_MICROCOPY = (
    "Por seguridad, tus resultados y datos clínicos están disponibles en tu portal. "
    "Ingresa en el enlace que te compartimos al registrarte."
)


class ConversationNotFoundError(Exception):
    """Raised when conversation does not exist for the given tenant+clinic."""

    def __init__(self, conversation_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Conversation {conversation_id} not found or access denied")
        self.conversation_id = conversation_id


class _AuditWriterProtocol:
    """Protocol for audit writer (duck-typing compatible)."""

    async def write(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        payload: dict | None = None,
    ) -> None:
        """Write audit row."""
        ...


class _EventBusProtocol:
    """Protocol for event bus (duck-typing compatible)."""

    async def publish(self, event: DomainEvent, **kwargs: object) -> None:
        """Publish domain event."""
        ...


class SendMessageResult:
    """Result from SendMessageService.send()."""

    def __init__(
        self,
        *,
        message_id: UUID,
        conversation_id: UUID,
        sender_type: str,
        sender_user_id: UUID | None,
        body_text: str | None,
        media_kind: str | None,
        media_url: str | None,
        media_duration_s: int | None,
        transcription_text: str | None,
        transcription_confidence: float | None,
        retracted_at: datetime | None,
        retract_succeeded: bool | None,
        handler_mode: str,
        sent_at: datetime,
        action_receipt_expires_at: datetime | None,
    ) -> None:
        """Initialize send result."""
        self.message_id = message_id
        self.conversation_id = conversation_id
        self.sender_type = sender_type
        self.sender_user_id = sender_user_id
        self.body_text = body_text
        self.media_kind = media_kind
        self.media_url = media_url
        self.media_duration_s = media_duration_s
        self.transcription_text = transcription_text
        self.transcription_confidence = transcription_confidence
        self.retracted_at = retracted_at
        self.retract_succeeded = retract_succeeded
        self.handler_mode = handler_mode
        self.sent_at = sent_at
        self.action_receipt_expires_at = action_receipt_expires_at


class SendMessageService:
    """Service for sending messages in a conversation.

    Handles both human-path (direct channel send) and ai-path (enqueue Adrián).
    Writes audit log row sync pre-response (HIPAA-lite requirement).
    Emits MessageSent domain event via outbox bus.
    Supports idempotency dedup via optional idempotency_store.

    Slice 2 (T-1): Optional compliance_service runs PHI channel gate before outbound.
    When compliance blocks: portal-redirect microcopy replaces body_text + activity event
    'compliance_block_outbound_phi' written (no raw PHI in description_es per RN-10).
    """

    def __init__(
        self,
        *,
        conv_repo: ConversationRepository,
        msg_repo: MessageRepository,
        receipt_repo: ActionReceiptRepository,
        audit_writer: _AuditWriterProtocol,
        event_bus: _EventBusProtocol,
        session: AsyncSession,
        idempotency_store: IdempotencyStore | None = None,
        compliance_service: object | None = None,
        activity_event_repo: ActivityEventRepository | None = None,
    ) -> None:
        """Initialize SendMessageService.

        Args:
            conv_repo: ConversationRepository (dual-filter enforced).
            msg_repo: MessageRepository (dual-filter enforced).
            receipt_repo: ActionReceiptRepository (for 5min window receipts).
            audit_writer: Async audit log writer.
            event_bus: Outbox event bus.
            session: AsyncSession for transaction coordination.
            idempotency_store: Optional idempotency store for dedup.
            compliance_service: Optional ComplianceService for PHI channel gate (T-1 Slice 2).
            activity_event_repo: Optional ActivityEventRepository for compliance activity events.
        """
        self._conv_repo = conv_repo
        self._msg_repo = msg_repo
        self._receipt_repo = receipt_repo
        self._audit_writer = audit_writer
        self._event_bus = event_bus
        self._session = session
        self._idempotency_store = idempotency_store
        self._compliance_service = compliance_service
        self._activity_event_repo = activity_event_repo

    async def send(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        user_id: UUID,
        body_text: str | None = None,
        media_url: str | None = None,
        media_kind: str | None = None,
        media_duration_s: int | None = None,
        handler_mode_override: str | None = None,
        idempotency_key: str | None = None,
    ) -> SendMessageResult:
        """Send a message in a conversation.

        PHI dual-filter: all repo calls include tenant_id AND clinic_id.
        Audit log written sync before returning result.
        MessageSent event emitted via outbox bus.

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            conversation_id: Target conversation UUID.
            user_id: Sending user UUID.
            body_text: Optional message text (max 4000 chars).
            media_url: Optional media URL.
            media_kind: Optional media kind (audio/image/video/document).
            media_duration_s: Optional audio duration in seconds.
            handler_mode_override: Optional override for handler mode ('ai' | 'human').
                                   When provided, applies before determining sender_type.
            idempotency_key: Optional dedup key (Idempotency-Key header).

        Returns:
            SendMessageResult with message details and optional action receipt.

        Raises:
            ConversationNotFoundError: If conversation does not exist for tenant+clinic.
        """
        # Idempotency check (if store provided)
        if idempotency_key and self._idempotency_store:
            claimed = await self._idempotency_store.claim(
                type("Key", (), {"namespace": "inbox.send", "key": idempotency_key})()
            )
            if not claimed:
                cached = await self._idempotency_store.cached_result(
                    type("Key", (), {"namespace": "inbox.send", "key": idempotency_key})()
                )
                if cached is not None:
                    logger.info(
                        "send_message.idempotency_cache_hit",
                        idempotency_key=idempotency_key,
                        tenant_id=str(tenant_id),
                    )
                    # Return stub from cache — msg_repo.create NOT called
                    return SendMessageResult(
                        message_id=UUID(cached["message_id"]),
                        conversation_id=conversation_id,
                        sender_type=cached.get("sender_type", "agent_human"),
                        sender_user_id=user_id,
                        body_text=body_text,
                        media_kind=media_kind,
                        media_url=media_url,
                        media_duration_s=media_duration_s,
                        transcription_text=None,
                        transcription_confidence=None,
                        retracted_at=None,
                        retract_succeeded=None,
                        handler_mode=cached.get("handler_mode", "human"),
                        sent_at=datetime.now(UTC),
                        action_receipt_expires_at=None,
                    )

        # Fetch conversation (dual-filter applied by repo)
        conv = await self._conv_repo.get_by_id(
            id=conversation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )
        if conv is None:
            raise ConversationNotFoundError(conversation_id)

        now = datetime.now(UTC)

        # PHI compliance gate (T-1 Slice 2 — SC-3/RN-7 hipaa-lite.md).
        # Applies only when compliance_service is wired (optional for backward compat).
        # Checks outbound text messages against PHI keywords on unencrypted channels.
        # When blocked: replaces body_text with portal-redirect microcopy + writes
        # activity event + audit row 'compliance_block_outbound_phi'.
        # lead_id is not available in the send path — pass conversation_id as sentinel
        # (PhiChannelPolicy only uses channel + identifier, not lead_id).
        if self._compliance_service is not None and body_text is not None:
            compliance_result = await self._compliance_service.check(
                tenant_id=tenant_id,
                lead_id=conversation_id,  # sentinel: PhiChannelPolicy ignores lead_id
                channel=conv.channel,
                identifier=body_text,
                campaign_id=None,
            )
            if not compliance_result.allowed:
                # Replace body_text with portal-redirect microcopy (no PHI in response)
                body_text = _PORTAL_REDIRECT_MICROCOPY
                logger.info(
                    "send_message.phi_compliance_blocked",
                    channel=conv.channel,
                    failed_policy=compliance_result.failed_policy,
                    tenant_id=str(tenant_id),
                    conversation_id=str(conversation_id),
                )
                # Write activity event (no raw PHI in description_es — RN-10)
                if self._activity_event_repo is not None:
                    from src.modules.vitalia.crm.infrastructure.persistence.models.activity_event_model import (  # noqa: PLC0415
                        ActivityEventModel,
                    )

                    activity_model = ActivityEventModel(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        clinic_id=clinic_id,
                        conversation_id=conversation_id,
                        source_trace_event_id=None,
                        event_kind="compliance_block_outbound_phi",
                        description_es=("Adrián detectó contenido clínico en canal no cifrado y redirigió al portal."),
                        agent_id="adrian",
                        occurred_at=now,
                        payload_sanitized={
                            "channel": conv.channel,
                            "failed_policy": compliance_result.failed_policy,
                            "action": "portal_redirect",
                        },
                        created_at=now,
                    )
                    self._activity_event_repo._session.add(activity_model)
                    await self._activity_event_repo._session.flush()
                # Write audit row sync pre-response (HIPAA-lite)
                await self._audit_writer.write(
                    tenant_id=tenant_id,
                    clinic_id=clinic_id,
                    user_id=user_id,
                    action="compliance_block_outbound_phi",
                    resource_type="inbox.compliance_block",
                    resource_id=conversation_id,
                    payload={
                        "channel": conv.channel,
                        "failed_policy": compliance_result.failed_policy,
                        "action": "portal_redirect",
                    },
                )

        # Apply handler_mode_override if provided (Medium #5)
        effective_mode = handler_mode_override if handler_mode_override is not None else conv.handler_mode
        if handler_mode_override is not None and handler_mode_override != conv.handler_mode:
            await self._conv_repo.update_handler_mode(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                new_handler_mode=handler_mode_override,
                expected_updated_at=conv.updated_at,
            )
            logger.info(
                "send_message.handler_mode_override_applied",
                conversation_id=str(conversation_id),
                old_mode=conv.handler_mode,
                new_mode=handler_mode_override,
            )

        sender_type = "agent_human" if effective_mode == "human" else "agent_ai"

        # Persist message
        msg = await self._msg_repo.create(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            conversation_id=conversation_id,
            channel=conv.channel,
            external_message_id=None,
            sender_type=sender_type,
            sender_user_id=user_id,
            body_text=body_text,
            media_kind=media_kind,
            media_url=media_url,
            media_duration_s=media_duration_s,
            media_phi_flagged=False,
            transcription_text=None,
            transcription_confidence=None,
            retracted_at=None,
            retracted_by_user_id=None,
            retracted_reason=None,
            retract_succeeded=None,
            handler_mode=effective_mode,
            cache_hit_rate=None,
            llm_cost_usd=None,
            sent_at=now,
            delivered_at=None,
            read_at=None,
        )

        # Create ActionReceipt for AI messages (Critical #1 — SC-01 §6.3)
        action_receipt_expires_at: datetime | None = None
        if sender_type == "agent_ai":
            action_receipt_expires_at = now + timedelta(minutes=_ACTION_RECEIPT_WINDOW_MINUTES)
            await self._receipt_repo.create(
                message_id=msg.id,
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                expires_at=action_receipt_expires_at,
            )
            logger.info(
                "send_message.action_receipt_created",
                message_id=str(msg.id),
                expires_at=action_receipt_expires_at.isoformat(),
            )

        # Audit log sync write (HIPAA-lite: mandatory pre-response)
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=user_id,
            action="inbox.message.sent",
            resource_type="inbox.message",
            resource_id=msg.id,
            payload={
                "conversation_id": str(conversation_id),
                "sender_type": sender_type,
                "handler_mode": effective_mode,
                "has_media": media_url is not None,
                "action_receipt_created": action_receipt_expires_at is not None,
            },
        )

        # Emit MessageSent event via outbox bus
        event = MessageSent(
            event_name="message_sent",
            tenant_id=tenant_id,
            message_id=msg.id,
            conversation_id=conversation_id,
            clinic_id=clinic_id,
            sender_type=sender_type,
            channel=conv.channel,
            occurred_at=now,
        )
        await self._event_bus.publish(event, session=self._session)

        logger.info(
            "send_message.success",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
            sender_type=sender_type,
            action_receipt_expires_at=(action_receipt_expires_at.isoformat() if action_receipt_expires_at else None),
        )

        return SendMessageResult(
            message_id=msg.id,
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_user_id=user_id,
            body_text=body_text,
            media_kind=media_kind,
            media_url=media_url,
            media_duration_s=media_duration_s,
            transcription_text=None,
            transcription_confidence=None,
            retracted_at=None,
            retract_succeeded=None,
            handler_mode=effective_mode,
            sent_at=now,
            action_receipt_expires_at=action_receipt_expires_at,
        )
