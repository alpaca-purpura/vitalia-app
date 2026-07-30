# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""RetractMessageService — vitalia inbox application layer.

SC-03 coverage: 5min action receipt window + OCC + channel adapter + fallback.

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter on all repos
2. Audit log written sync pre-response
3. No PHI in structlog traces
4. Emits MessageRetracted via outbox bus

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.vitalia.connections.email.adapter import ChannelRetractUnsupportedError
from src.modules.vitalia.crm.domain.events import MessageRetracted

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


class ActionReceiptExpiredError(Exception):
    """Raised when the 5-minute retract window has expired (→ 410 Gone)."""

    def __init__(self, message_id: UUID, expired_at: datetime) -> None:
        """Initialize."""
        super().__init__(f"Action receipt for message {message_id} expired at {expired_at}")
        self.message_id = message_id
        self.expired_at = expired_at


class MessageNotRetractableError(Exception):
    """Raised when no active action receipt exists for the message."""

    def __init__(self, message_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"No active action receipt for message {message_id}")
        self.message_id = message_id


class PatientRepliedConflictError(Exception):
    """Raised when patient replied after the AI message (→ 409 Conflict)."""

    def __init__(self, message_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Cannot retract message {message_id}: patient has replied")
        self.message_id = message_id


@dataclass
class RetractResult:
    """Result from RetractMessageService.retract()."""

    message_id: UUID
    retracted_at: datetime | None
    retract_succeeded: bool
    fallback_applied: bool
    retract_reason: str | None


class RetractMessageService:
    """Service for retracting AI messages within the 5-minute window.

    Enforces:
    1. Active action receipt exists (not expired, not already retracted)
    2. No patient reply after the message (→ 409 Conflict)
    3. Channel adapter retract (with graceful degradation to fallback)
    4. Sync audit log write
    5. MessageRetracted event via outbox bus
    """

    def __init__(
        self,
        *,
        msg_repo: MessageRepository,
        receipt_repo: ActionReceiptRepository,
        conv_repo: ConversationRepository,
        audit_writer: object,
        event_bus: object,
        channel_adapters: dict[str, object],
        session: object | None = None,
    ) -> None:
        """Initialize RetractMessageService.

        Args:
            msg_repo: MessageRepository (dual-filter enforced).
            receipt_repo: ActionReceiptRepository (dual-filter enforced).
            conv_repo: ConversationRepository (dual-filter enforced).
            audit_writer: Async audit log writer.
            event_bus: Outbox event bus.
            channel_adapters: Dict mapping channel name to adapter instance.
            session: Optional AsyncSession for event publish.
        """
        self._msg_repo = msg_repo
        self._receipt_repo = receipt_repo
        self._conv_repo = conv_repo
        self._audit_writer = audit_writer
        self._event_bus = event_bus
        self._channel_adapters = channel_adapters
        self._session = session

    async def retract(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        message_id: UUID,
        retracted_by_user_id: UUID,
        reason: str | None,
    ) -> RetractResult:
        """Attempt to retract a message within the 5-minute action receipt window.

        PHI dual-filter: all repo calls include tenant_id AND clinic_id.
        Audit log written sync before returning result.

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            conversation_id: Conversation UUID.
            message_id: Message UUID to retract.
            retracted_by_user_id: User requesting the retraction.
            reason: Optional retract reason label ('user_undo').

        Returns:
            RetractResult with retract_succeeded + fallback_applied flags.

        Raises:
            MessageNotRetractableError: No active action receipt.
            ActionReceiptExpiredError: Receipt exists but 5min window expired.
            PatientRepliedConflictError: Patient replied after the message.
        """
        # Fetch message (dual-filter via repo)
        msg = await self._msg_repo.get_by_id(
            id=message_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )
        if msg is None:
            raise MessageNotRetractableError(message_id)

        # Check action receipt
        receipt = await self._receipt_repo.get_active_for_message(
            message_id=message_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        if receipt is None:
            raise MessageNotRetractableError(message_id)

        # Enforce 5-minute window
        now = datetime.now(UTC)
        if receipt.expires_at < now:
            raise ActionReceiptExpiredError(message_id, receipt.expires_at)

        # Check for patient reply
        patient_reply = await self._msg_repo.find_patient_reply_after(
            message_id=message_id,
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        if patient_reply is not None:
            raise PatientRepliedConflictError(message_id)

        # Attempt channel retract
        retract_succeeded = False
        fallback_applied = False

        adapter = self._channel_adapters.get(msg.channel)
        if adapter is not None:
            try:
                adapter_result = await adapter.retract_message_id(msg.external_message_id)  # type: ignore[union-attr]
                retract_succeeded = adapter_result.succeeded
            except ChannelRetractUnsupportedError:
                # Email or other unsupported channel → apply "marcar como erróneo" fallback
                retract_succeeded = False
                fallback_applied = True
                logger.info(
                    "retract_message.channel_unsupported_fallback",
                    channel=msg.channel,
                    message_id=str(message_id),
                )
            except Exception:
                retract_succeeded = False
                logger.warning(
                    "retract_message.channel_adapter_error",
                    channel=msg.channel,
                    message_id=str(message_id),
                )

        if not retract_succeeded and not fallback_applied:
            fallback_applied = True

        # Persist retraction state
        await self._msg_repo.mark_retracted(
            message_id=message_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            retracted_by_user_id=retracted_by_user_id,
            retracted_at=now,
            retract_succeeded=retract_succeeded,
            retracted_reason=reason or "user_undo",
        )

        # Flip conversation handler_mode to 'human' after retract (Critical #2 — SC-01 spec §6.3)
        # Fetch conversation for OCC token (needed by update_handler_mode)
        conv = await self._conv_repo.get_by_id(
            id=conversation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )
        if conv is not None:
            await self._conv_repo.update_handler_mode(
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                new_handler_mode="human",
                expected_updated_at=conv.updated_at,
            )
            logger.info(
                "retract_message.handler_mode_flipped_human",
                conversation_id=str(conversation_id),
                tenant_id=str(tenant_id),
            )

        # Audit log sync write (HIPAA-lite: mandatory pre-response)
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=retracted_by_user_id,
            action="inbox.message.retracted",
            resource_type="inbox.message",
            resource_id=message_id,
            payload={
                "conversation_id": str(conversation_id),
                "retract_succeeded": retract_succeeded,
                "fallback_applied": fallback_applied,
                "channel": msg.channel,
            },
        )

        # Emit MessageRetracted event via outbox bus
        event = MessageRetracted(
            event_name="message_retracted",
            tenant_id=tenant_id,
            message_id=message_id,
            conversation_id=conversation_id,
            clinic_id=clinic_id,
            retract_succeeded=retract_succeeded,
            retract_reason=reason or "user_undo",
            occurred_at=now,
        )
        await self._event_bus.publish(event, session=self._session)

        logger.info(
            "retract_message.complete",
            tenant_id=str(tenant_id),
            message_id=str(message_id),
            retract_succeeded=retract_succeeded,
            fallback_applied=fallback_applied,
        )

        return RetractResult(
            message_id=message_id,
            retracted_at=now,
            retract_succeeded=retract_succeeded,
            fallback_applied=fallback_applied,
            retract_reason=reason or "user_undo",
        )
