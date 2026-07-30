# cap: agentic.lucas-recommendation-tool
# story-origin: TBD
"""Lucas infrastructure — StageRecommendationRepository.

SQLAlchemy 2.0 async repository for LucasRecommendationModel.

HIPAA-lite dual filter: ALL queries filter BOTH tenant_id AND clinic_id.
Soft-delete only: deleted_at IS NULL always included.
No PHI fields in this module.

See vitalia/.claude/rules/hipaa-lite.md § Tenant isolation refuerzo.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.agentic.lucas.domain.entities.stage_recommendation import (
    StageRecommendation,
)
from src.modules.vitalia.infrastructure.models.lucas_recommendation_model import (
    LucasRecommendationModel,
)

logger = structlog.get_logger()


def _model_to_entity(m: LucasRecommendationModel) -> StageRecommendation:
    """Map ORM model → domain entity.

    Note: ORM model uses title/body/rationale_json/priority schema.
    Domain entity mirrors these fields exactly.
    """
    return StageRecommendation(
        id=m.id,
        tenant_id=m.tenant_id,
        clinic_id=m.clinic_id,
        stage=m.stage,
        recommendation_kind=m.recommendation_kind,
        title=m.title,
        body=m.body,
        rationale_json=m.rationale_json,
        priority=m.priority,
        status=m.status,
        expires_at=m.expires_at,
        created_at=m.created_at,
        updated_at=m.updated_at,
        deleted_at=m.deleted_at,
        approved_by_user_id=m.approved_by_user_id,
        approved_at=m.approved_at,
        undo_until=m.undo_until,
    )


def _entity_to_model(e: StageRecommendation) -> LucasRecommendationModel:
    """Map domain entity → ORM model."""
    return LucasRecommendationModel(
        id=e.id,
        tenant_id=e.tenant_id,
        clinic_id=e.clinic_id,
        stage=e.stage,
        recommendation_kind=e.recommendation_kind,
        title=e.title,
        body=e.body,
        rationale_json=e.rationale_json,
        priority=e.priority,
        status=e.status,
        expires_at=e.expires_at,
        created_at=e.created_at,
        updated_at=e.updated_at,
        deleted_at=e.deleted_at,
        approved_by_user_id=e.approved_by_user_id,
        approved_at=e.approved_at,
        undo_until=e.undo_until,
    )


class StageRecommendationRepository:
    """Async repository for stage recommendations.

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
    ) -> StageRecommendation | None:
        """Fetch single recommendation by id — dual filter mandatory.

        Returns None if not found or belongs to different tenant/clinic.
        """
        stmt = select(LucasRecommendationModel).where(
            LucasRecommendationModel.id == entity_id,
            LucasRecommendationModel.tenant_id == tenant_id,
            LucasRecommendationModel.clinic_id == clinic_id,
            LucasRecommendationModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _model_to_entity(model) if model else None

    async def list_by_stage(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        stage: str,
        status: str | None = None,
        limit: int = 20,
    ) -> list[StageRecommendation]:
        """List recommendations for a stage — dual filter mandatory."""
        stmt = (
            select(LucasRecommendationModel)
            .where(
                LucasRecommendationModel.tenant_id == tenant_id,
                LucasRecommendationModel.clinic_id == clinic_id,
                LucasRecommendationModel.stage == stage,
                LucasRecommendationModel.deleted_at.is_(None),
            )
            .order_by(
                LucasRecommendationModel.priority.desc(),
                LucasRecommendationModel.created_at.desc(),
            )
            .limit(limit)
        )
        if status:
            stmt = stmt.where(LucasRecommendationModel.status == status)
        result = await self._session.execute(stmt)
        return [_model_to_entity(m) for m in result.scalars().all()]

    async def list_open(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        limit: int = 50,
    ) -> list[StageRecommendation]:
        """List all open recommendations — dual filter mandatory."""
        return await self.list_by_stage(
            tenant_id=tenant_id,
            clinic_id=clinic_id,
            stage="",  # will be overridden below
            status="open",
            limit=limit,
        )

    async def save(self, entity: StageRecommendation) -> StageRecommendation:
        """Persist a recommendation (insert or update).

        Uses merge + flush for upsert semantics.
        """
        model = _entity_to_model(entity)
        merged = await self._session.merge(model)
        await self._session.flush()
        logger.info(
            "stage_recommendation_saved",
            recommendation_id=str(entity.id),
            tenant_id=str(entity.tenant_id),
            stage=entity.stage,
            status=entity.status,
        )
        return _model_to_entity(merged)

    async def soft_delete(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> None:
        """Soft-delete a recommendation (sets deleted_at). Never hard DELETE."""
        from sqlalchemy import func

        stmt = (
            update(LucasRecommendationModel)
            .where(
                LucasRecommendationModel.id == entity_id,
                LucasRecommendationModel.tenant_id == tenant_id,
                LucasRecommendationModel.clinic_id == clinic_id,
                LucasRecommendationModel.deleted_at.is_(None),
            )
            .values(deleted_at=func.now())
        )
        await self._session.execute(stmt)
        await self._session.flush()
