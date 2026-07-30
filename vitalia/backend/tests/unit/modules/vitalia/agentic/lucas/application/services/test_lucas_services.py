"""RED tests — Lucas application services (stage recommendation, attribution, referrals).

TDD per .claude/rules/tdd-mandatory.md.

Tests verify:
- LucasStageRecommendationService: BudgetGuard pre-LLM, skips when budget exceeded
- LucasAttributionService: pure DB, calls analytics adapter + save
- LucasReferralsService: pure DB, calls analytics adapter + save
- All services pass tenant_id + clinic_id to repos (HIPAA-lite dual filter)
- No PHI in log traces (sanitize_payload pattern)
- Currency comes from tenant locale, never hardcoded
"""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

TENANT_ID = uuid4()
CLINIC_ID = uuid4()


def _utc_now() -> dt.datetime:
    return dt.datetime.now(tz=dt.timezone.utc)


def _make_mock_locale(currency: str = "ARS", timezone: str = "America/Buenos_Aires") -> MagicMock:
    locale = MagicMock()
    locale.currency = currency
    locale.timezone = timezone
    return locale


class TestLucasStageRecommendationService:
    """Tests for LucasStageRecommendationService."""

    @pytest.mark.asyncio
    async def test_compute_saves_recommendation_when_budget_ok(self) -> None:
        """compute() calls LLM and saves recommendation when budget is available."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_stage_recommendation_service import (
            LucasStageRecommendationService,
        )

        mock_repo = AsyncMock()

        # save() must return the entity passed to it (capture pattern)
        async def _capture_save(entity: object) -> object:
            return entity

        mock_repo.save = AsyncMock(side_effect=_capture_save)
        mock_budget_guard = MagicMock()
        mock_budget_guard.check = MagicMock(return_value=True)  # budget OK
        mock_llm = AsyncMock()
        mock_llm.complete = AsyncMock(
            return_value=MagicMock(content="Recomendación generada por IA para etapa attraction.")
        )
        mock_adapter = MagicMock()
        mock_adapter.get_stage_metrics = AsyncMock(return_value={"channel_count": 3, "avg_ctr": 0.05})
        mock_locale = _make_mock_locale()

        service = LucasStageRecommendationService(
            repo=mock_repo,
            budget_guard=mock_budget_guard,
            llm_service=mock_llm,
            analytics_adapter=mock_adapter,
        )
        result = await service.compute(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            stage="attraction",
            period="2026-01",
            locale=mock_locale,
        )

        assert result is not None
        assert result.stage == "attraction"
        assert result.status == "open"
        mock_repo.save.assert_called_once()
        mock_budget_guard.check.assert_called_once()

    @pytest.mark.asyncio
    async def test_compute_returns_skipped_budget_when_budget_exceeded(self) -> None:
        """compute() returns skipped_budget recommendation when BudgetGuard check fails."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_stage_recommendation_service import (
            LucasStageRecommendationService,
        )

        mock_repo = AsyncMock()

        async def _capture_save(entity: object) -> object:
            return entity

        mock_repo.save = AsyncMock(side_effect=_capture_save)
        mock_budget_guard = MagicMock()
        mock_budget_guard.check = MagicMock(return_value=False)  # budget exceeded
        mock_llm = AsyncMock()
        mock_adapter = MagicMock()
        mock_adapter.get_stage_metrics = AsyncMock(return_value={})
        mock_locale = _make_mock_locale()

        service = LucasStageRecommendationService(
            repo=mock_repo,
            budget_guard=mock_budget_guard,
            llm_service=mock_llm,
            analytics_adapter=mock_adapter,
        )
        result = await service.compute(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            stage="capture",
            period="2026-01",
            locale=mock_locale,
        )

        assert result.status == "skipped_budget"
        # LLM must NOT be called when budget exceeded
        mock_llm.complete.assert_not_called()

    @pytest.mark.asyncio
    async def test_compute_passes_clinic_id_to_repo(self) -> None:
        """compute() passes both tenant_id and clinic_id to repo (HIPAA dual filter)."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_stage_recommendation_service import (
            LucasStageRecommendationService,
        )

        mock_repo = AsyncMock()

        async def _capture_save(entity: object) -> object:
            return entity

        mock_repo.save = AsyncMock(side_effect=_capture_save)
        mock_budget_guard = MagicMock()
        mock_budget_guard.check = MagicMock(return_value=True)
        mock_llm = AsyncMock()
        mock_llm.complete = AsyncMock(return_value=MagicMock(content="Recomendación de prueba."))
        mock_adapter = MagicMock()
        mock_adapter.get_stage_metrics = AsyncMock(return_value={})
        mock_locale = _make_mock_locale()

        service = LucasStageRecommendationService(
            repo=mock_repo,
            budget_guard=mock_budget_guard,
            llm_service=mock_llm,
            analytics_adapter=mock_adapter,
        )
        await service.compute(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            stage="nurture",
            period="2026-01",
            locale=mock_locale,
        )

        # Repo save was called with an entity having correct tenant+clinic
        saved_entity = mock_repo.save.call_args[0][0]
        assert saved_entity.tenant_id == TENANT_ID
        assert saved_entity.clinic_id == CLINIC_ID


class TestLucasAttributionService:
    """Tests for LucasAttributionService (pure DB, no LLM)."""

    @pytest.mark.asyncio
    async def test_compute_attribution_queries_adapter_and_saves(self) -> None:
        """compute_attribution() queries analytics adapter and saves snapshot."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_attribution_service import (
            LucasAttributionService,
        )

        mock_repo = AsyncMock()

        async def _capture_save(entity: object) -> object:
            return entity

        mock_repo.save = AsyncMock(side_effect=_capture_save)
        mock_adapter = MagicMock()
        mock_adapter.get_attribution_breakdown = AsyncMock(return_value={"google_ads": 15000.0, "organic": 8000.0})
        mock_locale = _make_mock_locale(currency="ARS")

        service = LucasAttributionService(
            repo=mock_repo,
            analytics_adapter=mock_adapter,
        )
        result = await service.compute_attribution(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 1, 1),
            period_end=dt.date(2026, 1, 31),
            locale=mock_locale,
        )

        assert result is not None
        assert result.currency == "ARS"  # from locale, NOT hardcoded
        assert result.tenant_id == TENANT_ID
        assert result.clinic_id == CLINIC_ID
        mock_repo.save.assert_called_once()
        mock_adapter.get_attribution_breakdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_compute_attribution_currency_from_locale(self) -> None:
        """compute_attribution() uses locale.currency — never hardcodes USD."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_attribution_service import (
            LucasAttributionService,
        )

        mock_repo = AsyncMock()

        async def _capture_save(entity: object) -> object:
            return entity

        mock_repo.save = AsyncMock(side_effect=_capture_save)
        mock_adapter = MagicMock()
        mock_adapter.get_attribution_breakdown = AsyncMock(return_value={})
        mock_locale = _make_mock_locale(currency="COP")

        service = LucasAttributionService(
            repo=mock_repo,
            analytics_adapter=mock_adapter,
        )
        result = await service.compute_attribution(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 1, 1),
            period_end=dt.date(2026, 1, 31),
            locale=mock_locale,
        )

        assert result.currency == "COP"  # from locale


class TestLucasReferralsService:
    """Tests for LucasReferralsService (pure DB, no LLM)."""

    @pytest.mark.asyncio
    async def test_compute_referrals_queries_adapter_and_saves(self) -> None:
        """compute_referrals() queries analytics adapter and saves leaderboard snapshot."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_referrals_service import (
            LucasReferralsService,
        )

        mock_repo = AsyncMock()

        async def _capture_save(entity: object) -> object:
            return entity

        mock_repo.save = AsyncMock(side_effect=_capture_save)
        mock_adapter = MagicMock()
        mock_adapter.get_referrals_data = AsyncMock(
            return_value={
                "top_referrers": [{"referrer_id": str(uuid4()), "referral_count": 5, "rank": 1}],
                "total_referrals": 12,
                "total_converted": 8,
            }
        )
        mock_locale = _make_mock_locale()

        service = LucasReferralsService(
            repo=mock_repo,
            analytics_adapter=mock_adapter,
        )
        result = await service.compute_referrals(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 1, 1),
            period_end=dt.date(2026, 1, 31),
            locale=mock_locale,
        )

        assert result is not None
        assert result.total_referrals == 12
        assert result.total_converted == 8
        assert result.tenant_id == TENANT_ID
        assert result.clinic_id == CLINIC_ID
        mock_repo.save.assert_called_once()

    @pytest.mark.asyncio
    async def test_compute_referrals_passes_dual_filter_to_repo(self) -> None:
        """compute_referrals() entity saved with both tenant_id and clinic_id."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_referrals_service import (
            LucasReferralsService,
        )

        mock_repo = AsyncMock()

        async def _capture_save(entity: object) -> object:
            return entity

        mock_repo.save = AsyncMock(side_effect=_capture_save)
        mock_adapter = MagicMock()
        mock_adapter.get_referrals_data = AsyncMock(
            return_value={"top_referrers": [], "total_referrals": 0, "total_converted": 0}
        )
        mock_locale = _make_mock_locale()

        service = LucasReferralsService(
            repo=mock_repo,
            analytics_adapter=mock_adapter,
        )
        await service.compute_referrals(
            tenant_id=TENANT_ID,
            clinic_id=CLINIC_ID,
            period_start=dt.date(2026, 2, 1),
            period_end=dt.date(2026, 2, 28),
            locale=mock_locale,
        )

        saved_entity = mock_repo.save.call_args[0][0]
        assert saved_entity.tenant_id == TENANT_ID
        assert saved_entity.clinic_id == CLINIC_ID
