# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""LeadScreeningEventRepository — SQLAlchemy 2.0 async implementation.

PHI repository — inherits PhiRepositoryBase for dual-filter enforcement.
Every query MUST filter BOTH tenant_id AND clinic_id (HIPAA-lite cardinal).

Per vitalia/.claude/rules/hipaa-lite.md:
  "Además de tenant_id (raíz rule), vitalia agrega clinic_id como segundo
   filter obligatorio en queries PHI."

Architecture gate: vitalia/backend/tests/architecture/test_phi_dual_filter.py

downstream-regression-na: brand-local PHI repo for vitalia sales_agent
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from sqlalchemy import select

from src.modules.vitalia._shared.repositories.phi_repository import (
    PhiRepositoryBase,
)
from src.modules.vitalia.sales_agent.domain.entities.lead_screening_event import (
    LeadScreeningEvent,
)
from src.modules.vitalia.sales_agent.persistence.models.lead_screening_event import (
    LeadScreeningEventModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


def _utc_now() -> datetime:
    return datetime.now(tz=timezone.utc)


def _to_domain(model: LeadScreeningEventModel) -> LeadScreeningEvent:
    """Map ORM model to domain entity."""
    return LeadScreeningEvent(
        id=model.id,
        tenant_id=model.tenant_id,
        clinic_id=model.clinic_id,
        lead_id=model.lead_id,
        vertical=model.vertical,
        questions_asked=model.questions_asked or [],
        response_text=model.response_text,
        outcome=model.outcome,
        reasoning=model.reasoning,
        evaluated_at=model.evaluated_at,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )


class LeadScreeningEventRepository(PhiRepositoryBase):
    """Repository for lead_screening_events table.

    All operations enforce the HIPAA-lite dual filter:
      WHERE tenant_id = :tenant_id AND clinic_id = :clinic_id

    Soft-delete only: never issues DELETE statements.
    """

    def __init__(self, session: "AsyncSession") -> None:
        """Initialize with an active async DB session.

        Args:
            session: SQLAlchemy async session shared with the UoW transaction.
        """
        self._session = session

    async def get_by_id(
        self,
        entity_id: UUID,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> LeadScreeningEvent | None:
        """Retrieve a LeadScreeningEvent by PK with dual filter.

        Args:
            entity_id: UUID primary key of the screening event.
            tenant_id: Tenant UUID (root isolation — mandatory).
            clinic_id: Clinic UUID (HIPAA-lite second filter — mandatory).

        Returns:
            Domain entity or None if not found / soft-deleted.

        Raises:
            MissingClinicFilterError: If clinic_id is None.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = select(LeadScreeningEventModel).where(
            LeadScreeningEventModel.tenant_id == tenant_id,
            LeadScreeningEventModel.clinic_id == clinic_id,
            LeadScreeningEventModel.id == entity_id,
            LeadScreeningEventModel.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return _to_domain(model)

    async def list_by_filter(
        self,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
        lead_id: UUID | None = None,
        vertical: str | None = None,
        outcome: str | None = None,
        **_filters: object,
    ) -> list[LeadScreeningEvent]:
        """List screening events with dual filter + optional extra filters.

        Args:
            tenant_id: Tenant UUID (root isolation — mandatory).
            clinic_id: Clinic UUID (HIPAA-lite second filter — mandatory).
            lead_id: Optional filter by lead UUID.
            vertical: Optional filter by clinical vertical.
            outcome: Optional filter by screening outcome.

        Returns:
            List of matching domain entities (empty list if none found).

        Raises:
            MissingClinicFilterError: If clinic_id is None.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        stmt = select(LeadScreeningEventModel).where(
            LeadScreeningEventModel.tenant_id == tenant_id,
            LeadScreeningEventModel.clinic_id == clinic_id,
            LeadScreeningEventModel.deleted_at.is_(None),
        )
        if lead_id is not None:
            stmt = stmt.where(LeadScreeningEventModel.lead_id == lead_id)
        if vertical is not None:
            stmt = stmt.where(LeadScreeningEventModel.vertical == vertical)
        if outcome is not None:
            stmt = stmt.where(LeadScreeningEventModel.outcome == outcome)

        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [_to_domain(m) for m in models]

    async def create(
        self,
        entity: LeadScreeningEvent,
        *,
        tenant_id: UUID,
        clinic_id: UUID,
    ) -> LeadScreeningEvent:
        """Persist a new LeadScreeningEvent.

        Args:
            entity: Domain entity to persist (id must already be set).
            tenant_id: Tenant UUID (validated against entity.tenant_id).
            clinic_id: Clinic UUID (validated against entity.clinic_id).

        Returns:
            The persisted domain entity (same as input after flush).

        Raises:
            MissingClinicFilterError: If clinic_id is None.
            ValueError: If tenant_id mismatch between param and entity.
        """
        self.validate_dual_filter(tenant_id=tenant_id, clinic_id=clinic_id)

        if entity.tenant_id != tenant_id:
            raise ValueError(f"tenant_id mismatch: entity.tenant_id={entity.tenant_id}, param={tenant_id}")
        if entity.clinic_id != clinic_id:
            raise ValueError(f"clinic_id mismatch: entity.clinic_id={entity.clinic_id}, param={clinic_id}")

        model = LeadScreeningEventModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            clinic_id=entity.clinic_id,
            lead_id=entity.lead_id,
            vertical=entity.vertical,
            questions_asked=entity.questions_asked,
            response_text=entity.response_text,
            outcome=entity.outcome,
            reasoning=entity.reasoning,
            evaluated_at=entity.evaluated_at,
            created_at=entity.created_at,
            deleted_at=None,
        )
        self._session.add(model)
        await self._session.flush()

        logger.info(
            "lead_screening_event_created",
            event_id=str(entity.id),
            tenant_id=str(tenant_id),
            clinic_id=str(clinic_id),
            lead_id=str(entity.lead_id),
            outcome=entity.outcome,
        )
        return entity
