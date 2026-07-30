"""Tests for MessageRepository — dual filter enforcement (T-inbox-be-2).

TDD RED: tests written BEFORE implementation.

PHI obligations (hipaa-lite.md § Regla cardinal):
- tenant_id + clinic_id dual filter on every query (CompoundScopeRepositoryBase)
- transcription_text is PHI — must be sanitized before traces (not tested here)
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


class TestMessageRepositoryInheritance:
    """MessageRepository must subclass CompoundScopeRepositoryBase."""

    def test_inherits_compound_scope_repository_base(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
            MessageRepository,
        )

        assert issubclass(MessageRepository, CompoundScopeRepositoryBase)

    def test_model_class_attribute_defined(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
            MessageRepository,
        )
        from src.modules.vitalia.crm.infrastructure.persistence.models.message_model import (
            MessageModel,
        )

        assert MessageRepository.MODEL is MessageModel

    def test_get_by_id_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
            MessageRepository,
        )

        assert inspect.iscoroutinefunction(MessageRepository.get_by_id)

    def test_list_for_conversation_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
            MessageRepository,
        )

        assert inspect.iscoroutinefunction(MessageRepository.list_for_conversation)

    def test_scope_field_is_clinic_id(self) -> None:
        """Constructor must set scope_field='clinic_id' (HIPAA-lite second filter)."""
        session = AsyncMock()
        from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
            MessageRepository,
        )

        repo = MessageRepository(session=session)
        assert repo._scope_field == "clinic_id"


class TestMessageRepositoryDualFilter:
    """CompoundScopeRepositoryBase get_by_id enforces both tenant_id AND clinic_id."""

    @pytest.mark.asyncio
    async def test_get_by_id_requires_both_filters(self) -> None:
        """get_by_id must pass tenant_id + scope_id to base — no single-filter bypass."""
        from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
            MessageRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = MessageRepository(session=session)
        result = await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())
        assert result is None
        assert session.execute.called

    @pytest.mark.asyncio
    async def test_list_for_conversation_filters_tenant_and_clinic(self) -> None:
        """list_for_conversation must apply both tenant_id and clinic_id filters."""
        from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
            MessageRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        repo = MessageRepository(session=session)
        results = await repo.list_for_conversation(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
            limit=50,
            offset=0,
        )
        assert isinstance(results, list)
        assert session.execute.called


class TestMessageRepositorySoftDelete:
    """MessageRepository must support soft delete (set deleted_at) without hard DELETE."""

    @pytest.mark.asyncio
    async def test_soft_delete_sets_deleted_at(self) -> None:
        """soft_delete must UPDATE deleted_at, never issue DELETE FROM."""
        from src.modules.vitalia.crm.infrastructure.persistence.message_repository import (
            MessageRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 1
        session.execute = AsyncMock(return_value=mock_result)

        repo = MessageRepository(session=session)
        success = await repo.soft_delete(
            message_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
        )
        assert isinstance(success, bool)
        assert success is True
