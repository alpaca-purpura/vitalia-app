"""TDD tests for vitalia marketing cron jobs (T-mk-be-6).

Tests cover:
- channel_metrics_sync_meta: soft-fail per tenant, ChannelSyncFailed event publish
- channel_metrics_sync_google: soft-fail per tenant, upsert metrics
- lucas_daily_analysis_sweep: 30d cooldown for rejected recommendation_kinds
- referrals_value_sync: conversion_value_cents recomputation

All cron jobs use @cron_envelope from engine (luana_core_platform.workers.cron_envelope).

HIPAA-lite: no PHI in payloads; dual filter tenant_id + clinic_id verified via mocks.

downstream-regression-na: brand-local worker tests — no cross-brand consumers
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers / factories
# ---------------------------------------------------------------------------

_TENANT_ID = uuid.uuid4()
_CLINIC_ID = uuid.uuid4()


def _make_sync_state(
    *,
    tenant_id: uuid.UUID = _TENANT_ID,
    clinic_id: uuid.UUID = _CLINIC_ID,
    provider: str = "meta_ads",
    status: str = "ok",
    enabled: bool = True,
    ad_account_id: str | None = "act_123456",
) -> MagicMock:
    """Create a mock ChannelSyncStateModel."""
    m = MagicMock()
    m.id = uuid.uuid4()
    m.tenant_id = tenant_id
    m.clinic_id = clinic_id
    m.provider = provider
    m.status = status
    m.enabled = enabled
    m.ad_account_id = ad_account_id
    m.last_sync_at = None
    m.last_success_at = None
    return m


def _make_recommendation(
    *,
    tenant_id: uuid.UUID = _TENANT_ID,
    clinic_id: uuid.UUID = _CLINIC_ID,
    status: str = "rejected",
    recommendation_kind: str = "increase_budget",
    rejected_at: datetime | None = None,
) -> MagicMock:
    """Create a mock LucasRecommendationModel."""
    m = MagicMock()
    m.id = uuid.uuid4()
    m.tenant_id = tenant_id
    m.clinic_id = clinic_id
    m.status = status
    m.recommendation_kind = recommendation_kind
    m.rejected_at = rejected_at or datetime.now(UTC) - timedelta(days=5)
    m.reject_reason = "not_relevant"
    return m


def _make_referral(
    *,
    tenant_id: uuid.UUID = _TENANT_ID,
    clinic_id: uuid.UUID = _CLINIC_ID,
    status: str = "converted",
    referred_patient_id: uuid.UUID | None = None,
) -> MagicMock:
    """Create a mock ReferralModel."""
    m = MagicMock()
    m.id = uuid.uuid4()
    m.tenant_id = tenant_id
    m.clinic_id = clinic_id
    m.status = status
    m.referred_patient_id = referred_patient_id or uuid.uuid4()
    m.converted_at = None
    m.conversion_value_cents = None
    return m


# ---------------------------------------------------------------------------
# channel_metrics_sync_meta tests
# ---------------------------------------------------------------------------


class TestChannelMetricsSyncMeta:
    """Tests for channel_metrics_sync_meta cron job (SC-MK-02)."""

    @pytest.mark.asyncio
    async def test_channel_metrics_sync_meta_soft_fail_per_tenant(self) -> None:
        """SC-MK-02: One tenant's adapter failure does not abort the cron for other tenants.

        Given two active Meta Ads connections (tenant A and tenant B),
        When tenant A's Meta API call raises an exception,
        Then the cron continues and processes tenant B successfully.
        """
        tenant_a = uuid.uuid4()
        clinic_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        clinic_b = uuid.uuid4()

        sync_state_a = _make_sync_state(tenant_id=tenant_a, clinic_id=clinic_a)
        sync_state_b = _make_sync_state(tenant_id=tenant_b, clinic_id=clinic_b)

        mock_sync_repo = AsyncMock()
        mock_sync_repo.get_all_active_by_provider = AsyncMock(return_value=[sync_state_a, sync_state_b])
        mock_sync_repo.decrypt_token = AsyncMock(return_value=b"fake_token")

        mock_metric_repo = AsyncMock()
        mock_metric_repo.upsert_metric = AsyncMock()

        # Tenant A fails, tenant B succeeds
        call_count = [0]

        async def fake_fetch_insights(**kwargs: Any) -> list[dict[str, Any]]:
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Meta API error para tenant A")
            return [
                {
                    "campaign_id": "camp_001",
                    "impressions": 1000,
                    "clicks": 50,
                    "spend": "25.00",
                    "date_start": "2026-05-20",
                    "date_stop": "2026-05-20",
                }
            ]

        mock_meta_adapter = AsyncMock()
        mock_meta_adapter.fetch_insights = AsyncMock(side_effect=fake_fetch_insights)

        mock_bus = AsyncMock()

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_all_active_meta_connections",
                new=AsyncMock(return_value=[sync_state_a, sync_state_b]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_sync_repo",
                return_value=mock_sync_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_metric_repo",
                return_value=mock_metric_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_meta_adapter",
                return_value=mock_meta_adapter,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta import (
                channel_metrics_sync_meta,
            )

            # Should NOT raise — soft-fail isolates per tenant
            await channel_metrics_sync_meta.__wrapped__(ctx)

        # Tenant B processed successfully — upsert called at least once
        assert mock_metric_repo.upsert_metric.call_count >= 1
        # Tenant A error did not prevent tenant B processing
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_channel_metrics_sync_meta_publishes_channelsyncfailed_event(self) -> None:
        """SC-MK-02: On Meta API failure, ChannelSyncFailed event is published.

        Given an active Meta Ads connection,
        When the Meta API call raises an exception,
        Then a ChannelSyncFailed event is published via the outbox adapter_bus.
        """
        sync_state = _make_sync_state()
        mock_sync_repo = AsyncMock()
        mock_sync_repo.decrypt_token = AsyncMock(return_value=b"fake_token")

        mock_metric_repo = AsyncMock()

        mock_meta_adapter = AsyncMock()
        mock_meta_adapter.fetch_insights = AsyncMock(side_effect=RuntimeError("Auth expired"))

        published_events: list[Any] = []

        async def capture_publish(event: Any) -> None:
            published_events.append(event)

        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(side_effect=capture_publish)

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_all_active_meta_connections",
                new=AsyncMock(return_value=[sync_state]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_sync_repo",
                return_value=mock_sync_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_metric_repo",
                return_value=mock_metric_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_meta_adapter",
                return_value=mock_meta_adapter,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta import (
                channel_metrics_sync_meta,
            )

            await channel_metrics_sync_meta.__wrapped__(ctx)

        # ChannelSyncFailed event published
        assert len(published_events) == 1
        event = published_events[0]
        from src.modules.vitalia.marketing.domain.events import ChannelSyncFailed

        assert isinstance(event, ChannelSyncFailed)
        assert event.tenant_id == sync_state.tenant_id
        assert event.clinic_id == sync_state.clinic_id
        assert "Auth expired" in event.error_message

    @pytest.mark.asyncio
    async def test_channel_metrics_sync_meta_publishes_channelsync_succeeded_event(self) -> None:
        """On success, ChannelSyncSucceeded event is published."""
        sync_state = _make_sync_state()
        mock_sync_repo = AsyncMock()
        mock_sync_repo.decrypt_token = AsyncMock(return_value=b"token_ok")

        mock_metric_repo = AsyncMock()
        mock_metric_repo.upsert_metric = AsyncMock()

        mock_meta_adapter = AsyncMock()
        mock_meta_adapter.fetch_insights = AsyncMock(
            return_value=[
                {
                    "campaign_id": "camp_001",
                    "campaign_name": "Campaña Verano",
                    "impressions": 2000,
                    "clicks": 100,
                    "spend": "50.00",
                    "date_start": "2026-05-20",
                    "date_stop": "2026-05-20",
                }
            ]
        )

        published_events: list[Any] = []

        async def capture_publish(event: Any) -> None:
            published_events.append(event)

        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(side_effect=capture_publish)

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_all_active_meta_connections",
                new=AsyncMock(return_value=[sync_state]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_sync_repo",
                return_value=mock_sync_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_metric_repo",
                return_value=mock_metric_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_meta_adapter",
                return_value=mock_meta_adapter,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta import (
                channel_metrics_sync_meta,
            )

            await channel_metrics_sync_meta.__wrapped__(ctx)

        assert len(published_events) == 1
        from src.modules.vitalia.marketing.domain.events import ChannelSyncSucceeded

        assert isinstance(published_events[0], ChannelSyncSucceeded)

    @pytest.mark.asyncio
    async def test_channel_metrics_sync_meta_upserts_metrics_for_each_campaign(self) -> None:
        """Multiple campaigns per account → upsert called once per campaign row."""
        sync_state = _make_sync_state()
        mock_sync_repo = AsyncMock()
        mock_sync_repo.decrypt_token = AsyncMock(return_value=b"tk")

        mock_metric_repo = AsyncMock()
        mock_metric_repo.upsert_metric = AsyncMock()

        mock_meta_adapter = AsyncMock()
        mock_meta_adapter.fetch_insights = AsyncMock(
            return_value=[
                {
                    "campaign_id": "camp_a",
                    "campaign_name": "A",
                    "impressions": 100,
                    "clicks": 5,
                    "spend": "10.00",
                    "date_start": "2026-05-20",
                    "date_stop": "2026-05-20",
                },
                {
                    "campaign_id": "camp_b",
                    "campaign_name": "B",
                    "impressions": 200,
                    "clicks": 10,
                    "spend": "20.00",
                    "date_start": "2026-05-20",
                    "date_stop": "2026-05-20",
                },
            ]
        )

        mock_bus = AsyncMock()

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_all_active_meta_connections",
                new=AsyncMock(return_value=[sync_state]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_sync_repo",
                return_value=mock_sync_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_metric_repo",
                return_value=mock_metric_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta._get_meta_adapter",
                return_value=mock_meta_adapter,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.channel_metrics_sync_meta import (
                channel_metrics_sync_meta,
            )

            await channel_metrics_sync_meta.__wrapped__({})

        # 2 campaigns → 2 upsert calls
        assert mock_metric_repo.upsert_metric.call_count == 2


# ---------------------------------------------------------------------------
# channel_metrics_sync_google tests
# ---------------------------------------------------------------------------


class TestChannelMetricsSyncGoogle:
    """Tests for channel_metrics_sync_google cron job."""

    @pytest.mark.asyncio
    async def test_channel_metrics_sync_google_soft_fail_per_tenant(self) -> None:
        """One tenant Google Ads failure does not abort the cron for other tenants."""
        tenant_a = uuid.uuid4()
        clinic_a = uuid.uuid4()
        tenant_b = uuid.uuid4()
        clinic_b = uuid.uuid4()

        sync_state_a = _make_sync_state(tenant_id=tenant_a, clinic_id=clinic_a, provider="google_ads")
        sync_state_b = _make_sync_state(tenant_id=tenant_b, clinic_id=clinic_b, provider="google_ads")

        call_count = [0]

        async def fake_fetch(**kwargs: Any) -> list[dict[str, Any]]:
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("Google Ads quota exceeded")
            return [
                {
                    "campaign.id": "gcamp_1",
                    "campaign.name": "Campaña B",
                    "metrics.impressions": "500",
                    "metrics.clicks": "20",
                    "metrics.cost_micros": "10000000",
                    "segments.date": "2026-05-20",
                    "customer.currency_code": "MXN",
                }
            ]

        mock_sync_repo = AsyncMock()
        mock_sync_repo.decrypt_token = AsyncMock(return_value=b"google_token")
        mock_metric_repo = AsyncMock()
        mock_metric_repo.upsert_metric = AsyncMock()
        mock_google_adapter = AsyncMock()
        mock_google_adapter.fetch_campaign_metrics = AsyncMock(side_effect=fake_fetch)
        mock_bus = AsyncMock()

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google._get_all_active_google_connections",
                new=AsyncMock(return_value=[sync_state_a, sync_state_b]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google._get_sync_repo",
                return_value=mock_sync_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google._get_metric_repo",
                return_value=mock_metric_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google._get_google_adapter",
                return_value=mock_google_adapter,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.channel_metrics_sync_google import (
                channel_metrics_sync_google,
            )

            # Should not raise — soft-fail
            await channel_metrics_sync_google.__wrapped__(ctx)

        # Tenant B was processed
        assert mock_metric_repo.upsert_metric.call_count >= 1
        assert call_count[0] == 2

    @pytest.mark.asyncio
    async def test_channel_metrics_sync_google_publishes_failed_event_on_error(self) -> None:
        """ChannelSyncFailed published when Google Ads fetch fails."""
        sync_state = _make_sync_state(provider="google_ads")
        mock_sync_repo = AsyncMock()
        mock_sync_repo.decrypt_token = AsyncMock(return_value=b"goog_token")
        mock_metric_repo = AsyncMock()
        mock_google_adapter = AsyncMock()
        mock_google_adapter.fetch_campaign_metrics = AsyncMock(side_effect=RuntimeError("Invalid credentials"))

        published_events: list[Any] = []
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(side_effect=lambda e: published_events.append(e))

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google._get_all_active_google_connections",
                new=AsyncMock(return_value=[sync_state]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google._get_sync_repo",
                return_value=mock_sync_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google._get_metric_repo",
                return_value=mock_metric_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google._get_google_adapter",
                return_value=mock_google_adapter,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.channel_metrics_sync_google.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.channel_metrics_sync_google import (
                channel_metrics_sync_google,
            )

            await channel_metrics_sync_google.__wrapped__(ctx)

        assert len(published_events) == 1
        from src.modules.vitalia.marketing.domain.events import ChannelSyncFailed

        assert isinstance(published_events[0], ChannelSyncFailed)


# ---------------------------------------------------------------------------
# lucas_daily_analysis_sweep tests
# ---------------------------------------------------------------------------


class TestLucasDailyAnalysisSweep:
    """Tests for lucas_daily_analysis_sweep cron job.

    Post-fix (F-iter2-1/2/3): orchestrator mock uses run_daily_analysis returning
    AnalysisReport; cooldown filtering is post-call on stage_recommendations dicts;
    stage enum is BowtieStage (not .value string).
    """

    # ------------------------------------------------------------------
    # Helper: build a real AnalysisReport for mock returns
    # ------------------------------------------------------------------

    @staticmethod
    def _make_analysis_report(
        tenant_id: uuid.UUID,
        clinic_id: uuid.UUID,
        stage_recommendations: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Build a real AnalysisReport dataclass for orchestrator mock returns."""
        from src.modules.vitalia.agentic.lucas.application.services.lucas_orchestrator_service import (
            AnalysisReport,
        )

        recs = stage_recommendations or []
        # Build a minimal final_state TypedDict-like dict
        final_state: dict[str, Any] = {
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "analysis_date": "2026-05-20",
            "period": "2026-05",
            "stages_to_analyze": [],
            "stage_recommendations": recs,
            "attribution_matrix": None,
            "referrals_leaderboard": None,
            "iterations": len(recs),
            "task_complete": True,
            "messages": [],
            "last_error": None,
        }
        return AnalysisReport(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            analysis_date="2026-05-20",
            period="2026-05",
            stages_processed=len(recs),
            attribution_present=False,
            referrals_present=False,
            iterations=len(recs),
            task_complete=True,
            final_state=final_state,  # type: ignore[arg-type]
        )

    @pytest.mark.asyncio
    async def test_lucas_daily_analysis_sweep_skips_rejected_30d_cooldown(self) -> None:
        """SC-MK-02: Recommendations rejected within 30d cooldown are not published.

        Given a clinic has previously rejected 'increase_budget' recommendations
        within the last 30 days,
        When the daily sweep runs and orchestrator returns 'increase_budget' rec,
        Then NO LucasRecommendationGenerated event is published for that kind
        (cooldown suppression applies post-call).
        """

        # Simulate a recently-rejected recommendation (5 days ago — within 30d window)
        recent_rejection = _make_recommendation(
            status="rejected",
            recommendation_kind="increase_budget",
            rejected_at=datetime.now(UTC) - timedelta(days=5),
        )

        mock_rec_repo = AsyncMock()
        # Recent rejections query returns 1 rejection for 'increase_budget'
        mock_rec_repo.list_recent_rejections_by_kind = AsyncMock(return_value=[recent_rejection])
        mock_rec_repo.expire_stale_open = AsyncMock(return_value=0)

        tenant_id = _TENANT_ID
        clinic_id = _CLINIC_ID

        # Orchestrator returns a report with an 'increase_budget' recommendation
        # — cron should filter it out due to cooldown (post-call)
        cooled_rec = {
            "stage": "attraction",
            "recommendation_kind": "increase_budget",
            "recommendation_text": "Aumenta el presupuesto.",
            "confidence": 0.9,
            "supporting_data": {},
            "currency": "USD",
            "status": "generated",
            "priority": 1,
        }
        report = self._make_analysis_report(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage_recommendations=[cooled_rec],
        )

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run_daily_analysis = AsyncMock(return_value=report)

        published_events: list[Any] = []
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(side_effect=lambda e: published_events.append(e))

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_active_clinics",
                new=AsyncMock(return_value=[{"tenant_id": tenant_id, "clinic_id": clinic_id}]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_rec_repo",
                return_value=mock_rec_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_orchestrator",
                new=AsyncMock(return_value=mock_orchestrator),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep import (
                lucas_daily_analysis_sweep,
            )

            await lucas_daily_analysis_sweep.__wrapped__(ctx)

        # run_daily_analysis was called (not the old run_daily_sweep)
        mock_orchestrator.run_daily_analysis.assert_called_once()

        # 'increase_budget' is in cooldown → NO event published
        assert len(published_events) == 0, (
            "Expected 0 events: 'increase_budget' is in 30d cooldown set and should be filtered out"
        )

    @pytest.mark.asyncio
    async def test_lucas_daily_analysis_sweep_does_not_skip_old_rejections(self) -> None:
        """Recommendations rejected >30d ago are NOT in cooldown — events published."""
        # Old rejection not returned by list_recent_rejections_by_kind (repo filtered by since=)
        mock_rec_repo = AsyncMock()
        mock_rec_repo.list_recent_rejections_by_kind = AsyncMock(return_value=[])
        mock_rec_repo.expire_stale_open = AsyncMock(return_value=0)

        tenant_id = _TENANT_ID
        clinic_id = _CLINIC_ID

        # Orchestrator returns an 'increase_budget' rec — no cooldown → should be published
        old_rec = {
            "stage": "attraction",
            "recommendation_kind": "increase_budget",
            "recommendation_text": "Aumenta el presupuesto.",
            "confidence": 0.8,
            "supporting_data": {},
            "currency": "USD",
            "status": "generated",
            "priority": 1,
        }
        report = self._make_analysis_report(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage_recommendations=[old_rec],
        )

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run_daily_analysis = AsyncMock(return_value=report)

        published_events: list[Any] = []
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(side_effect=lambda e: published_events.append(e))

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_active_clinics",
                new=AsyncMock(return_value=[{"tenant_id": tenant_id, "clinic_id": clinic_id}]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_rec_repo",
                return_value=mock_rec_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_orchestrator",
                new=AsyncMock(return_value=mock_orchestrator),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep import (
                lucas_daily_analysis_sweep,
            )

            await lucas_daily_analysis_sweep.__wrapped__(ctx)

        # Old rejection NOT in cooldown → event published
        assert len(published_events) == 1, "Expected 1 event: 'increase_budget' is not in cooldown (old rejection)"

    @pytest.mark.asyncio
    async def test_lucas_daily_analysis_sweep_event_uses_bowtiestage_enum(self) -> None:
        """F-iter2-3: LucasRecommendationGenerated must receive BowtieStage enum not .value string.

        This test validates that stage string from stage_recommendations dict is
        properly converted to BowtieStage enum before being passed to the event,
        which would crash with AttributeError if given a plain string.
        """
        from src.modules.vitalia.marketing.domain.events import LucasRecommendationGenerated

        mock_rec_repo = AsyncMock()
        mock_rec_repo.list_recent_rejections_by_kind = AsyncMock(return_value=[])
        mock_rec_repo.expire_stale_open = AsyncMock(return_value=0)

        tenant_id = _TENANT_ID
        clinic_id = _CLINIC_ID

        # stage value is a string (as returned by LangGraph state dict)
        rec_with_string_stage = {
            "stage": "attraction",  # string — cron must convert to BowtieStage enum
            "recommendation_kind": "create_content",
            "recommendation_text": "Crea contenido educativo.",
            "confidence": 0.85,
            "supporting_data": {},
            "currency": "USD",
            "status": "generated",
            "priority": 2,
        }
        report = self._make_analysis_report(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage_recommendations=[rec_with_string_stage],
        )

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run_daily_analysis = AsyncMock(return_value=report)

        published_events: list[Any] = []
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(side_effect=lambda e: published_events.append(e))

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_active_clinics",
                new=AsyncMock(return_value=[{"tenant_id": tenant_id, "clinic_id": clinic_id}]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_rec_repo",
                return_value=mock_rec_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_orchestrator",
                new=AsyncMock(return_value=mock_orchestrator),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep import (
                lucas_daily_analysis_sweep,
            )

            # Would crash with AttributeError: 'str' object has no attribute 'value'
            # if stage is passed as string to LucasRecommendationGenerated(stage=...)
            await lucas_daily_analysis_sweep.__wrapped__(ctx)

        assert len(published_events) == 1
        event = published_events[0]
        assert isinstance(event, LucasRecommendationGenerated)
        # Verify the event payload has the stage value (string) from enum conversion
        assert event.payload["stage"] == "attraction"

    @pytest.mark.asyncio
    async def test_lucas_daily_analysis_sweep_soft_fail_per_clinic(self) -> None:
        """One clinic failure does not abort the sweep for other clinics."""
        mock_rec_repo = AsyncMock()
        mock_rec_repo.list_recent_rejections_by_kind = AsyncMock(return_value=[])
        mock_rec_repo.expire_stale_open = AsyncMock(return_value=0)

        clinic_a = {"tenant_id": uuid.uuid4(), "clinic_id": uuid.uuid4()}
        clinic_b = {"tenant_id": uuid.uuid4(), "clinic_id": uuid.uuid4()}

        call_count = [0]

        async def fake_run_analysis(**kwargs: Any) -> Any:
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("BudgetGuard: límite diario alcanzado")
            return self._make_analysis_report(
                tenant_id=clinic_b["tenant_id"],
                clinic_id=clinic_b["clinic_id"],
            )

        mock_orchestrator = AsyncMock()
        mock_orchestrator.run_daily_analysis = AsyncMock(side_effect=fake_run_analysis)
        mock_bus = AsyncMock()
        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_active_clinics",
                new=AsyncMock(return_value=[clinic_a, clinic_b]),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_rec_repo",
                return_value=mock_rec_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep._get_orchestrator",
                new=AsyncMock(return_value=mock_orchestrator),
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.lucas_daily_analysis_sweep import (
                lucas_daily_analysis_sweep,
            )

            # Should NOT raise — soft-fail per clinic
            await lucas_daily_analysis_sweep.__wrapped__(ctx)

        # Both clinics were attempted (run_daily_analysis called twice)
        assert call_count[0] == 2


# ---------------------------------------------------------------------------
# referrals_value_sync tests
# ---------------------------------------------------------------------------


class TestReferralsValueSync:
    """Tests for referrals_value_sync cron job."""

    @pytest.mark.asyncio
    async def test_referrals_value_sync_recomputes_conversion_value(self) -> None:
        """Referral conversion_value_cents is updated from completed appointments."""
        referral = _make_referral(status="converted")
        referral.conversion_value_cents = None

        mock_referral_repo = AsyncMock()
        mock_referral_repo.list_active_for_value_sync = AsyncMock(return_value=[referral])
        mock_referral_repo.save = AsyncMock(return_value=referral)

        # Appointments sum = 15000 cents
        mock_appointment_repo = AsyncMock()
        mock_appointment_repo.sum_conversion_value_for_patient = AsyncMock(return_value=15000)

        mock_bus = AsyncMock()
        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync._get_referral_repo",
                return_value=mock_referral_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync._get_appointment_repo",
                return_value=mock_appointment_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.referrals_value_sync import (
                referrals_value_sync,
            )

            await referrals_value_sync.__wrapped__(ctx)

        # save was called with updated conversion_value_cents
        mock_referral_repo.save.assert_called_once()
        saved_referral = mock_referral_repo.save.call_args[0][0]
        assert saved_referral.conversion_value_cents == 15000

    @pytest.mark.asyncio
    async def test_referrals_value_sync_publishes_referral_converted_event(self) -> None:
        """When referral transitions to converted, ReferralConverted event published."""
        referral = _make_referral(status="signed_up")
        referral.conversion_value_cents = None

        mock_referral_repo = AsyncMock()
        mock_referral_repo.list_active_for_value_sync = AsyncMock(return_value=[referral])
        mock_referral_repo.save = AsyncMock(return_value=referral)

        # Non-zero value — triggers converted transition
        mock_appointment_repo = AsyncMock()
        mock_appointment_repo.sum_conversion_value_for_patient = AsyncMock(return_value=20000)

        published_events: list[Any] = []
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(side_effect=lambda e: published_events.append(e))

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync._get_referral_repo",
                return_value=mock_referral_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync._get_appointment_repo",
                return_value=mock_appointment_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.referrals_value_sync import (
                referrals_value_sync,
            )

            await referrals_value_sync.__wrapped__(ctx)

        assert len(published_events) == 1
        from src.modules.vitalia.marketing.domain.events import ReferralConverted

        assert isinstance(published_events[0], ReferralConverted)

    @pytest.mark.asyncio
    async def test_referrals_value_sync_soft_fail_per_referral(self) -> None:
        """One referral processing failure does not abort the sync for other referrals."""
        referral_a = _make_referral(status="converted")
        referral_b = _make_referral(status="converted")

        mock_referral_repo = AsyncMock()
        mock_referral_repo.list_active_for_value_sync = AsyncMock(return_value=[referral_a, referral_b])
        mock_referral_repo.save = AsyncMock()

        call_count = [0]

        async def fake_sum(**kwargs: Any) -> int | None:
            call_count[0] += 1
            if call_count[0] == 1:
                raise RuntimeError("DB error en referral A")
            return 5000

        mock_appointment_repo = AsyncMock()
        mock_appointment_repo.sum_conversion_value_for_patient = AsyncMock(side_effect=fake_sum)

        mock_bus = AsyncMock()
        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync._get_referral_repo",
                return_value=mock_referral_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync._get_appointment_repo",
                return_value=mock_appointment_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.referrals_value_sync import (
                referrals_value_sync,
            )

            # Should NOT raise — soft-fail per referral
            await referrals_value_sync.__wrapped__(ctx)

        # Referral B was processed (save called once despite referral A failure)
        assert mock_referral_repo.save.call_count >= 1

    @pytest.mark.asyncio
    async def test_referrals_value_sync_no_event_when_value_unchanged(self) -> None:
        """No event published when conversion_value_cents does not change."""
        referral = _make_referral(status="converted")
        referral.conversion_value_cents = 10000  # already set

        mock_referral_repo = AsyncMock()
        mock_referral_repo.list_active_for_value_sync = AsyncMock(return_value=[referral])
        mock_referral_repo.save = AsyncMock(return_value=referral)

        mock_appointment_repo = AsyncMock()
        mock_appointment_repo.sum_conversion_value_for_patient = AsyncMock(
            return_value=10000  # same value
        )

        published_events: list[Any] = []
        mock_bus = AsyncMock()
        mock_bus.publish = AsyncMock(side_effect=lambda e: published_events.append(e))

        ctx: dict[str, Any] = {}

        with (
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync._get_referral_repo",
                return_value=mock_referral_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync._get_appointment_repo",
                return_value=mock_appointment_repo,
            ),
            patch(
                "src.modules.vitalia.marketing.jobs.referrals_value_sync.adapter_bus",
                mock_bus,
            ),
        ):
            from src.modules.vitalia.marketing.jobs.referrals_value_sync import (
                referrals_value_sync,
            )

            await referrals_value_sync.__wrapped__(ctx)

        # No change → no event
        assert len(published_events) == 0
