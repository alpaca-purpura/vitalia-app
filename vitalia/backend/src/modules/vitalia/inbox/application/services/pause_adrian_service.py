# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""PauseAdrianService — vitalia inbox application layer.

60-minute pause: sets DB pause_until + Redis TTL for fast check.

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter on all repos
2. Audit log written sync pre-response
3. AdrianPaused event via outbox bus

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.vitalia.crm.domain.events import AdrianPaused

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
        ConversationRepository,
    )

logger = structlog.get_logger()

# Default pause duration (60 minutes per arch spec §6.5)
_DEFAULT_PAUSE_MINUTES = 60
_REDIS_KEY_TEMPLATE = "vitalia:inbox:pause:{conversation_id}"


class ConversationNotFoundError(Exception):
    """Raised when conversation does not exist for tenant+clinic."""

    def __init__(self, conversation_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Conversation {conversation_id} not found or access denied")
        self.conversation_id = conversation_id


@dataclass
class PauseResult:
    """Result from PauseAdrianService.pause()."""

    conversation_id: UUID
    pause_until: datetime
    handler_mode: str
    status: str


class PauseAdrianService:
    """Service for pausing Adrián (AI agent) for 60 minutes.

    Sets pause_until in DB and Redis TTL for fast pre-check in Adrián entry point.
    Emits AdrianPaused domain event.
    Writes audit log sync pre-response.
    """

    def __init__(
        self,
        *,
        conv_repo: ConversationRepository,
        audit_writer: object,
        event_bus: object,
        redis_client: object,
        session: AsyncSession,
    ) -> None:
        """Initialize PauseAdrianService.

        Args:
            conv_repo: ConversationRepository (dual-filter enforced).
            audit_writer: Async audit log writer.
            event_bus: Outbox event bus.
            redis_client: Async Redis client for TTL-based pause flag.
            session: AsyncSession for event publish.
        """
        self._conv_repo = conv_repo
        self._audit_writer = audit_writer
        self._event_bus = event_bus
        self._redis = redis_client
        self._session = session

    async def pause(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        paused_by_user_id: UUID,
        reason: str | None,
        duration_minutes: int = _DEFAULT_PAUSE_MINUTES,
    ) -> PauseResult:
        """Pause Adrián for the specified duration (default 60min).

        PHI dual-filter: repo calls include tenant_id AND clinic_id.
        Audit log written sync before returning.
        AdrianPaused event emitted via outbox bus.

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            conversation_id: Target conversation UUID.
            paused_by_user_id: User requesting the pause.
            reason: Optional human-readable pause reason.
            duration_minutes: Pause duration (default 60).

        Returns:
            PauseResult with pause_until timestamp and conversation state.

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

        now = datetime.now(UTC)
        pause_until = now + timedelta(minutes=duration_minutes)
        ttl_seconds = duration_minutes * 60

        # Set Redis key with TTL (fast check in Adrián entry point)
        redis_key = _REDIS_KEY_TEMPLATE.format(conversation_id=str(conversation_id))
        await self._redis.setex(redis_key, ttl_seconds, "1")

        # Persist pause_until in DB
        updated_conv = await self._conv_repo.set_pause_until(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            pause_until=pause_until,
        )

        # Audit log sync write (HIPAA-lite: mandatory pre-response)
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=paused_by_user_id,
            action="inbox.conversation.adrian_paused",
            resource_type="inbox.conversation",
            resource_id=conversation_id,
            payload={
                "duration_minutes": duration_minutes,
                "pause_until": pause_until.isoformat(),
                "reason": reason,
            },
        )

        # Emit AdrianPaused event via outbox bus
        event = AdrianPaused(
            event_name="adrian_paused",
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            clinic_id=clinic_id,
            pause_until=pause_until,
            paused_by_user_id=paused_by_user_id,
            occurred_at=now,
        )
        await self._event_bus.publish(event, session=self._session)

        logger.info(
            "pause_adrian.success",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
            pause_until=pause_until.isoformat(),
            duration_minutes=duration_minutes,
        )

        return PauseResult(
            conversation_id=conversation_id,
            pause_until=updated_conv.pause_until,
            handler_mode=updated_conv.handler_mode,
            status=updated_conv.status,
        )
