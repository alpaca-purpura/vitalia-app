# cap: agentic.lucas-daily-analysis
# story-origin: TBD
"""Lucas application service — LucasReferralsService.

Pure DB service — no LLM calls. Queries analytics engine adapter for
referrals leaderboard data and persists snapshot.

HIPAA-lite:
  - top_referrers contains referrer_id (UUID hash) only — no patient names.
  - Clinic_id ALWAYS passed to repo (dual filter).
"""

from __future__ import annotations

import datetime as dt
from typing import Any, Protocol
from uuid import UUID, uuid4

import structlog

from src.modules.vitalia.agentic.lucas.domain.entities.referrals_leaderboard_snapshot import (
    ReferralsLeaderboardSnapshot,
)
from src.modules.vitalia.agentic.lucas.infrastructure.adapters.analytics_engine_query_adapter import (
    AnalyticsEngineQueryAdapter,
)
from src.modules.vitalia.agentic.lucas.infrastructure.repositories.referrals_leaderboard_snapshot_repository import (
    ReferralsLeaderboardSnapshotRepository,
)

logger = structlog.get_logger()


class TenantLocaleProtocol(Protocol):
    """Minimal locale protocol."""

    currency: str
    timezone: str


class LucasReferralsService:
    """Application service for computing referrals leaderboard snapshots.

    Pure DB — no LLM. Queries analytics engine and persists snapshot.

    Flow:
        1. AnalyticsEngineQueryAdapter.get_referrals_data() — engine query.
        2. Build ReferralsLeaderboardSnapshot.
        3. repo.save() — persist with tenant_id + clinic_id.
        4. Return entity.

    HIPAA: top_referrers list uses referrer_id (UUID) only — no patient names.
    """

    def __init__(
        self,
        *,
        repo: ReferralsLeaderboardSnapshotRepository,
        analytics_adapter: AnalyticsEngineQueryAdapter,
    ) -> None:
        """Initialise with DI'd dependencies."""
        self._repo = repo
        self._analytics_adapter = analytics_adapter

    async def compute_referrals(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: dt.date,
        period_end: dt.date,
        locale: TenantLocaleProtocol,
    ) -> ReferralsLeaderboardSnapshot:
        """Compute and persist referrals leaderboard snapshot.

        Args:
            tenant_id: Tenant UUID.
            clinic_id: Clinic UUID (HIPAA-lite dual filter).
            period_start: Start of period (inclusive).
            period_end: End of period (inclusive).
            locale: TenantLocale — available for future currency-related metrics.

        Returns:
            ReferralsLeaderboardSnapshot with top_referrers using UUIDs only.
        """
        now = dt.datetime.now(tz=dt.timezone.utc)

        # Query analytics engine (READ-ONLY)
        referrals_data = await self._analytics_adapter.get_referrals_data(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
        )

        top_referrers: list[dict[str, Any]] = referrals_data.get("top_referrers", [])
        total_referrals: int = int(referrals_data.get("total_referrals", 0))
        total_converted: int = int(referrals_data.get("total_converted", 0))

        entity = ReferralsLeaderboardSnapshot(
            id=uuid4(),
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            period_start=period_start,
            period_end=period_end,
            top_referrers=top_referrers,
            total_referrals=total_referrals,
            total_converted=total_converted,
            computed_at=now,
            deleted_at=None,
        )

        saved = await self._repo.save(entity)

        logger.info(
            "lucas_referrals_snapshot_saved",
            snapshot_id=str(saved.id),
            tenant_id=str(tenant_id),
            period_start=str(period_start),
            total_referrals=total_referrals,
        )

        return saved
