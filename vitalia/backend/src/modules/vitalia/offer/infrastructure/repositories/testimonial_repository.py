# cap: lisa.servicios
"""TestimonialRepository — async, tenant-scoped, soft-delete. NOT PHI."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.offer.domain.proof import Testimonial
from src.modules.vitalia.offer.infrastructure.models.offer_service_testimonial_model import (
    OfferServiceTestimonialModel,
)


def _to_domain(model: OfferServiceTestimonialModel) -> Testimonial:
    return Testimonial(
        tenant_id=model.tenant_id,
        offer_id=model.offer_id,
        rating=model.rating,
        text=model.text,
        author=model.author,
        source=model.source,
        id=model.id,
        created_at=model.created_at,
        deleted_at=model.deleted_at,
    )


class TestimonialRepository:
    """Persistence for offer testimonials."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, testimonial: Testimonial) -> Testimonial:
        model = OfferServiceTestimonialModel(
            id=testimonial.id,
            tenant_id=testimonial.tenant_id,
            offer_id=testimonial.offer_id,
            rating=testimonial.rating,
            text=testimonial.text,
            author=testimonial.author,
            source=testimonial.source,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

    async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID) -> Testimonial | None:
        stmt = select(OfferServiceTestimonialModel).where(
            OfferServiceTestimonialModel.id == entity_id,
            OfferServiceTestimonialModel.tenant_id == tenant_id,
            OfferServiceTestimonialModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(model) if model is not None else None

    async def list_by_offer(self, offer_id: UUID, *, tenant_id: UUID) -> list[Testimonial]:
        stmt = select(OfferServiceTestimonialModel).where(
            OfferServiceTestimonialModel.offer_id == offer_id,
            OfferServiceTestimonialModel.tenant_id == tenant_id,
            OfferServiceTestimonialModel.deleted_at.is_(None),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_to_domain(m) for m in rows]

    async def soft_delete(self, entity_id: UUID, *, tenant_id: UUID) -> None:
        stmt = (
            update(OfferServiceTestimonialModel)
            .where(
                OfferServiceTestimonialModel.id == entity_id,
                OfferServiceTestimonialModel.tenant_id == tenant_id,
                OfferServiceTestimonialModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
