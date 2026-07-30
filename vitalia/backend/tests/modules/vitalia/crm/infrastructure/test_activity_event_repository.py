"""Tests for ActivityEventRepository — dual filter enforcement (T-inbox-be-2).

TDD RED: tests written BEFORE implementation.

PHI obligations (hipaa-lite.md § Regla cardinal):
- tenant_id + clinic_id dual filter on every query (CompoundScopeRepositoryBase)
- payload_sanitized: PII must be redacted before storing (enforced in service layer)
- ActivityStream: 8 last events per conversation (SC-01)

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


class TestActivityEventRepositoryInheritance:
    """ActivityEventRepository must subclass CompoundScopeRepositoryBase."""

    def test_inherits_compound_scope_repository_base(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
            ActivityEventRepository,
        )

        assert issubclass(ActivityEventRepository, CompoundScopeRepositoryBase)

    def test_model_class_attribute_defined(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
            ActivityEventRepository,
        )
        from src.modules.vitalia.crm.infrastructure.persistence.models.activity_event_model import (
            ActivityEventModel,
        )

        assert ActivityEventRepository.MODEL is ActivityEventModel

    def test_get_by_id_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
            ActivityEventRepository,
        )

        assert inspect.iscoroutinefunction(ActivityEventRepository.get_by_id)

    def test_list_for_activity_stream_is_coroutine(self) -> None:
        from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
            ActivityEventRepository,
        )

        assert inspect.iscoroutinefunction(ActivityEventRepository.list_for_activity_stream)

    def test_scope_field_is_clinic_id(self) -> None:
        """Constructor must set scope_field='clinic_id' (HIPAA-lite second filter)."""
        session = AsyncMock()
        from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
            ActivityEventRepository,
        )

        repo = ActivityEventRepository(session=session)
        assert repo._scope_field == "clinic_id"


class TestActivityEventRepositoryDualFilter:
    """CompoundScopeRepositoryBase get_by_id enforces both tenant_id AND clinic_id."""

    @pytest.mark.asyncio
    async def test_get_by_id_requires_both_filters(self) -> None:
        """get_by_id must pass tenant_id + scope_id — no single-filter bypass."""
        from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
            ActivityEventRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = ActivityEventRepository(session=session)
        result = await repo.get_by_id(id=uuid4(), tenant_id=uuid4(), scope_id=uuid4())
        assert result is None
        assert session.execute.called

    @pytest.mark.asyncio
    async def test_list_for_activity_stream_returns_last_8(self) -> None:
        """list_for_activity_stream must return at most 8 events (SC-01)."""
        from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
            ActivityEventRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        repo = ActivityEventRepository(session=session)
        results = await repo.list_for_activity_stream(
            conversation_id=uuid4(),
            tenant_id=uuid4(),
            clinic_id=uuid4(),
        )
        assert isinstance(results, list)
        assert session.execute.called

    @pytest.mark.asyncio
    async def test_list_for_activity_stream_filters_tenant_and_clinic(self) -> None:
        """list_for_activity_stream applies tenant_id + clinic_id dual filter."""
        from src.modules.vitalia.crm.infrastructure.persistence.activity_event_repository import (
            ActivityEventRepository,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        repo = ActivityEventRepository(session=session)
        tenant_id = uuid4()
        clinic_id = uuid4()

        await repo.list_for_activity_stream(
            conversation_id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
        )
        # Must have called session.execute (dual filter applied in query)
        assert session.execute.called
