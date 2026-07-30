# cap: marketing.lucas-stage-recommendations
# story-origin: TBD
"""LucasRecommendationRepository — dual-scope async repository.

Subclasses ``CompoundScopeRepositoryBase`` from engine (luana-core-platform v0.4.0).
scope_field="clinic_id" enforces HIPAA-lite dual filter (tenant_id + clinic_id).

All queries exclude soft-deleted rows (deleted_at IS NULL).
No PHI in marketing recommendation tables.

downstream-regression-na: brand-local marketing repository (vitalia-only module)
"""

from __future__ import annotations

from datetime import datetime
from typing import ClassVar
from uuid import UUID

import structlog
from luana_core_platform.repositories.compound_scope_repository import CompoundScopeRepositoryBase
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.infrastructure.models.lucas_recommendation_model import (
    LucasRecommendationModel,
)
from src.modules.vitalia.marketing.domain.enums import BowtieStage, RecommendationStatus

logger = structlog.get_logger()


class LucasRecommendationRepository(CompoundScopeRepositoryBase[LucasRecommendationModel, UUID]):
    """Async repository for LucasRecommendation (marketing AI recommendations).

    Dual-scope isolation: tenant_id (multitenant) + clinic_id (HIPAA-lite).
    scope_field="clinic_id" per vitalia brand convention.

    Custom queries beyond base get_by_id / list_for_scope:
      - list_open_by_stage: OPEN recs for a stage (Lucas panel)
      - list_pending_undo_expired: APPROVED recs past undo window (cron sweep)
    """

    MODEL: ClassVar[type[LucasRecommendationModel]] = LucasRecommendationModel

    def __init__(self, *, session: AsyncSession) -> None:
        """Initialize with clinic_id as the secondary scope axis."""
        super().__init__(session=session, scope_field="clinic_id")

    async def list_open_by_stage(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        stage: BowtieStage,
        limit: int = 3,
    ) -> list[LucasRecommendationModel]:
        """Return OPEN recommendations for a given bowtie stage.

        Used by the Lucas recommendations panel to surface actionable
        suggestions to clinic users.

        Dual filter: tenant_id + clinic_id (HIPAA-lite).
        Excludes soft-deleted and non-OPEN records.
        Ordered by priority DESC (highest urgency first).

        Args:
            tenant_id: Tenant UUID for root isolation.
            clinic_id: Clinic UUID for secondary isolation.
            stage: Bowtie funnel stage to filter by (BowtieStage enum).
            limit: Max recommendations to return (default 3 per panel slot).

        Returns:
            List of LucasRecommendationModel, ordered by priority DESC.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.status == RecommendationStatus.OPEN.value)
            .where(self.MODEL.stage == stage.value)
            .where(self.MODEL.deleted_at.is_(None))
            .order_by(self.MODEL.priority.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        logger.info(
            "lucas_recommendation.list_open_by_stage",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            stage=stage.value,
            count=len(rows),
        )
        return rows

    async def save(self, model: LucasRecommendationModel) -> LucasRecommendationModel:
        """Persist a LucasRecommendationModel (insert or update).

        Uses session.merge() to handle both new and existing records.
        Caller must ensure the model has tenant_id + clinic_id set correctly
        before calling save() — dual filter is enforced by get_by_id() upstream.

        Flushes the session to make changes visible within the transaction.
        Commit is handled by the FastAPI dependency (per-request transaction).

        Args:
            model: LucasRecommendationModel to persist.

        Returns:
            Merged (refreshed) model instance.
        """
        merged = await self._session.merge(model)
        await self._session.flush()
        logger.info(
            "lucas_recommendation.saved",
            recommendation_id=str(merged.id),
            tenant_id=str(merged.tenant_id),
            status=merged.status,
        )
        return merged

    async def list_recent_rejections_by_kind(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        since: datetime,
    ) -> list[LucasRecommendationModel]:
        """Return REJECTED recommendations for a clinic rejected after `since`.

        Used by the daily sweep cron to build the 30-day cooldown set of
        recommendation_kind values that should not be regenerated today.

        Dual filter: tenant_id + clinic_id (HIPAA-lite).
        Only returns REJECTED rows with rejected_at >= since.
        Excludes soft-deleted rows.

        Args:
            tenant_id: Tenant UUID for root isolation.
            clinic_id: Clinic UUID for secondary isolation.
            since: Datetime threshold — only rejections on or after this date.

        Returns:
            List of LucasRecommendationModel with status=REJECTED within window.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.status == RecommendationStatus.REJECTED.value)
            .where(self.MODEL.rejected_at.isnot(None))
            .where(self.MODEL.rejected_at >= since)
            .where(self.MODEL.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        logger.info(
            "lucas_recommendation.list_recent_rejections_by_kind",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            since=since.isoformat(),
            count=len(rows),
        )
        return rows

    async def expire_stale_open(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        now: datetime,
    ) -> int:
        """Soft-expire OPEN recommendations whose expires_at is in the past.

        Updates status from 'open' to 'expired' for stale recommendations.
        Used by the daily sweep cron before generating new recommendations.

        Dual filter: tenant_id + clinic_id (HIPAA-lite).

        Args:
            tenant_id: Tenant UUID for root isolation.
            clinic_id: Clinic UUID for secondary isolation.
            now: Current UTC datetime (passed explicitly for testability).

        Returns:
            Number of rows updated.
        """
        from sqlalchemy import update  # noqa: PLC0415

        scope_attr = self._scope_attr()
        stmt = (
            update(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.status == RecommendationStatus.OPEN.value)
            .where(self.MODEL.expires_at < now)
            .where(self.MODEL.deleted_at.is_(None))
            .values(status=RecommendationStatus.EXPIRED.value)
        )
        result = await self._session.execute(stmt)
        count: int = result.rowcount  # type: ignore[attr-defined]
        logger.info(
            "lucas_recommendation.expire_stale_open",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            expired_count=count,
        )
        return count

    async def list_pending_undo_expired(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        now: datetime,
    ) -> list[LucasRecommendationModel]:
        """Return APPROVED recommendations whose 5-minute undo window has expired.

        Used by a cron job to finalize approved recommendations after the undo
        window passes (transition from pending-confirmed to fully applied).

        Dual filter: tenant_id + clinic_id (HIPAA-lite).
        Filters: status=APPROVED AND undo_until < now AND deleted_at IS NULL.

        Args:
            tenant_id: Tenant UUID for root isolation.
            clinic_id: Clinic UUID for secondary isolation.
            now: Current UTC datetime (passed explicitly for testability).

        Returns:
            List of LucasRecommendationModel with expired undo windows.
        """
        scope_attr = self._scope_attr()
        stmt = (
            select(self.MODEL)
            .where(self.MODEL.tenant_id == tenant_id)
            .where(scope_attr == clinic_id)
            .where(self.MODEL.status == RecommendationStatus.APPROVED.value)
            .where(self.MODEL.undo_until.isnot(None))
            .where(self.MODEL.undo_until < now)
            .where(self.MODEL.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        logger.info(
            "lucas_recommendation.list_pending_undo_expired",
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            count=len(rows),
        )
        return rows
