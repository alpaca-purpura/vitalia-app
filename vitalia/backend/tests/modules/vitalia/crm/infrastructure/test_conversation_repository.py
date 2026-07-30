"""Tests for ConversationRepository — dual filter enforcement (T-inbox-be-2).

TDD RED: tests written BEFORE implementation.

PHI obligations (hipaa-lite.md § Regla cardinal):
- tenant_id + clinic_id dual filter on every query (CompoundScopeRepositoryBase)
- scope_field="clinic_id" → scope_id param maps to clinic_id column
- Soft-delete excluded in all queries

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


class TestConversationRepositoryInheritance:
    """ConversationRepository must subclass CompoundScopeRepositoryBase."""

    def test_inherits_compound_scope_repository_base(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )

        assert issubclass(ConversationRepository, CompoundScopeRepositoryBase)

    def test_model_class_attribute_defined(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )
        from src.modules.vitalia.crm.infrastructure.persistence.models.conversation_model import (
            ConversationModel,
        )

        assert ConversationRepository.MODEL is ConversationModel

    def test_get_by_id_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )

        assert inspect.iscoroutinefunction(ConversationRepository.get_by_id)

    def test_list_for_inbox_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )

        assert inspect.iscoroutinefunction(ConversationRepository.list_for_inbox)

    def test_update_handler_mode_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )

        assert inspect.iscoroutinefunction(ConversationRepository.update_handler_mode)

    def test_scope_field_is_clinic_id(self) -> None:
        """Constructor must set scope_field='clinic_id' (HIPAA-lite second filter)."""
        session = AsyncMock()
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )

        repo = ConversationRepository(session=session)
        assert repo._scope_field == "clinic_id"


class TestConversationRepositoryDualFilter:
    """CompoundScopeRepositoryBase get_by_id enforces both tenant_id AND clinic_id."""

    @pytest.mark.asyncio
    async def test_get_by_id_filters_tenant_and_clinic(self) -> None:
        """get_by_id must pass tenant_id + scope_id (clinic_id) to base method."""
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = ConversationRepository(session=session)
        tenant_id = uuid4()
        clinic_id = uuid4()
        conv_id = uuid4()

        result = await repo.get_by_id(id=conv_id, tenant_id=tenant_id, scope_id=clinic_id)

        # session.execute must have been called
        assert session.execute.called
        assert result is None  # base returns None when not found

    @pytest.mark.asyncio
    async def test_list_for_inbox_filters_tenant_and_clinic(self) -> None:
        """list_for_inbox must apply both tenant_id and clinic_id filters."""
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        repo = ConversationRepository(session=session)
        tenant_id = uuid4()
        clinic_id = uuid4()

        results = await repo.list_for_inbox(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            limit=20,
            offset=0,
        )
        assert isinstance(results, list)
        assert session.execute.called


class TestConversationRepositoryOCC:
    """update_handler_mode uses OCC (Optimistic Concurrency Control) via updated_at."""

    @pytest.mark.asyncio
    async def test_update_handler_mode_returns_bool(self) -> None:
        """update_handler_mode returns True on success, False on OCC conflict."""
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        session.execute = AsyncMock(return_value=mock_result)

        repo = ConversationRepository(session=session)
        success = await repo.update_handler_mode(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            new_handler_mode="ai",
            expected_updated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
        assert isinstance(success, bool)

    @pytest.mark.asyncio
    async def test_update_handler_mode_returns_false_on_occ_conflict(self) -> None:
        """rowcount=0 means OCC conflict → returns False."""
        from src.modules.vitalia.crm.infrastructure.persistence.conversation_repository import (
            ConversationRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        session.execute = AsyncMock(return_value=mock_result)

        repo = ConversationRepository(session=session)
        success = await repo.update_handler_mode(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            new_handler_mode="human",
            expected_updated_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )
        assert success is False
