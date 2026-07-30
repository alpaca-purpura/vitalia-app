# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas infrastructure — ReferralsLeaderboardSnapshotRepository.

SQLAlchemy 2.0 async repository for ReferralsLeaderboardSnapshotModel.

HIPAA-lite dual filter: ALL queries filter BOTH tenant_id AND clinic_id.
Soft-delete only: deleted_at IS NULL always included.
No PHI: referrer data uses UUID referrer_id only, no names.

See vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo.
"""

from __future__ import annotations

import datetime as dt
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.agentic.lucas.domain.entities.referrals_leaderboard_snapshot import (
    ReferralsLeaderboardSnapshot,
)
from src.modules.vitalia.agentic.lucas.persistence.models.referrals_leaderboard_snapshot import (
    ReferralsLeaderboardSnapshotModel,
)

logger = structlog.get_logger()


def _model_to_entity(m: ReferralsLeaderboardSnapshotModel) -> ReferralsLeaderboardSnapshot:
    """Map ORM model → domain entity."""
    return ReferralsLeaderboardSnapshot(
        id=m.id,
        tenant_id=m.tenant_id,
        clinic_id=m.clinic_id,
        period_start=m.period_start,
        period_end=m.period_end,
        top_referrers=m.top_referrers or [],
        total_referrals=m.total_referrals,
        total_converted=m.total_converted,
        computed_at=m.computed_at,
        deleted_at=m.deleted_at,
    )


def _entity_to_model(e: ReferralsLeaderboardSnapshot) -> ReferralsLeaderboardSnapshotModel:
    """Map domain entity → ORM model."""
    return ReferralsLeaderboardSnapshotModel(
        id=e.id,
        tenant_id=e.tenant_id,
        clinic_id=e.clinic_id,
        period_start=e.period_start,
        period_end=e.period_end,
        top_referrers=e.top_referrers,
        total_referrals=e.total_referrals,
        total_converted=e.total_converted,
        computed_at=e.computed_at,
        deleted_at=e.deleted_at,
    )


class ReferralsLeaderboardSnapshotRepository:
    """Async repository for referrals leaderboard snapshots.

    Every method accepts tenant_id + clinic_id (HIPAA-lite dual filter).
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialise with async SQLAlchemy session."""
        self._session = session

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> ReferralsLeaderboardSnapshot | None:
        """Fetch single snapshot by id — dual filter mandatory."""
        stmt = select(ReferralsLeaderboardSnapshotModel).where(
            ReferralsLeaderboardSnapshotModel.id == entity_id,
            ReferralsLeaderboardSnapshotModel.tenant_id == tenant_id,
            ReferralsLeaderboardSnapshotModel.clinic_id == clinic_id,
            ReferralsLeaderboardSnapshotModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def get_latest_for_period(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        period_start: dt.date,
        period_end: dt.date,
    ) -> ReferralsLeaderboardSnapshot | None:
        """Get most recent snapshot for given period — dual filter mandatory."""
        stmt = (
            select(ReferralsLeaderboardSnapshotModel)
            .where(
                ReferralsLeaderboardSnapshotModel.tenant_id == tenant_id,
                ReferralsLeaderboardSnapshotModel.clinic_id == clinic_id,
                ReferralsLeaderboardSnapshotModel.period_start == period_start,
                ReferralsLeaderboardSnapshotModel.period_end == period_end,
                ReferralsLeaderboardSnapshotModel.deleted_at.is_(None),
            )
            .order_by(ReferralsLeaderboardSnapshotModel.computed_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def list_for_tenant(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        limit: int = 12,
    ) -> list[ReferralsLeaderboardSnapshot]:
        """List recent snapshots for tenant — dual filter mandatory."""
        stmt = (
            select(ReferralsLeaderboardSnapshotModel)
            .where(
                ReferralsLeaderboardSnapshotModel.tenant_id == tenant_id,
                ReferralsLeaderboardSnapshotModel.clinic_id == clinic_id,
                ReferralsLeaderboardSnapshotModel.deleted_at.is_(None),
            )
            .order_by(ReferralsLeaderboardSnapshotModel.period_start.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def save(self, entity: ReferralsLeaderboardSnapshot) -> ReferralsLeaderboardSnapshot:
        """Persist a referrals leaderboard snapshot (insert or update)."""
        model = _entity_to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()
        logger.info(
            "referrals_leaderboard_saved",
            snapshot_id=str(entity.id),
            tenant_id=str(entity.tenant_id),
            period_start=str(entity.period_start),
            total_referrals=entity.total_referrals,
        )
        return _model_to_entity(merged)
