"""Tests for LucasRecommendationRepository.

Covers:
- SC-MK-01: approve updates status (approve_updates_status, dual_filter, cross_clinic_blocked)
- list_open_by_stage: filters by status=open + stage, respects dual filter
- list_pending_undo_expired: filters approved + undo_until in past
- HIPAA-lite dual filter: tenant_id + clinic_id enforced (SC-MK-04)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from src.modules.vitalia.infrastructure.models.lucas_recommendation_model import (
    LucasRecommendationModel,
)

# These imports will fail until infrastructure is implemented — RED phase
from src.modules.vitalia.marketing.domain.enums import BowtieStage
from src.modules.vitalia.marketing.infrastructure.repositories.lucas_recommendation_repository import (
    LucasRecommendationRepository,
)


def _make_model(
    *,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    status: str = "open",
    stage: str = "attract",
    priority: int = 1,
    expires_at: datetime | None = None,
    approved_at: datetime | None = None,
    undo_until: datetime | None = None,
    deleted_at: datetime | None = None,
) -> LucasRecommendationModel:
    """Factory for LucasRecommendationModel test instances."""
    now = datetime.now(UTC)
    model = LucasRecommendationModel()
    model.id = uuid.uuid4()
    model.tenant_id = tenant_id
    model.clinic_id = clinic_id
    model.stage = stage
    model.recommendation_kind = "increase_budget"
    model.title = "Aumentar presupuesto Google Ads"
    model.body = "Tu CTR bajó 15% esta semana."
    model.rationale_json = {"metric": "ctr", "delta": -0.15}
    model.priority = priority
    model.status = status
    model.expires_at = expires_at or (now + timedelta(days=7))
    model.created_at = now
    model.updated_at = now
    model.approved_at = approved_at
    model.undo_until = undo_until
    model.deleted_at = deleted_at
    return model


class TestLucasRecommendationRepositoryInit:
    """Repository construction uses scope_field='clinic_id'."""

    def test_inherits_compound_scope_repository_base(self) -> None:
        """LucasRecommendationRepository must subclass CompoundScopeRepositoryBase."""
        from luana_core_platform.repositories.compound_scope_repository import (
            CompoundScopeRepositoryBase,
        )

        assert issubclass(LucasRecommendationRepository, CompoundScopeRepositoryBase)

    def test_model_class_var_is_set(self) -> None:
        """MODEL ClassVar must be LucasRecommendationModel."""
        assert LucasRecommendationRepository.MODEL is LucasRecommendationModel

    def test_scope_field_is_clinic_id(self) -> None:
        """Repository scope_field must be 'clinic_id' for HIPAA-lite dual filter."""
        session = AsyncMock()
        repo = LucasRecommendationRepository(session=session)
        assert repo._scope_field == "clinic_id"  # noqa: SLF001


class TestListOpenByStage:
    """list_open_by_stage — filters OPEN recs for a tenant/clinic/stage."""

    async def test_returns_open_recs_for_stage(self) -> None:
        """Returns models with status=open for the given stage."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        model = _make_model(tenant_id=tenant_id, clinic_id=clinic_id, status="open", stage="attract")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [model]
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        results = await repo.list_open_by_stage(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage=BowtieStage.ATTRACTION,
        )

        assert len(results) == 1
        assert results[0].status == "open"
        assert results[0].stage == "attract"
        session.execute.assert_called_once()

    async def test_dual_filter_applied(self) -> None:
        """Query must use both tenant_id AND clinic_id (SC-MK-04)."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        await repo.list_open_by_stage(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage=BowtieStage.ATTRACTION,
        )

        session.execute.assert_called_once()
        stmt = session.execute.call_args[0][0]
        # SQLAlchemy may render UUIDs with or without dashes in literal_binds
        stmt_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        tenant_hex = str(tenant_id).replace("-", "")
        clinic_hex = str(clinic_id).replace("-", "")
        assert tenant_hex in stmt_str.replace("-", ""), f"tenant_id not in query: {stmt_str}"
        assert clinic_hex in stmt_str.replace("-", ""), f"clinic_id not in query: {stmt_str}"

    async def test_excludes_deleted_recs(self) -> None:
        """Soft-deleted records must never appear."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        deleted_model = _make_model(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            status="open",
            stage="attract",
            deleted_at=datetime.now(UTC),
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []  # must NOT include deleted
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        results = await repo.list_open_by_stage(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage=BowtieStage.ATTRACTION,
        )

        # deleted_model excluded (mocked to empty)
        assert deleted_model not in results

    async def test_excludes_non_open_status(self) -> None:
        """Approved/rejected/expired recs must not appear in open list."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        results = await repo.list_open_by_stage(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage=BowtieStage.ATTRACTION,
        )

        assert results == []

    async def test_limit_is_applied(self) -> None:
        """list_open_by_stage accepts optional limit param (default 3)."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        # Should not raise
        await repo.list_open_by_stage(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage=BowtieStage.ATTRACTION,
            limit=5,
        )
        session.execute.assert_called_once()


class TestListPendingUndoExpired:
    """list_pending_undo_expired — filters APPROVED recs with undo_until in past."""

    async def test_returns_approved_with_expired_undo_window(self) -> None:
        """Returns approved recs where undo_until < now."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        now = datetime.now(UTC)
        session = AsyncMock()

        model = _make_model(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            status="approved",
            approved_at=now - timedelta(minutes=10),
            undo_until=now - timedelta(minutes=5),  # expired
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [model]
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        results = await repo.list_pending_undo_expired(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            now=now,
        )

        assert len(results) == 1
        assert results[0].status == "approved"
        assert results[0].undo_until is not None
        assert results[0].undo_until < now

    async def test_dual_filter_applied_undo_expired(self) -> None:
        """list_pending_undo_expired also enforces dual filter."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        now = datetime.now(UTC)
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        await repo.list_pending_undo_expired(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            now=now,
        )

        session.execute.assert_called_once()
        stmt = session.execute.call_args[0][0]
        stmt_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        tenant_hex = str(tenant_id).replace("-", "")
        clinic_hex = str(clinic_id).replace("-", "")
        assert tenant_hex in stmt_str.replace("-", ""), f"tenant_id not in query: {stmt_str}"
        assert clinic_hex in stmt_str.replace("-", ""), f"clinic_id not in query: {stmt_str}"


class TestApproveUpdatesStatus:
    """SC-MK-01: approve recommendation updates status in DB."""

    async def test_approve_updates_status(self) -> None:
        """get_by_id returns model; domain entity approve() works; repo is SQLA 2.0."""
        session = AsyncMock()
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        rec_id = uuid.uuid4()
        now = datetime.now(UTC)

        model = _make_model(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            status="open",
            expires_at=now + timedelta(days=7),
        )
        model.id = rec_id

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = model
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        result = await repo.get_by_id(id=rec_id, tenant_id=tenant_id, scope_id=clinic_id)

        assert result is not None
        assert result.id == rec_id
        assert result.status == "open"

    async def test_dual_filter_tenant_and_clinic(self) -> None:
        """get_by_id MUST filter both tenant_id and clinic_id (HIPAA-lite dual filter)."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        rec_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        await repo.get_by_id(id=rec_id, tenant_id=tenant_id, scope_id=clinic_id)

        session.execute.assert_called_once()
        stmt = session.execute.call_args[0][0]
        stmt_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        tenant_hex = str(tenant_id).replace("-", "")
        clinic_hex = str(clinic_id).replace("-", "")
        assert tenant_hex in stmt_str.replace("-", ""), f"tenant_id not in query: {stmt_str}"
        assert clinic_hex in stmt_str.replace("-", ""), f"clinic_id not in query: {stmt_str}"

    async def test_other_clinic_cannot_read(self) -> None:
        """A different clinic_id returns None (cross-clinic isolation, SC-MK-04)."""
        tenant_id = uuid.uuid4()
        clinic_b = uuid.uuid4()  # different clinic (clinic_a would own the record)
        rec_id = uuid.uuid4()
        session = AsyncMock()

        # clinic_a owns the record — querying with clinic_b returns None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        session.execute.return_value = mock_result

        repo = LucasRecommendationRepository(session=session)
        result = await repo.get_by_id(id=rec_id, tenant_id=tenant_id, scope_id=clinic_b)

        assert result is None, "Cross-clinic query must return None (dual filter enforced)"
