"""Tests for ChannelMetricRepository.

Covers:
- upsert_metric: ON CONFLICT DO UPDATE (natural key deduplication)
- list_for_scope: dual filter enforced
- HIPAA-lite dual filter: tenant_id + clinic_id on all queries
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

from src.modules.vitalia.marketing.domain.enums import ProviderSlug
from src.modules.vitalia.marketing.infrastructure.models.channel_metric_model import (
    ChannelMetricModel,
)
from src.modules.vitalia.marketing.infrastructure.repositories.channel_metric_repository import (
    ChannelMetricRepository,
)


def _make_model(
    *,
    tenant_id: uuid.UUID,
    clinic_id: uuid.UUID,
    provider: str = "google_ads",
    channel_slug: str = "google_ads_search",
    metric_date: date | None = None,
    campaign_id: str | None = None,
    impressions: int = 100,
    clicks: int = 10,
    spend_cents: int = 5000,
    deleted_at: datetime | None = None,
) -> ChannelMetricModel:
    """Factory for ChannelMetricModel test instances."""
    now = datetime.now(UTC)
    model = ChannelMetricModel()
    model.id = uuid.uuid4()
    model.tenant_id = tenant_id
    model.clinic_id = clinic_id
    model.provider = provider
    model.channel_slug = channel_slug
    model.metric_date = metric_date or date.today()
    model.campaign_id = campaign_id
    model.campaign_name = None
    model.impressions = impressions
    model.clicks = clicks
    model.conversions = 1
    model.spend_cents = spend_cents
    model.currency = "USD"
    model.raw_payload = None
    model.created_at = now
    model.updated_at = now
    model.deleted_at = deleted_at
    return model


class TestChannelMetricRepositoryInit:
    """Repository construction uses scope_field='clinic_id'."""

    def test_inherits_compound_scope_repository_base(self) -> None:
        """ChannelMetricRepository must subclass CompoundScopeRepositoryBase."""
        from luana_core_platform.repositories.compound_scope_repository import (
            CompoundScopeRepositoryBase,
        )

        assert issubclass(ChannelMetricRepository, CompoundScopeRepositoryBase)

    def test_model_class_var_is_set(self) -> None:
        """MODEL ClassVar must be ChannelMetricModel."""
        assert ChannelMetricRepository.MODEL is ChannelMetricModel

    def test_scope_field_is_clinic_id(self) -> None:
        """scope_field must be 'clinic_id'."""
        session = AsyncMock()
        repo = ChannelMetricRepository(session=session)
        assert repo._scope_field == "clinic_id"  # noqa: SLF001


class TestUpsertMetric:
    """upsert_metric: ON CONFLICT DO UPDATE on natural key."""

    async def test_upsert_signature_accepted(self) -> None:
        """upsert_metric accepts the required parameters."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(return_value=MagicMock())

        repo = ChannelMetricRepository(session=session)
        today = date.today()

        # Should not raise
        await repo.upsert_metric(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            provider=ProviderSlug.GOOGLE_ADS,
            channel_slug="google_ads_search",
            metric_date=today,
            impressions=500,
            clicks=25,
            conversions=3,
            spend_cents=12000,
            currency="USD",
            campaign_id="camp_abc",
            campaign_name="Campaña Dientes",
            raw_payload={"source": "google_ads_api"},
        )

        session.execute.assert_called_once()

    async def test_upsert_without_campaign_id(self) -> None:
        """upsert_metric works when campaign_id is None."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(return_value=MagicMock())

        repo = ChannelMetricRepository(session=session)
        today = date.today()

        await repo.upsert_metric(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            provider=ProviderSlug.META_ADS,
            channel_slug="meta_ads_feed",
            metric_date=today,
            impressions=200,
            clicks=15,
            conversions=2,
            spend_cents=8000,
            currency="USD",
            campaign_id=None,
            campaign_name=None,
            raw_payload=None,
        )

        session.execute.assert_called_once()

    async def test_upsert_uses_on_conflict_do_update(self) -> None:
        """Upsert SQL must use ON CONFLICT DO UPDATE pattern."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()
        session.execute = AsyncMock(return_value=MagicMock())

        repo = ChannelMetricRepository(session=session)

        await repo.upsert_metric(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            provider=ProviderSlug.GOOGLE_ADS,
            channel_slug="google_ads_search",
            metric_date=date.today(),
            impressions=100,
            clicks=10,
            conversions=1,
            spend_cents=5000,
            currency="USD",
            campaign_id=None,
            campaign_name=None,
            raw_payload=None,
        )

        call_args = session.execute.call_args
        assert call_args is not None
        stmt = call_args[0][0]
        stmt_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        # Must contain ON CONFLICT or equivalent upsert marker
        assert "ON CONFLICT" in stmt_str.upper() or "on_conflict" in str(type(stmt)).lower(), (
            f"Upsert must use ON CONFLICT DO UPDATE. Got: {stmt_str[:200]}"
        )


class TestListForScope:
    """list_for_scope: returns metrics for tenant+clinic."""

    async def test_list_for_scope_dual_filter(self) -> None:
        """list_for_scope enforces tenant_id + clinic_id dual filter."""
        tenant_id = uuid.uuid4()
        clinic_id = uuid.uuid4()
        session = AsyncMock()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute.return_value = mock_result

        repo = ChannelMetricRepository(session=session)
        await repo.list_for_scope(tenant_id=tenant_id, scope_id=clinic_id)

        session.execute.assert_called_once()
        stmt = session.execute.call_args[0][0]
        stmt_str = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        tenant_hex = str(tenant_id).replace("-", "")
        clinic_hex = str(clinic_id).replace("-", "")
        assert tenant_hex in stmt_str.replace("-", ""), f"tenant_id not in query: {stmt_str}"
        assert clinic_hex in stmt_str.replace("-", ""), f"clinic_id not in query: {stmt_str}"
