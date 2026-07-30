"""RED tests — Lucas infrastructure repositories.

TDD per .claude/rules/tdd-mandatory.md.
Tests verify HIPAA-lite dual filter (tenant_id + clinic_id) on every method,
soft-delete exclusion, and that get_by_id always passes both filter params.

No PHI in these test payloads — repositories are analytics/recommendations only.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
OTHER_TENANT = uuid4()
OTHER_CLINIC = uuid4()


def _utc_now() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


class TestStageRecommendationRepository:
    """Tests for StageRecommendationRepository — dual filter enforcement."""

    @pytest.mark.asyncio
    async def test_list_by_stage_passes_both_filters(self) -> None:
        """list_by_stage() passes tenant_id + clinic_id to query (dual filter)."""
        from src.modules.vitalia.agentic.lucas.infrastructure.repositories.stage_recommendation_repository import (
            StageRecommendationRepository,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = StageRecommendationRepository(session=mock_session)
        result = await repo.list_by_stage(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            stage="attraction",
        )

        assert isinstance(result, list)
        mock_session.execute.assert_called_once()
        # Verify BOTH tenant_id and clinic_id are in query criteria
        call_args = mock_session.execute.call_args[0][0]
        query_str = str(call_args)
        assert "tenant_id" in query_str
        assert "clinic_id" in query_str

    @pytest.mark.asyncio
    async def test_save_persists_recommendation(self) -> None:
        """save() merges recommendation into session and flushes."""
        from src.modules.vitalia.agentic.lucas.domain.entities.stage_recommendation import (
            StageRecommendation,
        )
        from src.modules.vitalia.agentic.lucas.infrastructure.repositories.stage_recommendation_repository import (
            StageRecommendationRepository,
        )

        mock_session = AsyncMock()

        entity = StageRecommendation(
            id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            stage="capture",
            recommendation_kind="conversion",
            title="Activa formulario de captura",
            body="Implementa formulario en tu página.",
            rationale_json={"source": "analytics"},
            priority=60,
            status="open",
            expires_at=_utc_now() + dt.timedelta(days=30),
            created_at=_utc_now(),
            updated_at=_utc_now(),
            deleted_at=None,
            approved_by_user_id=None,
            approved_at=None,
            undo_until=None,
        )
        repo = StageRecommendationRepository(session=mock_session)
        await repo.save(entity)

        mock_session.merge.assert_called_once()
        mock_session.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_by_id_passes_both_filters(self) -> None:
        """get_by_id() passes tenant_id + clinic_id (dual filter, no leak)."""
        from src.modules.vitalia.agentic.lucas.infrastructure.repositories.stage_recommendation_repository import (
            StageRecommendationRepository,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = StageRecommendationRepository(session=mock_session)
        result = await repo.get_by_id(
            entity_id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
        )

        assert result is None
        call_args = mock_session.execute.call_args[0][0]
        query_str = str(call_args)
        assert "tenant_id" in query_str
        assert "clinic_id" in query_str

    @pytest.mark.asyncio
    async def test_list_by_stage_excludes_soft_deleted(self) -> None:
        """list_by_stage() filters out rows with deleted_at IS NOT NULL."""
        from src.modules.vitalia.agentic.lucas.infrastructure.repositories.stage_recommendation_repository import (
            StageRecommendationRepository,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = StageRecommendationRepository(session=mock_session)
        await repo.list_by_stage(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            stage="retention",
        )

        call_args = mock_session.execute.call_args[0][0]
        query_str = str(call_args)
        assert "deleted_at" in query_str


class TestAttributionMatrixSnapshotRepository:
    """Tests for AttributionMatrixSnapshotRepository — dual filter enforcement."""

    @pytest.mark.asyncio
    async def test_get_latest_for_period_dual_filter(self) -> None:
        """get_latest_for_period() passes tenant_id + clinic_id."""
        from src.modules.vitalia.agentic.lucas.infrastructure.repositories.attribution_matrix_snapshot_repository import (  # noqa: E501
            AttributionMatrixSnapshotRepository,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = AttributionMatrixSnapshotRepository(session=mock_session)
        result = await repo.get_latest_for_period(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 1, 1),
            period_end=dt.date(2026, 1, 31),
        )
        assert result is None
        call_args = mock_session.execute.call_args[0][0]
        query_str = str(call_args)
        assert "tenant_id" in query_str
        assert "clinic_id" in query_str

    @pytest.mark.asyncio
    async def test_save_attribution_snapshot(self) -> None:
        """save() persists snapshot via merge+flush."""
        from src.modules.vitalia.agentic.lucas.domain.entities.attribution_matrix_snapshot import (
            AttributionMatrixSnapshot,
        )
        from src.modules.vitalia.agentic.lucas.infrastructure.repositories.attribution_matrix_snapshot_repository import (  # noqa: E501
            AttributionMatrixSnapshotRepository,
        )

        mock_session = AsyncMock()

        snap = AttributionMatrixSnapshot(
            id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 1, 1),
            period_end=dt.date(2026, 1, 31),
            channel_breakdown={"google_ads": 10000.0},
            total_attributed_revenue=Decimal("10000.00"),
            currency="ARS",
            computed_at=_utc_now(),
            deleted_at=None,
        )
        repo = AttributionMatrixSnapshotRepository(session=mock_session)
        await repo.save(snap)

        mock_session.merge.assert_called_once()
        mock_session.flush.assert_called_once()


class TestReferralsLeaderboardSnapshotRepository:
    """Tests for ReferralsLeaderboardSnapshotRepository — dual filter enforcement."""

    @pytest.mark.asyncio
    async def test_get_latest_for_period_dual_filter(self) -> None:
        """get_latest_for_period() passes tenant_id + clinic_id."""
        from src.modules.vitalia.agentic.lucas.infrastructure.repositories.referrals_leaderboard_snapshot_repository import (  # noqa: E501
            ReferralsLeaderboardSnapshotRepository,
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        repo = ReferralsLeaderboardSnapshotRepository(session=mock_session)
        result = await repo.get_latest_for_period(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 1, 1),
            period_end=dt.date(2026, 1, 31),
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_save_referrals_snapshot(self) -> None:
        """save() persists referrals snapshot."""
        from src.modules.vitalia.agentic.lucas.domain.entities.referrals_leaderboard_snapshot import (
            ReferralsLeaderboardSnapshot,
        )
        from src.modules.vitalia.agentic.lucas.infrastructure.repositories.referrals_leaderboard_snapshot_repository import (  # noqa: E501
            ReferralsLeaderboardSnapshotRepository,
        )

        mock_session = AsyncMock()

        snap = ReferralsLeaderboardSnapshot(
            id=uuid4(),
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 1, 1),
            period_end=dt.date(2026, 1, 31),
            top_referrers=[],
            total_referrals=0,
            total_converted=0,
            computed_at=_utc_now(),
            deleted_at=None,
        )
        repo = ReferralsLeaderboardSnapshotRepository(session=mock_session)
        await repo.save(snap)

        mock_session.merge.assert_called_once()
        mock_session.flush.assert_called_once()
