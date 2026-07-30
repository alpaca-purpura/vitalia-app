# cap: marketing.attribution-matrix-4-origins
# story-origin: TBD
"""MarketingService — bowtie funnel KPI snapshots.

Application layer — reads channel metrics persisted by the Lucas cron
and aggregates them into bowtie summary / stage detail / channel detail views.

HIPAA-lite:
  - Dual filter: tenant_id + clinic_id on all queries.
  - No PHI in channel metrics tables (marketing performance data only).

downstream-regression-na: brand-local marketing application service (vitalia-only)
"""

from __future__ import annotations

import datetime
from uuid import UUID

import structlog

from src.modules.vitalia.marketing.application.dtos.marketing_dtos import (
    BowtieSummaryResponse,
    ChannelDetailResponse,
    StageDetailResponse,
)
from src.modules.vitalia.marketing.domain.enums import BowtieStage

logger = structlog.get_logger()

# Mapping from bowtie stage to channel slugs (convention for Vitalia marketing)
# 5-stage health-clinic bowtie per spec § 2.1
_STAGE_CHANNEL_MAP: dict[BowtieStage, list[str]] = {
    BowtieStage.ATTRACTION: ["google_ads_search", "meta_ads_awareness", "google_ads_display"],
    BowtieStage.QUALIFICATION: ["google_ads_leads", "meta_ads_conversion", "remarketing"],
    BowtieStage.RESERVATION: ["email_nurture", "whatsapp_booking", "sms_reminder"],
    BowtieStage.ADOPTION: ["email_welcome", "whatsapp_followup", "post_visit_survey"],
    BowtieStage.EXPANSION: ["email_reengagement", "whatsapp_reactivation", "organic_referral"],
}


class MarketingService:
    """Application service for querying bowtie funnel KPI snapshots.

    Reads channel_metrics persisted by the Lucas cron jobs (via ChannelMetricRepository).
    Does NOT compute — only aggregates pre-computed rows.

    Methods:
      - bowtie_summary(): aggregated KPIs per stage for a date range
      - stage_detail(): channel breakdown for a specific stage
      - channel_detail(): individual channel metric rows for a date range
    """

    def __init__(self, *, channel_metric_repo: object) -> None:
        """Initialise with DI'd channel metrics repository.

        Args:
            channel_metric_repo: ChannelMetricRepository instance.
        """
        self._channel_metric_repo = channel_metric_repo

    async def bowtie_summary(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: datetime.date,
        period_end: datetime.date,
        currency: str | None = None,
    ) -> BowtieSummaryResponse:
        """Return aggregated bowtie funnel KPIs per stage for a date range.

        Reads all channel metrics in the period, aggregates by stage.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            period_start: First date of the period (inclusive).
            period_end: Last date of the period (inclusive).
            currency: ISO-4217 currency code from tenant locale (NEVER hardcoded).

        Returns:
            BowtieSummaryResponse with one StageDetailResponse per bowtie stage.
        """
        stages = []
        for stage in BowtieStage:
            stage_detail = await self.stage_detail(
                tenant_id=tenant_id,
                clinic_id=clinic_id,
                stage=stage,
                period_start=period_start,
                period_end=period_end,
                currency=currency,
            )
            stages.append(stage_detail)

        logger.info(
            "marketing.bowtie_summary",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            period_start=str(period_start),
            period_end=str(period_end),
        )

        return BowtieSummaryResponse(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
            stages=stages,
            currency=currency,
        )

    async def stage_detail(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        stage: BowtieStage,
        period_start: datetime.date,
        period_end: datetime.date,
        currency: str | None = None,
    ) -> StageDetailResponse:
        """Return channel breakdown for a specific bowtie stage.

        Queries channel metrics for channels mapped to the given stage.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            stage: BowtieStage to query.
            period_start: First date of the period (inclusive).
            period_end: Last date of the period (inclusive).
            currency: ISO-4217 currency code from tenant locale.

        Returns:
            StageDetailResponse with aggregated totals + per-channel breakdown.
        """
        channels = await self.channel_detail(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage=stage,
            period_start=period_start,
            period_end=period_end,
            currency=currency,
        )

        total_impressions = sum(c.impressions for c in channels)
        total_clicks = sum(c.clicks for c in channels)
        total_conversions = sum(c.conversions for c in channels)
        total_spend_cents = sum(c.spend_cents for c in channels)

        return StageDetailResponse(
            stage=stage,
            channels=channels,
            total_impressions=total_impressions,
            total_clicks=total_clicks,
            total_conversions=total_conversions,
            total_spend_cents=total_spend_cents,
            currency=currency,
        )

    async def channel_detail(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        stage: BowtieStage,
        period_start: datetime.date,
        period_end: datetime.date,
        currency: str | None = None,
    ) -> list[ChannelDetailResponse]:
        """Return individual channel metric rows for a stage and date range.

        Queries ChannelMetricRepository for all channel slugs mapped to the stage.
        Dual filter: tenant_id + clinic_id enforced by repository.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA dual filter).
            stage: BowtieStage to query channels for.
            period_start: First date of the period (inclusive).
            period_end: Last date of the period (inclusive).
            currency: ISO-4217 currency code from tenant locale.

        Returns:
            List of ChannelDetailResponse, one per channel metric row.
        """
        channel_slugs = _STAGE_CHANNEL_MAP.get(stage, [])

        models = await self._channel_metric_repo.list_for_stage(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            channel_slugs=channel_slugs,
            period_start=period_start,
            period_end=period_end,
        )

        result = []
        for model in models:
            result.append(
                ChannelDetailResponse(
                    id=model.id,
                    tenant_id=model.tenant_id,
                    clinic_id=model.clinic_id,
                    provider=model.provider,
                    channel_slug=model.channel_slug,
                    campaign_id=model.campaign_id,
                    campaign_name=model.campaign_name,
                    metric_date=model.metric_date,
                    impressions=model.impressions,
                    clicks=model.clicks,
                    conversions=model.conversions,
                    spend_cents=model.spend_cents,
                    currency=model.currency or currency,
                )
            )

        logger.info(
            "marketing.channel_detail",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            stage=stage.value,
            channel_count=len(result),
        )

        return result
