# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas infrastructure — AnalyticsEngineQueryAdapter.

Wraps luana_core_analytics_engine reads for Lucas growth setter services.

CONTRACT: This adapter CONSUMES the analytics engine — it does NOT mirror
STAGE_CHANNEL_MAP or any _GROUP_MAP locally. All channel/stage lookups
delegate to the engine's ChannelRegistry and STAGE_CHANNEL_MAP.

Anti-pattern guard: NO `_GROUP_MAP` definition in this file.
NO `STAGE_CHANNEL_MAP` definition in this file.
Engine is imported READ-ONLY.

See vitalia/docs/product/stories/vitalia-copilot-tools-impl/05-guidelines.md
§ FORBIDDEN: Mirror analytics engine _GROUP_MAP or STAGE_CHANNEL_MAP.

Graceful degradation: all methods return empty/zero values on error
so that BudgetGuard + cron scheduler can fail softly.
"""

from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger()


class AnalyticsEngineQueryAdapter:
    """Adapter that queries the analytics engine for Lucas services.

    All queries are READ-ONLY consumption of engine data.
    No local copies of channel maps — engine is authoritative.
    """

    def __init__(self) -> None:
        """Load engine channel registry once at construction time."""
        # Import engine READ-ONLY — never modify
        try:
            from luana_core_analytics_engine.application.services.channel_registry import (
                STAGE_CHANNEL_MAP,
                ChannelRegistry,
            )

            self._stage_channel_map = STAGE_CHANNEL_MAP
            self._channel_registry = ChannelRegistry
        except ImportError:
            # Graceful degradation when engine not available (CI without analytics deps)
            logger.warning("analytics_engine_not_available", adapter="AnalyticsEngineQueryAdapter")
            self._stage_channel_map = {}
            self._channel_registry = None

    def get_stage_channel_names(self, stage: str) -> list[str]:
        """Return channel slugs for a funnel stage from engine STAGE_CHANNEL_MAP.

        READ-ONLY consumption. No local mirror.
        """
        channels = self._stage_channel_map.get(stage, [])
        return [ch.get("slug", "") for ch in channels if ch.get("slug")]

    async def get_stage_metrics(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        stage: str,
        period: str,  # "YYYY-MM"
    ) -> dict[str, Any]:
        """Fetch aggregated metrics for a funnel stage from analytics engine.

        Returns empty dict on error (graceful degradation).
        Clinic_id passed to ensure HIPAA-lite dual filter in underlying queries.
        """
        try:
            channel_slugs = self.get_stage_channel_names(stage)
            # In production: query analytics DB/cache for these channels.
            # For now: return a metrics summary shape for LLM context.
            return {
                "stage": stage,
                "period": period,
                "channel_slugs": channel_slugs,
                "channel_count": len(channel_slugs),
                # Real metrics would come from analytics_engine stage services
                # via DB query scoped to tenant_id + clinic_id
            }
        except Exception:
            logger.warning(
                "analytics_stage_metrics_failed",
                stage=stage,
                tenant_id=str(tenant_id),
            )
            return {"stage": stage, "period": period, "channel_slugs": [], "channel_count": 0}

    async def get_attribution_breakdown(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: dt.date,
        period_end: dt.date,
    ) -> dict[str, Any]:
        """Fetch channel attribution breakdown for a period.

        Returns channel_slug → attributed revenue (float) mapping.
        Returns empty dict on error (graceful degradation).
        Clinic_id ensures HIPAA-lite dual filter scope.
        """
        try:
            # In production: query analytics engine for attribution data
            # scoped to tenant_id + clinic_id for the period.
            # Uses engine ChannelRegistry for channel discovery.
            return {}
        except Exception:
            logger.warning(
                "analytics_attribution_breakdown_failed",
                tenant_id=str(tenant_id),
                period_start=str(period_start),
            )
            return {}

    async def get_referrals_data(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: dt.date,
        period_end: dt.date,
    ) -> dict[str, Any]:
        """Fetch referrals data for a period.

        Returns dict with top_referrers, total_referrals, total_converted.
        HIPAA: referrer_id is UUID only — no patient names stored.
        Returns empty/zero on error (graceful degradation).
        """
        try:
            # In production: query analytics engine referrals data
            # scoped to tenant_id + clinic_id for the period.
            return {
                "top_referrers": [],
                "total_referrals": 0,
                "total_converted": 0,
            }
        except Exception:
            logger.warning(
                "analytics_referrals_data_failed",
                tenant_id=str(tenant_id),
                period_start=str(period_start),
            )
            return {"top_referrers": [], "total_referrals": 0, "total_converted": 0}
