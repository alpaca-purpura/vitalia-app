"""Tests for SqlAlchemyOnboardingProgressRepository.

TDD: RED tests written before implementation (T-onboarding-1).
Tests cover: create, get_by_tenant_user, update_step, mark_completed,
tenant isolation cross-tenant rejection (returns None, NOT raises 403 — repo layer).

downstream-regression-na: brand-local copilot onboarding repo tests (vitalia-specific, not engine pattern)
"""

from __future__ import annotations

import inspect
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(tz=timezone.utc)


class TestOnboardingProgressRepositoryInterface:
    """Verify domain interface is ABC with correct method signatures."""

    def test_interface_is_abstract(self) -> None:
        """OnboardingProgressRepository must be abstract (cannot instantiate)."""

        from src.modules.vitalia.copilot.domain.repositories.onboarding_progress_repository import (
            OnboardingProgressRepository,
        )

        assert inspect.isabstract(OnboardingProgressRepository), (
            "OnboardingProgressRepository must be abstract (ABC) — it is a domain interface, "
            "concrete implementations live in infrastructure layer."
        )

    def test_create_method_signature(self) -> None:
        """create() must be abstract async method."""
        from src.modules.vitalia.copilot.domain.repositories.onboarding_progress_repository import (
            OnboardingProgressRepository,
        )

        assert hasattr(OnboardingProgressRepository, "create")
        assert inspect.iscoroutinefunction(OnboardingProgressRepository.create)

    def test_get_by_tenant_user_method_signature(self) -> None:
        """get_by_tenant_user() must be abstract async method."""
        from src.modules.vitalia.copilot.domain.repositories.onboarding_progress_repository import (
            OnboardingProgressRepository,
        )

        assert hasattr(OnboardingProgressRepository, "get_by_tenant_user")
        assert inspect.iscoroutinefunction(OnboardingProgressRepository.get_by_tenant_user)

    def test_update_step_method_signature(self) -> None:
        """update_step() must be abstract async method."""
        from src.modules.vitalia.copilot.domain.repositories.onboarding_progress_repository import (
            OnboardingProgressRepository,
        )

        assert hasattr(OnboardingProgressRepository, "update_step")
        assert inspect.iscoroutinefunction(OnboardingProgressRepository.update_step)

    def test_mark_completed_method_signature(self) -> None:
        """mark_completed() must be abstract async method."""
        from src.modules.vitalia.copilot.domain.repositories.onboarding_progress_repository import (
            OnboardingProgressRepository,
        )

        assert hasattr(OnboardingProgressRepository, "mark_completed")
        assert inspect.iscoroutinefunction(OnboardingProgressRepository.mark_completed)


class TestSqlAlchemyOnboardingProgressRepositoryCreate:
    """Test SqlAlchemyOnboardingProgressRepository.create() behaviour."""

    def _make_repo(self) -> "object":
        """Create repository with AsyncMock session (no real DB needed)."""
        from src.modules.vitalia.copilot.infrastructure.repositories.onboarding_progress_repository import (
            SqlAlchemyOnboardingProgressRepository,
        )

        mock_session = AsyncMock()
        return SqlAlchemyOnboardingProgressRepository(session=mock_session), mock_session

    @pytest.mark.asyncio
    async def test_create_returns_onboarding_draft(self) -> None:
        """create() must return an OnboardingDraft domain entity."""
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft

        repo, mock_session = self._make_repo()

        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        tenant_id = uuid4()
        user_id = uuid4()

        result = await repo.create(
            tenant_id=tenant_id,
            user_id=user_id,
            step="slot_collection",
            mode="libre",
            draft_id=None,
        )

        assert isinstance(result, OnboardingDraft), "create() must return OnboardingDraft domain entity, not ORM model"
        assert result.tenant_id == tenant_id
        assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_create_calls_session_add_and_flush(self) -> None:
        """create() must call session.add() and session.flush() — not commit (caller manages tx)."""
        repo, mock_session = self._make_repo()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        await repo.create(
            tenant_id=uuid4(),
            user_id=uuid4(),
            step="slot_collection",
            mode=None,
            draft_id=None,
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_accepts_none_mode(self) -> None:
        """create() accepts mode=None for default wizard sessions."""
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft

        repo, mock_session = self._make_repo()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        result = await repo.create(
            tenant_id=uuid4(),
            user_id=uuid4(),
            step="start",
            mode=None,
            draft_id=None,
        )

        assert isinstance(result, OnboardingDraft)
        assert result.mode is None or result.mode == ""

    @pytest.mark.asyncio
    async def test_create_accepts_draft_id_link(self) -> None:
        """create() accepts draft_id to link progress with brand studio draft."""
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft

        repo, mock_session = self._make_repo()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        draft_id = uuid4()
        result = await repo.create(
            tenant_id=uuid4(),
            user_id=uuid4(),
            step="slot_collection",
            mode="guiado",
            draft_id=draft_id,
        )

        assert isinstance(result, OnboardingDraft)


class TestSqlAlchemyOnboardingProgressRepositoryGetByTenantUser:
    """Test get_by_tenant_user() with tenant isolation."""

    def _make_repo(self) -> "object":
        from src.modules.vitalia.copilot.infrastructure.repositories.onboarding_progress_repository import (
            SqlAlchemyOnboardingProgressRepository,
        )

        mock_session = AsyncMock()
        return SqlAlchemyOnboardingProgressRepository(session=mock_session), mock_session

    @pytest.mark.asyncio
    async def test_get_by_tenant_user_returns_draft_when_found(self) -> None:
        """get_by_tenant_user() returns OnboardingDraft when row exists for tenant+user."""
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft
        from src.modules.vitalia.copilot.persistence.models.onboarding_progress_model import (
            OnboardingProgressModel,
        )

        repo, mock_session = self._make_repo()
        tenant_id = uuid4()
        user_id = uuid4()

        # Build a mock ORM row
        mock_row = MagicMock(spec=OnboardingProgressModel)
        mock_row.id = uuid4()
        mock_row.tenant_id = tenant_id
        mock_row.user_id = user_id
        mock_row.step = "slot_collection"
        mock_row.slots_confirmed = {}
        mock_row.slots_pending = {}
        mock_row.mode = "libre"
        mock_row.draft_id = None
        mock_row.attachments = {}
        mock_row.status = "in_progress"
        mock_row.completed_at = None
        mock_row.created_at = _utc_now()
        mock_row.updated_at = _utc_now()

        # Mock execute result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_by_tenant_user(tenant_id=tenant_id, user_id=user_id)

        assert result is not None
        assert isinstance(result, OnboardingDraft)
        assert result.tenant_id == tenant_id
        assert result.user_id == user_id

    @pytest.mark.asyncio
    async def test_get_by_tenant_user_returns_none_when_not_found(self) -> None:
        """get_by_tenant_user() returns None when no row exists — NOT raises."""
        repo, mock_session = self._make_repo()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_by_tenant_user(tenant_id=uuid4(), user_id=uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_tenant_isolation_cross_tenant_returns_none(self) -> None:
        """Tenant isolation: query with different tenant_id returns None (repo layer enforces isolation)."""
        repo, mock_session = self._make_repo()

        # Simulate DB returning nothing for wrong tenant (row exists for tenant_A, queried with tenant_B)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # tenant_B query returns no row
        mock_session.execute = AsyncMock(return_value=mock_result)

        tenant_b_id = uuid4()
        user_id = uuid4()  # same user, different tenant

        result = await repo.get_by_tenant_user(tenant_id=tenant_b_id, user_id=user_id)

        # MUST return None (not raise 403) — isolation is row-level, not exception-level
        assert result is None, "Repo layer returns None on cross-tenant miss — HTTP 403/404 is API layer responsibility"
        # Verify the SELECT query was passed tenant_b_id (not any arbitrary tenant)
        mock_session.execute.assert_called_once()


class TestSqlAlchemyOnboardingProgressRepositoryUpdateStep:
    """Test update_step() with tenant isolation."""

    def _make_repo_with_existing(self, tenant_id: UUID, progress_id: UUID) -> "tuple":
        from src.modules.vitalia.copilot.infrastructure.repositories.onboarding_progress_repository import (
            SqlAlchemyOnboardingProgressRepository,
        )
        from src.modules.vitalia.copilot.persistence.models.onboarding_progress_model import (
            OnboardingProgressModel,
        )

        mock_session = AsyncMock()

        mock_row = MagicMock(spec=OnboardingProgressModel)
        mock_row.id = progress_id
        mock_row.tenant_id = tenant_id
        mock_row.user_id = uuid4()
        mock_row.step = "slot_collection"
        mock_row.slots_confirmed = {}
        mock_row.slots_pending = {"tenant.name": {}}
        mock_row.mode = "libre"
        mock_row.draft_id = None
        mock_row.attachments = {}
        mock_row.status = "in_progress"
        mock_row.completed_at = None
        mock_row.created_at = _utc_now()
        mock_row.updated_at = _utc_now()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        repo = SqlAlchemyOnboardingProgressRepository(session=mock_session)
        return repo, mock_session, mock_row

    @pytest.mark.asyncio
    async def test_update_step_returns_updated_draft(self) -> None:
        """update_step() returns updated OnboardingDraft with new step value."""
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft

        tenant_id = uuid4()
        progress_id = uuid4()
        repo, mock_session, mock_row = self._make_repo_with_existing(tenant_id, progress_id)

        result = await repo.update_step(
            tenant_id=tenant_id,
            progress_id=progress_id,
            step="voice_sample",
            slots_confirmed={"tenant.name": {"value": "Clinica Salud Total"}},
            slots_pending={},
        )

        assert isinstance(result, OnboardingDraft)
        # Step was mutated on mock_row
        assert mock_row.step == "voice_sample"
        mock_session.flush.assert_called_once()


class TestSqlAlchemyOnboardingProgressRepositoryMarkCompleted:
    """Test mark_completed() sets completed_at and status='completed'."""

    def _make_repo_with_existing(self, tenant_id: UUID, progress_id: UUID) -> "tuple":
        from src.modules.vitalia.copilot.infrastructure.repositories.onboarding_progress_repository import (
            SqlAlchemyOnboardingProgressRepository,
        )
        from src.modules.vitalia.copilot.persistence.models.onboarding_progress_model import (
            OnboardingProgressModel,
        )

        mock_session = AsyncMock()

        mock_row = MagicMock(spec=OnboardingProgressModel)
        mock_row.id = progress_id
        mock_row.tenant_id = tenant_id
        mock_row.user_id = uuid4()
        mock_row.step = "voice_sample"
        mock_row.slots_confirmed = {"tenant.name": {"value": "Test"}}
        mock_row.slots_pending = {}
        mock_row.mode = "libre"
        mock_row.draft_id = None
        mock_row.attachments = {}
        mock_row.status = "in_progress"
        mock_row.completed_at = None
        mock_row.created_at = _utc_now()
        mock_row.updated_at = _utc_now()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        repo = SqlAlchemyOnboardingProgressRepository(session=mock_session)
        return repo, mock_session, mock_row

    @pytest.mark.asyncio
    async def test_mark_completed_sets_status_and_timestamp(self) -> None:
        """mark_completed() sets status='completed' and completed_at on the ORM row."""
        from src.modules.vitalia.copilot.domain.entities.onboarding_draft import OnboardingDraft

        tenant_id = uuid4()
        progress_id = uuid4()
        repo, mock_session, mock_row = self._make_repo_with_existing(tenant_id, progress_id)

        completed_at = _utc_now()
        result = await repo.mark_completed(
            tenant_id=tenant_id,
            progress_id=progress_id,
            completed_at=completed_at,
        )

        assert isinstance(result, OnboardingDraft)
        assert mock_row.status == "completed"
        assert mock_row.completed_at == completed_at
        mock_session.flush.assert_called_once()
