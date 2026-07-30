# cap: agentic.eval-goldens-slice-1
# story-origin: TBD
"""Lucas infrastructure — AttributionMatrixSnapshotRepository.

SQLAlchemy 2.0 async repository for AttributionMatrixSnapshotModel.

HIPAA-lite dual filter: ALL queries filter BOTH tenant_id AND clinic_id.
Soft-delete only: deleted_at IS NULL always included.
Currency from tenant locale — never hardcoded.

See vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.agentic.lucas.domain.entities.attribution_matrix_snapshot import (
    AttributionMatrixSnapshot,
)
from src.modules.vitalia.agentic.lucas.persistence.models.attribution_matrix_snapshot import (
    AttributionMatrixSnapshotModel,
)

logger = structlog.get_logger()


def _model_to_entity(m: AttributionMatrixSnapshotModel) -> AttributionMatrixSnapshot:
    """Map ORM model → domain entity."""
    raw_revenue = m.total_attributed_revenue
    try:
        revenue = Decimal(str(raw_revenue)) if raw_revenue is not None else Decimal("0.00")
    except Exception:
        revenue = Decimal("0.00")
    return AttributionMatrixSnapshot(
        id=m.id,
        tenant_id=m.tenant_id,
        clinic_id=m.clinic_id,
        period_start=m.period_start,
        period_end=m.period_end,
        channel_breakdown=m.channel_breakdown or {},
        total_attributed_revenue=revenue,
        currency=m.currency,
        computed_at=m.computed_at,
        deleted_at=m.deleted_at,
    )


def _entity_to_model(e: AttributionMatrixSnapshot) -> AttributionMatrixSnapshotModel:
    """Map domain entity → ORM model."""
    return AttributionMatrixSnapshotModel(
        id=e.id,
        tenant_id=e.tenant_id,
        clinic_id=e.clinic_id,
        period_start=e.period_start,
        period_end=e.period_end,
        channel_breakdown=e.channel_breakdown,
        total_attributed_revenue=e.total_attributed_revenue,
        currency=e.currency,
        computed_at=e.computed_at,
        deleted_at=e.deleted_at,
    )


class AttributionMatrixSnapshotRepository:
    """Async repository for attribution matrix snapshots.

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
    ) -> AttributionMatrixSnapshot | None:
        """Fetch single snapshot by id — dual filter mandatory."""
        stmt = select(AttributionMatrixSnapshotModel).where(
            AttributionMatrixSnapshotModel.id == entity_id,
            AttributionMatrixSnapshotModel.tenant_id == tenant_id,
            AttributionMatrixSnapshotModel.clinic_id == clinic_id,
            AttributionMatrixSnapshotModel.deleted_at.is_(None),
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
    ) -> AttributionMatrixSnapshot | None:
        """Get most recent snapshot for given period — dual filter mandatory."""
        stmt = (
            select(AttributionMatrixSnapshotModel)
            .where(
                AttributionMatrixSnapshotModel.tenant_id == tenant_id,
                AttributionMatrixSnapshotModel.clinic_id == clinic_id,
                AttributionMatrixSnapshotModel.period_start == period_start,
                AttributionMatrixSnapshotModel.period_end == period_end,
                AttributionMatrixSnapshotModel.deleted_at.is_(None),
            )
            .order_by(AttributionMatrixSnapshotModel.computed_at.desc())
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
    ) -> list[AttributionMatrixSnapshot]:
        """List recent snapshots for tenant — dual filter mandatory."""
        stmt = (
            select(AttributionMatrixSnapshotModel)
            .where(
                AttributionMatrixSnapshotModel.tenant_id == tenant_id,
                AttributionMatrixSnapshotModel.clinic_id == clinic_id,
                AttributionMatrixSnapshotModel.deleted_at.is_(None),
            )
            .order_by(AttributionMatrixSnapshotModel.period_start.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def save(self, entity: AttributionMatrixSnapshot) -> AttributionMatrixSnapshot:
        """Persist an attribution snapshot (insert or update)."""
        model = _entity_to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()
        logger.info(
            "attribution_snapshot_saved",
            snapshot_id=str(entity.id),
            tenant_id=str(entity.tenant_id),
            period_start=str(entity.period_start),
            currency=entity.currency,
        )
        return _model_to_entity(merged)
