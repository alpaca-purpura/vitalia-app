# cap: lisa.servicios
"""ServiceSpecialistLinkRepository — async, tenant-scoped, soft-delete.

Link/unlink offer↔doctor. Unique (offer_id, doctor_id) WHERE deleted_at IS NULL
enforced at DB (migration 045). NOT PHI → plain AsyncSession.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.offer.domain.specialist_link import ServiceSpecialistLink
from src.modules.vitalia.offer.infrastructure.models.offer_service_specialist_link_model import (
    OfferServiceSpecialistLinkModel,
)


def _to_domain(model: OfferServiceSpecialistLinkModel) -> ServiceSpecialistLink:
    return ServiceSpecialistLink(
        tenant_id=model.tenant_id,
        offer_id=model.offer_id,
        doctor_id=model.doctor_id,
        id=model.id,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )


class ServiceSpecialistLinkRepository:
    """Persistence for offer↔doctor links."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def link(self, link: ServiceSpecialistLink) -> ServiceSpecialistLink:
        model = OfferServiceSpecialistLinkModel(
            id=link.id,
            tenant_id=link.tenant_id,
            offer_id=link.offer_id,
            doctor_id=link.doctor_id,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

    async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID) -> ServiceSpecialistLink | None:
        stmt = select(OfferServiceSpecialistLinkModel).where(
            OfferServiceSpecialistLinkModel.id == entity_id,
            OfferServiceSpecialistLinkModel.tenant_id == tenant_id,
            OfferServiceSpecialistLinkModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(model) if model is not None else None

    async def list_by_offer(self, offer_id: UUID, *, tenant_id: UUID) -> list[ServiceSpecialistLink]:
        stmt = select(OfferServiceSpecialistLinkModel).where(
            OfferServiceSpecialistLinkModel.offer_id == offer_id,
            OfferServiceSpecialistLinkModel.tenant_id == tenant_id,
            OfferServiceSpecialistLinkModel.deleted_at.is_(None),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(m) for m in rows]

    async def unlink(self, offer_id: UUID, doctor_id: UUID, *, tenant_id: UUID) -> None:
        stmt = (
            update(OfferServiceSpecialistLinkModel)
            .where(
                OfferServiceSpecialistLinkModel.offer_id == offer_id,
                OfferServiceSpecialistLinkModel.doctor_id == doctor_id,
                OfferServiceSpecialistLinkModel.tenant_id == tenant_id,
                OfferServiceSpecialistLinkModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
