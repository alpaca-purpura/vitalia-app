# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""ChannelMetricRepository — dual-scope async repository with upsert.

Subclasses ``CompoundScopeRepositoryBase`` from engine (luana-core-platform v0.4.0).
scope_field="clinic_id" enforces HIPAA-lite dual filter (tenant_id + clinic_id).

Key feature: upsert_metric() uses ON CONFLICT DO UPDATE on the natural key
  (tenant_id, clinic_id, provider, channel_slug, campaign_id, metric_date)
to handle idempotent ETL re-runs.

No PHI in channel metrics (campaign attribution data only).

downstream-regression-na: brand-local marketing repository (vitalia-only module)
"""

from __future__ import annotations

from datetime import date
from typing import ClassVar
from uuid import UUID, uuid4

import structlog
from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from src.modules.vitalia.marketing.domain.enums import ProviderSlug
from src.modules.vitalia.marketing.infrastructure.models.channel_metric_model import (
    ChannelMetricModel,
)

logger = structlog.get_logger()


class ChannelMetricRepository(CompoundScopeRepositoryBase[ChannelMetricModel, UUID]):
    """Async repository for ChannelMetric (daily ad performance snapshots).

    Dual-scope isolation: tenant_id (multitenant) + clinic_id (HIPAA-lite).
    scope_field="clinic_id" per vitalia brand convention.

    Key method:
      upsert_metric: ON CONFLICT DO UPDATE on natural key for idempotent ETL.
    """

    MODEL: ClassVar[type[ChannelMetricModel]] = ChannelMetricModel

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize with clinic_id as the secondary scope axis."""
        super().__init__(session=session, scope_field="clinic_id")

    async def upsert_metric(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        provider: ProviderSlug,
        channel_slug: str,
        metric_date: date,
        impressions: int,
        clicks: int,
        conversions: int,
        spend_cents: int,
        currency: str | None,
        campaign_id: str | None,
        campaign_name: str | None,
        raw_payload: dict | None,
    ) -> None:
        """Upsert a daily channel metric snapshot.

        Uses PostgreSQL ON CONFLICT DO UPDATE on the natural unique key:
          (tenant_id, clinic_id, provider, channel_slug, campaign_id, metric_date)

        If a row with this natural key already exists (e.g. ETL re-run for
        the same day), the metrics columns are updated in place. This makes
        ETL runs idempotent.

        currency: ISO 4217 code from provider (e.g. "USD", "MXN") — never
        hardcoded per currency-handling.md.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (secondary scope, HIPAA-lite dual filter).
            provider: Advertising provider enum.
            channel_slug: Provider-specific channel identifier string.
            metric_date: Date this snapshot covers.
            impressions: Total impressions for the day.
            clicks: Total clicks for the day.
            conversions: Total conversions for the day.
            spend_cents: Total spend in integer cents (no float precision issues).
            currency: ISO 4217 currency from provider response (may be None).
            campaign_id: Provider campaign identifier (None = aggregate).
            campaign_name: Human-readable campaign name (None = aggregate).
            raw_payload: Raw provider API response dict for audit (no PHI).
        """
        values = {
            "id": uuid4(),
            "tenant_id": tenant_id,
            "clinic_id": clinic_id,
            "provider": provider.value,
            "channel_slug": channel_slug,
            "metric_date": metric_date,
            "campaign_id": campaign_id,
            "campaign_name": campaign_name,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "spend_cents": spend_cents,
            "currency": currency,
            "raw_payload": raw_payload,
        }

        stmt = (
            pg_insert(ChannelMetricModel)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_vitalia_channel_metrics_natural_key",
                set_={
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "spend_cents": spend_cents,
                    "currency": currency,
                    "campaign_name": campaign_name,
                    "raw_payload": raw_payload,
                    "updated_at": func.now(),
                },
            )
        )

        await self._session.execute(stmt)
        logger.info(
            "channel_metric.upsert",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            provider=provider.value,
            channel_slug=channel_slug,
            metric_date=str(metric_date),
            campaign_id=campaign_id,
        )

    async def list_for_stage(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        channel_slugs: list[str],
        period_start: date,
        period_end: date,
    ) -> list[ChannelMetricModel]:
        """Return channel metric rows for a list of channel slugs within a date range.

        Used by MarketingService.stage_detail() / channel_detail() to aggregate
        per-stage metrics from persisted channel data.

        Dual filter: tenant_id + clinic_id (HIPAA-lite).
        Excludes soft-deleted rows.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            channel_slugs: List of channel_slug values to filter by.
            period_start: First date of the period (inclusive).
            period_end: Last date of the period (inclusive).

        Returns:
            List of ChannelMetricModel rows matching the filter.
        """
        if not channel_slugs:
            return []

        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.channel_slug.in_(channel_slugs))
            .where(self.MODEL.metric_date >= period_start)
            .where(self.MODEL.metric_date <= period_end)
            .where(self.MODEL.deleted_at.is_(None))
            .order_by(self.MODEL.metric_date.desc(), self.MODEL.channel_slug)
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        logger.info(
            "channel_metric.list_for_stage",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            channel_count=len(channel_slugs),
            row_count=len(rows),
        )
        return rows
