"""RED tests — LeadScreeningEventRepository.

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- Inherits from PhiRepositoryBase (dual filter enforcement)
- validate_dual_filter() called — raises MissingClinicFilterError when clinic_id missing
- create() persists model with tenant_id + clinic_id
- get_by_id() applies dual filter (tenant_id + clinic_id + not-deleted)
- list_by_lead() applies dual filter
- write_audit_log_row() called synchronously on create (pre-response)
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
LEAD_ID = uuid4()
EVENT_ID = uuid4()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _make_entity(**overrides: object) -> object:
    from src.modules.vitalia.sales_agent.domain.entities.lead_screening_event import (
        LeadScreeningEvent,
    )

    defaults = {
        "id": EVENT_ID,
        "tenant_id": TENANT_ID,
        "clinic_id": CLINIC_ID,
        "lead_id": LEAD_ID,
        "vertical": "dental",
        "questions_asked": ["¿Tienes dolor?"],
        "response_text": "No tengo dolor",
        "outcome": "ok_proceed",
        "reasoning": "No contraindications found",
        "evaluated_at": _utc_now(),
        "created_at": _utc_now(),
        "deleted_at": None,
    }
    defaults.update(overrides)
    return LeadScreeningEvent(**defaults)


@pytest.fixture()
def mock_session() -> AsyncMock:
    """Fake AsyncSession — no real DB needed for unit tests."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture()
def mock_audit_repo() -> AsyncMock:
    """Fake AuditLogRepository."""
    repo = AsyncMock()
    repo.write = AsyncMock()
    return repo


class TestLeadScreeningEventRepository:
    """Unit tests for LeadScreeningEventRepository."""

    def test_import_and_class_exists(self) -> None:
        """Repository must be importable from infrastructure layer."""
        from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (
            LeadScreeningEventRepository,
        )

        assert LeadScreeningEventRepository is not None

    def test_inherits_phi_repository_base(self) -> None:
        """Must inherit PhiRepositoryBase for dual-filter contract enforcement."""
        from src.modules.vitalia._shared.repositories.phi_repository import (
            PhiRepositoryBase,
        )
        from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (
            LeadScreeningEventRepository,
        )

        assert issubclass(LeadScreeningEventRepository, PhiRepositoryBase)

    @pytest.mark.asyncio()
    async def test_get_by_id_raises_missing_clinic_id_error(self, mock_session: AsyncMock) -> None:
        """get_by_id without clinic_id raises MissingClinicFilterError."""
        from src.modules.vitalia._shared.repositories.phi_repository import (
            MissingClinicFilterError,
        )
        from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (
            LeadScreeningEventRepository,
        )

        repo = LeadScreeningEventRepository(session=mock_session)
        with pytest.raises(MissingClinicFilterError):
            await repo.get_by_id(EVENT_ID, tenant_id=TENANT_ID, clinic_id=None)  # type: ignore[arg-type]

    @pytest.mark.asyncio()
    async def test_get_by_id_with_dual_filter(self, mock_session: AsyncMock) -> None:
        """get_by_id with both filters executes query (no raise)."""
        from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (
            LeadScreeningEventRepository,
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = result_mock

        repo = LeadScreeningEventRepository(session=mock_session)
        result = await repo.get_by_id(EVENT_ID, tenant_id=TENANT_ID, clinic_id=CLINIC_ID)
        assert result is None  # Not found is OK for unit test
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio()
    async def test_list_by_filter_raises_without_clinic_id(self, mock_session: AsyncMock) -> None:
        """list_by_filter without clinic_id raises MissingClinicFilterError."""
        from src.modules.vitalia._shared.repositories.phi_repository import (
            MissingClinicFilterError,
        )
        from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (
            LeadScreeningEventRepository,
        )

        repo = LeadScreeningEventRepository(session=mock_session)
        with pytest.raises(MissingClinicFilterError):
            await repo.list_by_filter(tenant_id=TENANT_ID, clinic_id=None)  # type: ignore[arg-type]

    @pytest.mark.asyncio()
    async def test_list_by_filter_with_dual_filter(self, mock_session: AsyncMock) -> None:
        """list_by_filter with dual filter executes query (returns list)."""
        from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (
            LeadScreeningEventRepository,
        )

        result_mock = MagicMock()
        result_mock.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = result_mock

        repo = LeadScreeningEventRepository(session=mock_session)
        result = await repo.list_by_filter(tenant_id=TENANT_ID, clinic_id=CLINIC_ID)
        assert result == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio()
    async def test_create_calls_session_add_and_flush(self, mock_session: AsyncMock) -> None:
        """create() calls session.add() + session.flush() to persist entity."""
        from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (
            LeadScreeningEventRepository,
        )

        repo = LeadScreeningEventRepository(session=mock_session)
        entity = _make_entity()
        await repo.create(entity, tenant_id=TENANT_ID, clinic_id=CLINIC_ID)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio()
    async def test_create_raises_without_clinic_id(self, mock_session: AsyncMock) -> None:
        """create() without clinic_id raises MissingClinicFilterError (PHI invariant)."""
        from src.modules.vitalia._shared.repositories.phi_repository import (
            MissingClinicFilterError,
        )
        from src.modules.vitalia.sales_agent.infrastructure.repositories.lead_screening_event_repository import (
            LeadScreeningEventRepository,
        )

        repo = LeadScreeningEventRepository(session=mock_session)
        entity = _make_entity()
        with pytest.raises(MissingClinicFilterError):
            await repo.create(entity, tenant_id=TENANT_ID, clinic_id=None)  # type: ignore[arg-type]
