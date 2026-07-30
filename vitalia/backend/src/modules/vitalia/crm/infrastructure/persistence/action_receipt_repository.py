# cap: crm.crm-consent-optout
# story-origin: TBD
"""ActionReceiptRepository — dual-scope async repository (T-inbox-be-2).

Inherits CompoundScopeRepositoryBase with scope_field="clinic_id" to enforce
the HIPAA-lite dual filter: tenant_id AND clinic_id on every query.

Custom methods:
- create():                 persist new action receipt for AI message
- get_active_for_message(): find active (non-retracted, non-expired) receipt
- mark_retracted():         update retraction state (5min undo SC-01)

PHI obligations (hipaa-lite.md § Regla cardinal):
1. tenant_id + clinic_id dual filter mandatory (via CompoundScopeRepositoryBase)
2. Retraction state changes logged by service layer

SC-01 Action Receipts: AI messages get a receipt with 5min countdown.
State transitions enforced at service layer (repository only persists state).

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

from src.modules.vitalia.crm.infrastructure.persistence.models.action_receipt_model import (
    ActionReceiptModel,
)

logger = structlog.get_logger()


class ActionReceiptRepository(CompoundScopeRepositoryBase[ActionReceiptModel, UUID]):
    """Async repository for vitalia_action_receipts.

    Dual-scope isolation: tenant_id + clinic_id (scope_field='clinic_id').
    Every query automatically filters both axes + excludes soft-deleted rows.

    Note: ActionReceiptModel has no deleted_at column (receipts are immutable
    state machines). The base get_by_id excludes deleted_at IS NULL — model
    must have the attribute for the base to work (handled by None default
    in the base query; if attribute missing, SQLA will raise AttributeError
    which is the expected behavior per MissingScopeFieldError pattern).
    """

    MODEL = ActionReceiptModel

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize with clinic_id as the secondary scope axis.

        Args:
            session: Async SQLAlchemy session (injected by DI).
        """
        super().__init__(session=session, scope_field="clinic_id")

    async def create(
        self,
        *,
        message_id: UUID,
        conversation_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        expires_at: datetime,
    ) -> ActionReceiptModel:
        """Persist a new action receipt for an AI message.

        Called by SendMessageService when sender_type == 'agent_ai'.
        The receipt enables the 5-minute undo window (SC-01).

        PHI dual filter: tenant_id AND clinic_id mandatory.

        Args:
            message_id: UUID of the AI message this receipt belongs to.
            conversation_id: Parent conversation UUID.
            tenant_id: Root tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite second scope filter).
            expires_at: Absolute expiry timestamp (sent_at + 5 minutes).

        Returns:
            Created ActionReceiptModel instance.
        """
        now = datetime.now(tz=timezone.utc)
        row = ActionReceiptModel(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            message_id=message_id,
            conversation_id=conversation_id,
            expires_at=expires_at,
            retracted_at=None,
            retract_succeeded=None,
            retract_reason=None,
            created_at=now,
            updated_at=now,
        )
        self._session.add(row)
        await self._session.flush()
        logger.info(
            "action_receipt_repo.create",
            receipt_id=str(row.id),
            message_id=str(message_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            expires_at=expires_at.isoformat(),
        )
        return row

    async def get_active_for_message(
        self,
        *,
        message_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> ActionReceiptModel | None:
        """Find the active (non-retracted, not expired) receipt for a message.

        An active receipt has:
        - retracted_at IS NULL (not yet retracted)
        - expires_at > now() (within the 5min window)

        PHI dual filter applied: tenant_id AND clinic_id mandatory.

        Args:
            message_id: UUID of the AI message.
            tenant_id:  Root tenant UUID.
            clinic_id:  Clinic UUID (HIPAA-lite second scope filter).

        Returns:
            ActionReceiptModel if an active receipt exists, else None.
        """
        scope_attr = self._scope_attr()
        now = datetime.now(tz=timezone.utc)
        stmt = (
            select(ActionReceiptModel)
            .where(ActionReceiptModel.message_id == message_id)
            .where(ActionReceiptModel.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(ActionReceiptModel.retracted_at.is_(None))
            .where(ActionReceiptModel.expires_at > now)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        logger.debug(
            "action_receipt_repo.get_active_for_message",
            message_id=str(message_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            found=row is not None,
        )
        return row

    async def mark_retracted(
        self,
        *,
        receipt_id: UUID,
        tenant_id: UUID,
        clinic_id: UUID,
        retract_succeeded: bool,
        retract_reason: str,
    ) -> bool:
        """Mark an action receipt as retracted with the given outcome.

        Updates retracted_at, retract_succeeded, retract_reason, and updated_at.
        PHI dual filter applied: only updates row with matching tenant_id AND clinic_id.

        Args:
            receipt_id:        UUID of the action receipt.
            tenant_id:         Root tenant UUID.
            clinic_id:         Clinic UUID (HIPAA-lite second scope filter).
            retract_succeeded: True if WA/IG retract API call succeeded.
                               False = fallback 'marcar erróneo' (e.g. email channel).
            retract_reason:    Reason string (e.g. 'user_undo', 'expired').

        Returns:
            True if the row was updated (rowcount == 1).
            False if not found, already retracted, or wrong tenant/clinic.
        """
        scope_attr = self._scope_attr()
        now = datetime.now(tz=timezone.utc)
        stmt = (
            update(ActionReceiptModel)
            .where(ActionReceiptModel.id == receipt_id)
            .where(ActionReceiptModel.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(ActionReceiptModel.retracted_at.is_(None))  # prevent double retraction
            .values(
                retracted_at=now,
                retract_succeeded=retract_succeeded,
                retract_reason=retract_reason,
                updated_at=now,
            )
        )
        result = await self._session.execute(stmt)
        success = result.rowcount == 1  # type: ignore[union-attr]
        logger.info(
            "action_receipt_repo.mark_retracted",
            receipt_id=str(receipt_id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            retract_succeeded=retract_succeeded,
            retract_reason=retract_reason,
            success=success,
        )
        return success
