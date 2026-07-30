# cap: crm.crm-consent-optout
# story-origin: TBD
"""ConversationRepository — dual-scope async repository (T-inbox-be-2).

Inherits CompoundScopeRepositoryBase with scope_field="clinic_id" to enforce
the HIPAA-lite dual filter: tenant_id AND clinic_id on every query.

Custom methods:
- list_for_inbox():           inbox list with filtering/ordering/pagination
- update_handler_mode():      OCC update (returns False on conflict, True on success)
- get_or_create_for_lead():   idempotent upsert for proactive outbound

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter mandatory (via CompoundScopeRepositoryBase)
2. Audit log row: written by service layer (not repository)
3. Sanitization: no PHI in traces (structlog with entity IDs only)
4. Encryption in transit: handled by infra (HTTPS + mTLS)

downstream-regression-na: brand-local vitalia CRM infrastructure repo
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import structlog
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.crm.infrastructure.persistence.models.conversation_model import (
    ConversationModel,
)

logger = structlog.get_logger()


class ConversationRepository(CompoundScopeRepositoryBase[ConversationModel, UUID]):
    """Async repository for vitalia_conversations.

    Dual-scope isolation: tenant_id + clinic_id (scope_field='clinic_id').
    Every query automatically filters both axes + excludes soft-deleted rows.
    """

    MODEL = ConversationModel

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize with clinic_id as the secondary scope axis.

        Args:
            session: Async SQLAlchemy session (injected by DI).
        """
        super().__init__(session=session, scope_field="clinic_id")

    async def list_for_inbox(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        status: str | None = None,
        channel: str | None = None,
        handler_mode: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ConversationModel]:
        """List conversations for the inbox view with optional filters.

        Applies PHI dual filter (tenant_id + clinic_id) on every call.
        Results ordered by last_message_at DESC (most recent first).

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            status:       Optional status filter (e.g. 'open', 'closed').
            channel:      Optional channel filter (e.g. 'whatsapp', 'instagram').
            handler_mode: Optional handler_mode filter (e.g. 'ai', 'human').
            limit:        Page size. Default 20.
            offset:       Page offset. Default 0.

        Returns:
            List of ConversationModel instances, ordered by last_message_at DESC.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(ConversationModel)
            .where(ConversationModel.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(ConversationModel.deleted_at.is_(None))
        )
        if status is not None:
            stmt = stmt.where(ConversationModel.status == status)
        if channel is not None:
            stmt = stmt.where(ConversationModel.channel == channel)
        if handler_mode is not None:
            stmt = stmt.where(ConversationModel.handler_mode == handler_mode)

        stmt = stmt.order_by(ConversationModel.last_message_at.desc().nullslast()).offset(offset).limit(limit)

        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        logger.debug(
            "conversation_repo.list_for_inbox",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            count=len(rows),
        )
        return rows

    async def update_handler_mode(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        new_handler_mode: str,
        expected_updated_at: datetime,
    ) -> bool:
        """Update handler_mode with Optimistic Concurrency Control (OCC).

        Uses expected_updated_at to detect concurrent modifications. If the
        row's updated_at differs from expected_updated_at (i.e., concurrent
        update occurred), returns False without making changes.

        PHI dual filter applied: only updates row with matching
        tenant_id AND clinic_id (prevents cross-tenant/clinic updates).

        Args:
            conversation_id:   UUID of the conversation to update.
            tenant_id:         Root tenant UUID.
            clinic_id:         Clinic UUID (HIPAA-lite second scope filter).
            new_handler_mode:  New handler mode value (e.g. 'ai', 'human').
            expected_updated_at: The updated_at value the caller last read.
                               If the DB row has a different value, the update
                               is skipped (OCC conflict).

        Returns:
            True if the update was applied (rowcount == 1).
            False if OCC conflict or row not found (rowcount == 0).
        """
        scope_attr = self._scope_attr()
        now = datetime.now(tz=timezone.utc)

        stmt = (
            update(ConversationModel)
            .where(ConversationModel.id == conversation_id)
            .where(ConversationModel.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(ConversationModel.deleted_at.is_(None))
            .where(ConversationModel.updated_at == expected_updated_at)
            .values(handler_mode=new_handler_mode, updated_at=now)
        )
        result = await self._session.execute(stmt)
        success = result.rowcount == 1  # type: ignore[union-attr]
        logger.info(
            "conversation_repo.update_handler_mode",
            conversation_id=str(conversation_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            new_handler_mode=new_handler_mode,
            occ_success=success,
        )
        return success

    async def set_pause_until(
        self,
        *,
        conversation_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        pause_until: datetime,
    ) -> ConversationModel | None:
        """Persist pause_until for a conversation and return the updated row.

        Used by PauseAdrianService. PHI dual filter (tenant_id + clinic_id).
        No OCC — pausing is idempotent (last writer wins). Returns the refreshed
        row so the caller can build its response; None if the row is gone.
        """
        scope_attr = self._scope_attr()
        now = datetime.now(tz=timezone.utc)

        await self._session.execute(
            update(ConversationModel)
            .where(ConversationModel.id == conversation_id)
            .where(ConversationModel.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(ConversationModel.deleted_at.is_(None))
            .values(pause_until=pause_until, updated_at=now)
        )
        result = await self._session.execute(
            select(ConversationModel)
            .where(ConversationModel.id == conversation_id)
            .where(ConversationModel.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(ConversationModel.deleted_at.is_(None))
        )
        conv = result.scalar_one_or_none()
        logger.info(
            "conversation_repo.set_pause_until",
            conversation_id=str(conversation_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            pause_until=pause_until.isoformat(),
        )
        return conv

    async def get_or_create_for_lead(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        lead_id: UUID,
        channel: str,
    ) -> ConversationModel:
        """Get existing open conversation for a lead or create a new one.

        Idempotent: returns existing open conversation if found, otherwise
        creates a new conversation record. Used by ProactiveOutboundService
        to ensure a conversation context exists before sending an HSM message.

        PHI dual filter applied: tenant_id AND clinic_id mandatory.

        Args:
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            lead_id: Target lead UUID.
            channel: Channel for the conversation (e.g. 'whatsapp').

        Returns:
            Existing or newly-created ConversationModel.
        """
        scope_attr = self._scope_attr()
        # Try to find an existing open conversation for this lead+channel
        stmt = (
            select(ConversationModel)
            .where(ConversationModel.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(ConversationModel.lead_id == lead_id)
            .where(ConversationModel.channel == channel)
            .where(ConversationModel.status == "open")
            .where(ConversationModel.deleted_at.is_(None))
            .order_by(ConversationModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing is not None:
            logger.debug(
                "conversation_repo.get_or_create_for_lead.found_existing",
                conversation_id=str(existing.id),
                lead_id=str(lead_id),
                tenant_id=str(tenant_id),
                clinic_id=str(clinic_id),
            )
            return existing

        now = datetime.now(tz=timezone.utc)
        row = ConversationModel(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            lead_id=lead_id,
            channel=channel,
            status="open",
            handler_mode="ai",
            proposal_required=False,
            help_needed=False,
            unread_media_count=0,
            messages_count=0,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.flush()
        logger.info(
            "conversation_repo.get_or_create_for_lead.created",
            conversation_id=str(row.id),
            lead_id=str(lead_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            channel=channel,
        )
        return row
