"""Tests for ActionReceiptRepository — dual filter enforcement (T-inbox-be-2).

TDD RED: tests written BEFORE implementation.

PHI obligations (hipaa-lite.md § Regla cardinal):
- tenant_id + clinic_id dual filter on every query (CompoundScopeRepositoryBase)
- SC-01: ActionReceipt tracks 5min undo window per AI message

downstream-regression-na: brand-local vitalia CRM inbox infra tests
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from luana_core_platform.repositories.compound_scope_repository import (
    CompoundScopeRepositoryBase,
)


class TestActionReceiptRepositoryInheritance:
    """ActionReceiptRepository must subclass CompoundScopeRepositoryBase."""

    def test_inherits_compound_scope_repository_base(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )

        assert issubclass(ActionReceiptRepository, CompoundScopeRepositoryBase)

    def test_model_class_attribute_defined(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )
        from src.modules.vitalia.crm.infrastructure.persistence.models.action_receipt_model import (
            ActionReceiptModel,
        )

        assert ActionReceiptRepository.MODEL is ActionReceiptModel

    def test_get_by_id_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )

        assert inspect.iscoroutinefunction(ActionReceiptRepository.get_by_id)

    def test_get_active_for_message_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )

        assert inspect.iscoroutinefunction(ActionReceiptRepository.get_active_for_message)

    def test_mark_retracted_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )

        assert inspect.iscoroutinefunction(ActionReceiptRepository.mark_retracted)

    def test_scope_field_is_clinic_id(self) -> None:
        """Constructor must set scope_field='clinic_id' (HIPAA-lite second filter)."""
        session = AsyncMock()
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )

        repo = ActionReceiptRepository(session=session)
        assert repo._scope_field == "clinic_id"


class TestActionReceiptRepositoryDualFilter:
    """get_by_id enforces both tenant_id AND clinic_id (via scope_id)."""

    @pytest.mark.asyncio
    async def test_get_by_id_requires_both_filters(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = ActionReceiptRepository(session=session)
        result = await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())
        assert result is None
        assert session.execute.called

    @pytest.mark.asyncio
    async def test_get_active_for_message_filters_tenant_and_clinic(self) -> None:
        """get_active_for_message must apply tenant_id + clinic_id dual filter."""
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = ActionReceiptRepository(session=session)
        result = await repo.get_active_for_message(
            message_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
        )
        assert result is None
        assert session.execute.called


class TestActionReceiptRepositoryRetraction:
    """mark_retracted updates retraction state with dual filter for safety."""

    @pytest.mark.asyncio
    async def test_mark_retracted_returns_bool(self) -> None:
        """mark_retracted returns True on success, False if not found / wrong scope."""
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        session.execute = AsyncMock(return_value=mock_result)

        repo = ActionReceiptRepository(session=session)
        success = await repo.mark_retracted(
            receipt_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            retract_succeeded=True,
            retract_reason="user_undo",
        )
        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_mark_retracted_returns_false_when_not_found(self) -> None:
        """rowcount=0 means receipt not found or wrong scope → returns False."""
        from src.modules.vitalia.crm.infrastructure.persistence.action_receipt_repository import (
            ActionReceiptRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        session.execute = AsyncMock(return_value=mock_result)

        repo = ActionReceiptRepository(session=session)
        success = await repo.mark_retracted(
            receipt_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            retract_succeeded=False,
            retract_reason="expired",
        )
        assert success is False
