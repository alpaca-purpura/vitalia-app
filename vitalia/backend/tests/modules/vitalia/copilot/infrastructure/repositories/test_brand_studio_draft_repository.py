"""Tests for SqlAlchemyBrandStudioDraftRepository.

TDD: RED tests written before implementation (T-onboarding-1).
Tests cover: create, get_by_id_tenant, append_payload_patch, mark_committed,
tenant isolation cross-tenant rejection (returns None, NOT raises 403 — repo layer).

downstream-regression-na: brand-local copilot brand studio draft repo tests (vitalia-specific, not engine pattern)
"""

from __future__ import annotations

import inspect
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest


def _utc_now() -> datetime:
    """Return timezone-aware UTC datetime."""
    return datetime.now(tz=timezone.utc)


class TestBrandStudioDraftRepositoryInterface:
    """Verify domain interface is ABC with correct method signatures."""

    def test_interface_is_abstract(self) -> None:
        """BrandStudioDraftRepository must be abstract (cannot instantiate)."""
        from src.modules.vitalia.copilot.domain.repositories.brand_studio_draft_repository import (
            BrandStudioDraftRepository,
        )

        assert inspect.isabstract(BrandStudioDraftRepository), (
            "BrandStudioDraftRepository must be abstract (ABC) — it is a domain interface."
        )

    def test_create_method_signature(self) -> None:
        """create() must be abstract async method."""
        from src.modules.vitalia.copilot.domain.repositories.brand_studio_draft_repository import (
            BrandStudioDraftRepository,
        )

        assert hasattr(BrandStudioDraftRepository, "create")
        assert inspect.iscoroutinefunction(BrandStudioDraftRepository.create)

    def test_get_by_id_tenant_method_signature(self) -> None:
        """get_by_id_tenant() must be abstract async method."""
        from src.modules.vitalia.copilot.domain.repositories.brand_studio_draft_repository import (
            BrandStudioDraftRepository,
        )

        assert hasattr(BrandStudioDraftRepository, "get_by_id_tenant")
        assert inspect.iscoroutinefunction(BrandStudioDraftRepository.get_by_id_tenant)

    def test_append_payload_patch_method_signature(self) -> None:
        """append_payload_patch() must be abstract async method."""
        from src.modules.vitalia.copilot.domain.repositories.brand_studio_draft_repository import (
            BrandStudioDraftRepository,
        )

        assert hasattr(BrandStudioDraftRepository, "append_payload_patch")
        assert inspect.iscoroutinefunction(BrandStudioDraftRepository.append_payload_patch)

    def test_mark_committed_method_signature(self) -> None:
        """mark_committed() must be abstract async method."""
        from src.modules.vitalia.copilot.domain.repositories.brand_studio_draft_repository import (
            BrandStudioDraftRepository,
        )

        assert hasattr(BrandStudioDraftRepository, "mark_committed")
        assert inspect.iscoroutinefunction(BrandStudioDraftRepository.mark_committed)


class TestSqlAlchemyBrandStudioDraftRepositoryCreate:
    """Test SqlAlchemyBrandStudioDraftRepository.create() behaviour."""

    def _make_repo(self) -> "tuple":
        from src.modules.vitalia.copilot.infrastructure.repositories.brand_studio_draft_repository import (
            SqlAlchemyBrandStudioDraftRepository,
        )

        mock_session = AsyncMock()
        return SqlAlchemyBrandStudioDraftRepository(session=mock_session), mock_session

    @pytest.mark.asyncio
    async def test_create_returns_brand_studio_draft(self) -> None:
        """create() must return a BrandStudioDraft domain entity."""
        from src.modules.vitalia.copilot.domain.entities.brand_studio_draft import BrandStudioDraft

        repo, mock_session = self._make_repo()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        tenant_id = uuid4()
        user_id = uuid4()
        expires_at = _utc_now() + timedelta(hours=24)

        result = await repo.create(
            tenant_id=tenant_id,
            user_id=user_id,
            draft_kind="onboarding_extraction",
            expires_at=expires_at,
        )

        assert isinstance(result, BrandStudioDraft), (
            "create() must return BrandStudioDraft domain entity, not ORM model"
        )
        assert result.tenant_id == tenant_id
        assert result.user_id == user_id
        assert result.draft_kind == "onboarding_extraction"

    @pytest.mark.asyncio
    async def test_create_calls_session_add_and_flush(self) -> None:
        """create() must call session.add() and session.flush()."""
        repo, mock_session = self._make_repo()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        await repo.create(
            tenant_id=uuid4(),
            user_id=uuid4(),
            draft_kind="onboarding_extraction",
            expires_at=_utc_now() + timedelta(hours=24),
        )

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_accepts_none_expires_at(self) -> None:
        """create() accepts expires_at=None for drafts without TTL."""
        from src.modules.vitalia.copilot.domain.entities.brand_studio_draft import BrandStudioDraft

        repo, mock_session = self._make_repo()
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()

        result = await repo.create(
            tenant_id=uuid4(),
            user_id=uuid4(),
            draft_kind="onboarding_extraction",
            expires_at=None,
        )

        assert isinstance(result, BrandStudioDraft)


class TestSqlAlchemyBrandStudioDraftRepositoryGetByIdTenant:
    """Test get_by_id_tenant() with tenant isolation."""

    def _make_repo(self) -> "tuple":
        from src.modules.vitalia.copilot.infrastructure.repositories.brand_studio_draft_repository import (
            SqlAlchemyBrandStudioDraftRepository,
        )

        mock_session = AsyncMock()
        return SqlAlchemyBrandStudioDraftRepository(session=mock_session), mock_session

    def _mock_orm_row(self, tenant_id: UUID, draft_id: UUID) -> "MagicMock":
        from src.modules.vitalia.copilot.persistence.models.brand_studio_draft_model import (
            BrandStudioDraftModel,
        )

        mock_row = MagicMock(spec=BrandStudioDraftModel)
        mock_row.id = draft_id
        mock_row.tenant_id = tenant_id
        mock_row.user_id = uuid4()
        mock_row.draft_kind = "onboarding_extraction"
        mock_row.draft_payload = {}
        mock_row.voice_profile_partial_json = {}
        mock_row.committed_at = None
        mock_row.expires_at = _utc_now() + timedelta(hours=24)
        mock_row.created_at = _utc_now()
        mock_row.updated_at = _utc_now()
        return mock_row

    @pytest.mark.asyncio
    async def test_get_by_id_tenant_returns_draft_when_found(self) -> None:
        """get_by_id_tenant() returns BrandStudioDraft when row found for tenant+draft_id."""
        from src.modules.vitalia.copilot.domain.entities.brand_studio_draft import BrandStudioDraft

        repo, mock_session = self._make_repo()
        tenant_id = uuid4()
        draft_id = uuid4()

        mock_row = self._mock_orm_row(tenant_id, draft_id)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id_tenant(tenant_id=tenant_id, draft_id=draft_id)

        assert result is not None
        assert isinstance(result, BrandStudioDraft)
        assert result.tenant_id == tenant_id

    @pytest.mark.asyncio
    async def test_get_by_id_tenant_returns_none_when_not_found(self) -> None:
        """get_by_id_tenant() returns None when no matching row — NOT raises."""
        repo, mock_session = self._make_repo()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        result = await repo.get_by_id_tenant(tenant_id=uuid4(), draft_id=uuid4())

        assert result is None

    @pytest.mark.asyncio
    async def test_tenant_isolation_cross_tenant_returns_none(self) -> None:
        """Tenant isolation: different tenant_id returns None (row-level isolation, not exception)."""
        repo, mock_session = self._make_repo()

        # Simulate: draft exists for tenant_A but queried with tenant_B → DB returns nothing
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        tenant_b_id = uuid4()
        draft_id = uuid4()  # draft owned by tenant_A

        result = await repo.get_by_id_tenant(tenant_id=tenant_b_id, draft_id=draft_id)

        # MUST return None — repo layer does NOT raise 403 (that's API layer responsibility)
        assert result is None, (
            "Cross-tenant query must return None from repo layer — 403 HTTP is API layer responsibility, NOT repo layer"
        )
        mock_session.execute.assert_called_once()


class TestSqlAlchemyBrandStudioDraftRepositoryAppendPayloadPatch:
    """Test append_payload_patch() merges patch into draft_payload."""

    def _make_repo_with_existing(self, tenant_id: UUID, draft_id: UUID) -> "tuple":
        from src.modules.vitalia.copilot.infrastructure.repositories.brand_studio_draft_repository import (
            SqlAlchemyBrandStudioDraftRepository,
        )
        from src.modules.vitalia.copilot.persistence.models.brand_studio_draft_model import (
            BrandStudioDraftModel,
        )

        mock_session = AsyncMock()

        mock_row = MagicMock(spec=BrandStudioDraftModel)
        mock_row.id = draft_id
        mock_row.tenant_id = tenant_id
        mock_row.user_id = uuid4()
        mock_row.draft_kind = "onboarding_extraction"
        mock_row.draft_payload = {"existing_key": "existing_value"}
        mock_row.voice_profile_partial_json = {}
        mock_row.committed_at = None
        mock_row.expires_at = _utc_now() + timedelta(hours=24)
        mock_row.created_at = _utc_now()
        mock_row.updated_at = _utc_now()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        repo = SqlAlchemyBrandStudioDraftRepository(session=mock_session)
        return repo, mock_session, mock_row

    @pytest.mark.asyncio
    async def test_append_payload_patch_merges_and_returns_draft(self) -> None:
        """append_payload_patch() merges patch into existing draft_payload and returns BrandStudioDraft."""
        from src.modules.vitalia.copilot.domain.entities.brand_studio_draft import BrandStudioDraft

        tenant_id = uuid4()
        draft_id = uuid4()
        repo, mock_session, mock_row = self._make_repo_with_existing(tenant_id, draft_id)

        patch = {"tenant.name": "Clinica Salud Total", "tenant.vertical": "salud"}
        voice_patch = {"energy": 0.4, "warmth": 0.8}

        result = await repo.append_payload_patch(
            tenant_id=tenant_id,
            draft_id=draft_id,
            patch=patch,
            voice_profile_patch=voice_patch,
        )

        assert isinstance(result, BrandStudioDraft)
        # Verify patch was merged into the existing payload
        assert mock_row.draft_payload["tenant.name"] == "Clinica Salud Total"
        assert mock_row.draft_payload["existing_key"] == "existing_value"  # original preserved
        assert mock_row.voice_profile_partial_json == voice_patch
        mock_session.flush.assert_called_once()


class TestSqlAlchemyBrandStudioDraftRepositoryMarkCommitted:
    """Test mark_committed() sets committed_at on the row."""

    def _make_repo_with_existing(self, tenant_id: UUID, draft_id: UUID) -> "tuple":
        from src.modules.vitalia.copilot.infrastructure.repositories.brand_studio_draft_repository import (
            SqlAlchemyBrandStudioDraftRepository,
        )
        from src.modules.vitalia.copilot.persistence.models.brand_studio_draft_model import (
            BrandStudioDraftModel,
        )

        mock_session = AsyncMock()

        mock_row = MagicMock(spec=BrandStudioDraftModel)
        mock_row.id = draft_id
        mock_row.tenant_id = tenant_id
        mock_row.user_id = uuid4()
        mock_row.draft_kind = "onboarding_extraction"
        mock_row.draft_payload = {"tenant.name": "Clinica Test"}
        mock_row.voice_profile_partial_json = {"energy": 0.5}
        mock_row.committed_at = None
        mock_row.expires_at = _utc_now() + timedelta(hours=24)
        mock_row.created_at = _utc_now()
        mock_row.updated_at = _utc_now()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_row
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.flush = AsyncMock()

        repo = SqlAlchemyBrandStudioDraftRepository(session=mock_session)
        return repo, mock_session, mock_row

    @pytest.mark.asyncio
    async def test_mark_committed_sets_committed_at(self) -> None:
        """mark_committed() sets committed_at timestamp on the ORM row and returns BrandStudioDraft."""
        from src.modules.vitalia.copilot.domain.entities.brand_studio_draft import BrandStudioDraft

        tenant_id = uuid4()
        draft_id = uuid4()
        repo, mock_session, mock_row = self._make_repo_with_existing(tenant_id, draft_id)

        committed_at = _utc_now()
        result = await repo.mark_committed(
            tenant_id=tenant_id,
            draft_id=draft_id,
            committed_at=committed_at,
        )

        assert isinstance(result, BrandStudioDraft)
        assert mock_row.committed_at == committed_at
        mock_session.flush.assert_called_once()
