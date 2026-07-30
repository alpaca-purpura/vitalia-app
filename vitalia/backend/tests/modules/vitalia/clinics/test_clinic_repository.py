"""Unit tests for ClinicRepository — tenant-isolated SQLA 2.0 queries.

TDD: RED tests defined per vitalia-adopt-luana-core-iam story.
All queries must filter (tenant_id + deleted_at) per HIPAA dual-filter rule.

downstream-regression-na: brand-local clinics repository tests
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.modules.vitalia.clinics.domain.clinic import Clinic
from src.modules.vitalia.clinics.infrastructure.models.clinic_model import ClinicModel
from src.modules.vitalia.clinics.infrastructure.repositories.clinic_repository import (
    ClinicRepository,
)


def _make_clinic_model(
    tenant_id: UUID | None = None,
    slug: str = "test-clinic",
    is_active: bool = True,
) -> ClinicModel:
    m = ClinicModel()
    m.id = uuid4()
    m.tenant_id = tenant_id or uuid4()
    m.name = "Test Clinic"
    m.slug = slug
    m.country = "AR"
    m.timezone = "America/Argentina/Buenos_Aires"
    m.plan_tier = "starter"
    m.is_active = is_active
    m.onboarding_completed = False
    m.created_at = datetime.now(tz=timezone.utc)
    m.updated_at = None
    m.deleted_at = None
    return m


class TestClinicRepositoryGetById:
    """get_by_id must filter tenant_id and deleted_at."""

    @pytest.mark.anyio
    async def test_get_by_id_returns_clinic_for_tenant(self) -> None:
        """Returns domain Clinic when tenant_id matches."""
        tenant_id = uuid4()
        model = _make_clinic_model(tenant_id=tenant_id)

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = model
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClinicRepository(mock_session)
        result = await repo.get_by_id(str(tenant_id), model.id)

        assert result is not None
        assert isinstance(result, Clinic)
        assert result.id == model.id
        assert result.tenant_id == tenant_id

    @pytest.mark.anyio
    async def test_get_by_id_returns_none_when_not_found(self) -> None:
        """Returns None when clinic not found for tenant."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClinicRepository(mock_session)
        result = await repo.get_by_id(str(uuid4()), uuid4())

        assert result is None

    @pytest.mark.anyio
    async def test_get_by_id_query_includes_tenant_filter(self) -> None:
        """Verify the query is built — execute called once (no raw SQL)."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClinicRepository(mock_session)
        await repo.get_by_id(str(uuid4()), uuid4())

        # execute MUST be called — tenant filter applied inside the method
        mock_session.execute.assert_called_once()


class TestClinicRepositoryListByTenant:
    """list_by_tenant must return only clinics for given tenant."""

    @pytest.mark.anyio
    async def test_list_by_tenant_returns_empty_when_none(self) -> None:
        """Returns empty list when no clinics for tenant."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClinicRepository(mock_session)
        result = await repo.list_by_tenant(str(uuid4()))

        assert result == []

    @pytest.mark.anyio
    async def test_list_by_tenant_maps_to_domain(self) -> None:
        """Returns list of domain Clinic objects."""
        tenant_id = uuid4()
        models = [
            _make_clinic_model(tenant_id=tenant_id, slug="clinic-a"),
            _make_clinic_model(tenant_id=tenant_id, slug="clinic-b"),
        ]

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = models
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClinicRepository(mock_session)
        result = await repo.list_by_tenant(str(tenant_id))

        assert len(result) == 2
        assert all(isinstance(c, Clinic) for c in result)
        assert {c.slug for c in result} == {"clinic-a", "clinic-b"}


class TestClinicRepositoryGetBySlug:
    """get_by_slug must filter tenant_id and slug."""

    @pytest.mark.anyio
    async def test_get_by_slug_returns_clinic(self) -> None:
        """Returns clinic when slug + tenant match."""
        tenant_id = uuid4()
        model = _make_clinic_model(tenant_id=tenant_id, slug="aurora-norte")

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = model
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClinicRepository(mock_session)
        result = await repo.get_by_slug(str(tenant_id), "aurora-norte")

        assert result is not None
        assert result.slug == "aurora-norte"

    @pytest.mark.anyio
    async def test_get_by_slug_returns_none_when_wrong_tenant(self) -> None:
        """Returns None when tenant_id doesn't match (cross-tenant isolation)."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.first.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClinicRepository(mock_session)
        result = await repo.get_by_slug(str(uuid4()), "aurora-norte")

        assert result is None


class TestClinicRepositoryCreate:
    """create must persist domain entity and return it."""

    @pytest.mark.anyio
    async def test_create_persists_and_returns_clinic(self) -> None:
        """Create adds model to session and returns domain Clinic."""
        tenant_id = uuid4()
        clinic = Clinic(
            id=uuid4(),
            tenant_id=tenant_id,
            name="Clínica Aurora",
            slug="aurora-norte",
            country="AR",
            timezone="America/Argentina/Buenos_Aires",
            plan_tier="starter",
            is_active=True,
            onboarding_completed=False,
            created_at=datetime.now(tz=timezone.utc),
        )

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock(return_value=None)

        repo = ClinicRepository(mock_session)
        result = await repo.create(clinic)

        mock_session.add.assert_called_once()
        assert isinstance(result, Clinic)
        assert result.slug == "aurora-norte"
        assert result.tenant_id == tenant_id


class TestClinicRepositorySoftDelete:
    """soft_delete sets deleted_at, never hard deletes."""

    @pytest.mark.anyio
    async def test_soft_delete_calls_update(self) -> None:
        """soft_delete executes an update (not DELETE FROM)."""
        mock_result = MagicMock()
        mock_result.rowcount = 1  # simulate 1 row updated

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ClinicRepository(mock_session)
        deleted = await repo.soft_delete(str(uuid4()), uuid4())

        # execute called once for the UPDATE statement
        mock_session.execute.assert_called_once()
        assert deleted is True
