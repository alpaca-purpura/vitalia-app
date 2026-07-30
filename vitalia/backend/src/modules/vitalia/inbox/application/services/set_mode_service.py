# cap: sales_agent.inbox-handler-mode-occ
# story-origin: TBD
"""SetModeService — vitalia inbox application layer.

SC-03 OCC: mode change with If-Match optimistic concurrency control.

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter on all repos
2. Audit log written sync pre-response
3. ModeChanged event via outbox bus

downstream-regression-na: brand-local vitalia inbox service
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.vitalia.crm.domain.events import ModeChanged

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
        ConversationRepository,
    )

logger = structlog.get_logger()


class ConversationNotFoundError(Exception):
    """Raised when conversation does not exist for tenant+clinic."""

    def __init__(self, conversation_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"Conversation {conversation_id} not found or access denied")
        self.conversation_id = conversation_id


class OCCConflictError(Exception):
    """Raised when OCC check fails (stale expected_updated_at → 409 Conflict)."""

    def __init__(self, conversation_id: UUID) -> None:
        """Initialize."""
        super().__init__(f"OCC conflict on conversation {conversation_id}: updated_at mismatch — reload and retry")
        self.conversation_id = conversation_id


@dataclass
class SetModeResult:
    """Result from SetModeService.set_mode()."""

    conversation_id: UUID
    handler_mode: str
    proposal_required: bool
    status: str
    pause_until: datetime | None
    help_needed: bool
    updated_at: datetime


class SetModeService:
    """Service for changing handler_mode with Optimistic Concurrency Control.

    Uses expected_updated_at (from If-Match header) to detect concurrent edits.
    Returns 409 (OCCConflictError) if conversation was updated since last read.
    """

    def __init__(
        self,
        *,
        conv_repo: ConversationRepository,
        audit_writer: object,
        event_bus: object,
        session: AsyncSession,
    ) -> None:
        """Initialize SetModeService.

        Args:
            conv_repo: ConversationRepository (dual-filter enforced).
            audit_writer: Async audit log writer.
            event_bus: Outbox event bus.
            session: AsyncSession for event publish.
        """
        self._conv_repo = conv_repo
        self._audit_writer = audit_writer
        self._event_bus = event_bus
        self._session = session

    async def set_mode(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        conversation_id: UUID,
        new_mode: str,
        proposal_required: bool,
        expected_updated_at: datetime,
        changed_by_user_id: UUID,
    ) -> SetModeResult:
        """Change handler_mode with OCC guard.

        PHI dual-filter: repo calls include tenant_id AND clinic_id.
        Audit log written sync before returning.
        ModeChanged event emitted via outbox bus.

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            conversation_id: Target conversation UUID.
            new_mode: New handler mode ('ai' or 'human').
            proposal_required: Whether proposal is required.
            expected_updated_at: OCC token (from If-Match header).
            changed_by_user_id: User performing the change.

        Returns:
            SetModeResult with updated conversation state.

        Raises:
            ConversationNotFoundError: If conversation does not exist.
            OCCConflictError: If expected_updated_at doesn't match current row.
        """
        # Fetch conversation (dual-filter applied by repo)
        conv = await self._conv_repo.get_by_id(
            id=conversation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )
        if conv is None:
            raise ConversationNotFoundError(conversation_id)

        from_mode = conv.handler_mode

        # OCC update: returns True if rowcount==1, False if stale
        success = await self._conv_repo.update_handler_mode(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            new_handler_mode=new_mode,
            expected_updated_at=expected_updated_at,
        )
        if not success:
            raise OCCConflictError(conversation_id)

        # Re-fetch updated conversation
        updated_conv = await self._conv_repo.get_by_id(
            id=conversation_id,
            tenant_id=tenant_id,
            scope_id=clinic_id,
        )
        if updated_conv is None:
            raise ConversationNotFoundError(conversation_id)

        now = datetime.now(UTC)

        # Audit log sync write (HIPAA-lite: mandatory pre-response)
        await self._audit_writer.write(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            user_id=changed_by_user_id,
            action="inbox.conversation.mode_changed",
            resource_type="inbox.conversation",
            resource_id=conversation_id,
            payload={
                "from_mode": from_mode,
                "to_mode": new_mode,
                "proposal_required": proposal_required,
            },
        )

        # Emit ModeChanged event via outbox bus
        event = ModeChanged(
            event_name="mode_changed",
            tenant_id=tenant_id,
            conversation_id=conversation_id,
            clinic_id=clinic_id,
            previous_handler_mode=from_mode,
            new_handler_mode=new_mode,
            previous_updated_at=expected_updated_at,
            occurred_at=now,
        )
        await self._event_bus.publish(event, session=self._session)

        logger.info(
            "set_mode.success",
            tenant_id=str(tenant_id),
            conversation_id=str(conversation_id),
            from_mode=from_mode,
            to_mode=new_mode,
        )

        return SetModeResult(
            conversation_id=conversation_id,
            handler_mode=updated_conv.handler_mode,
            proposal_required=proposal_required,
            status=updated_conv.status,
            pause_until=updated_conv.pause_until,
            help_needed=updated_conv.help_needed,
            updated_at=updated_conv.updated_at,
        )
