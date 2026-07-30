# cap: lisa.servicios
"""SalesBriefRepository — async, tenant-scoped, soft-delete. NOT PHI.

1:1 per offer. faq/objections/keywords round-trip via serializers (JSONB).
Write-through to the engine Offer is an application-layer concern (T-2/T-4).
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.vitalia.offer.domain.sales_brief import SalesBrief
from src.modules.vitalia.offer.infrastructure.models.offer_service_sales_brief_model import (
    OfferServiceSalesBriefModel,
)
from src.modules.vitalia.offer.infrastructure.serializers import (
    faq_from_list,
    faq_to_list,
    objections_from_list,
    objections_to_list,
)


class SalesBriefNotFoundError(Exception):
    """Raised when updating a SalesBrief that does not exist in the tenant scope."""

    def __init__(self, brief_id: UUID) -> None:
        super().__init__(f"SalesBrief {brief_id} not found (or soft-deleted) in tenant scope.")


_SCALAR_TEXT = (
    "candidate_ideal",
    "contraindications",
    "qualification_questions",
    "escalation_conditions",
    "emotional_benefits",
    "pain_of_not_treating",
    "differentiators",
    "promos",
    "problems_solved",
    "language_to_avoid",
)


def _to_model(brief: SalesBrief) -> OfferServiceSalesBriefModel:
    model = OfferServiceSalesBriefModel(
        id=brief.id,
        tenant_id=brief.tenant_id,
        offer_id=brief.offer_id,
        requires_evaluation=brief.requires_evaluation,
        faq=faq_to_list(brief.faq),
        objections=objections_to_list(brief.objections),
        keywords=list(brief.keywords),
    )
    for attr in _SCALAR_TEXT:
        setattr(model, attr, getattr(brief, attr))
    return model


def _to_domain(model: OfferServiceSalesBriefModel) -> SalesBrief:
    brief = SalesBrief(
        tenant_id=model.tenant_id,
        offer_id=model.offer_id,
        requires_evaluation=model.requires_evaluation,
        faq=faq_from_list(model.faq),
        objections=objections_from_list(model.objections),
        keywords=list(model.keywords or []),
        id=model.id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        deleted_at=model.deleted_at,
    )
    for attr in _SCALAR_TEXT:
        setattr(brief, attr, getattr(model, attr))
    return brief


class SalesBriefRepository:
    """Persistence for the Adrián-facing sales brief (1:1 per offer)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, brief: SalesBrief) -> SalesBrief:
        model = _to_model(brief)
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model)
        return _to_domain(model)

    async def get_by_id(self, entity_id: UUID, *, tenant_id: UUID) -> SalesBrief | None:
        stmt = select(OfferServiceSalesBriefModel).where(
            OfferServiceSalesBriefModel.id == entity_id,
            OfferServiceSalesBriefModel.tenant_id == tenant_id,
            OfferServiceSalesBriefModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(model) if model is not None else None

    async def get_by_offer(self, offer_id: UUID, *, tenant_id: UUID) -> SalesBrief | None:
        stmt = select(OfferServiceSalesBriefModel).where(
            OfferServiceSalesBriefModel.offer_id == offer_id,
            OfferServiceSalesBriefModel.tenant_id == tenant_id,
            OfferServiceSalesBriefModel.deleted_at.is_(None),
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        return _to_domain(model) if model is not None else None

    async def update(self, brief: SalesBrief) -> SalesBrief:
        """Patch an existing SalesBrief by (id, tenant_id). Touches updated_at."""
        values: dict[str, object] = {
            "requires_evaluation": brief.requires_evaluation,
            "faq": faq_to_list(brief.faq),
            "objections": objections_to_list(brief.objections),
            "keywords": list(brief.keywords),
            "updated_at": datetime.now(UTC),
        }
        for attr in _SCALAR_TEXT:
            values[attr] = getattr(brief, attr)
        stmt = (
            update(OfferServiceSalesBriefModel)
            .where(
                OfferServiceSalesBriefModel.id == brief.id,
                OfferServiceSalesBriefModel.tenant_id == brief.tenant_id,
                OfferServiceSalesBriefModel.deleted_at.is_(None),
            )
            .values(**values)
            .returning(OfferServiceSalesBriefModel)
        )
        model = (await self._session.execute(stmt)).scalar_one_or_none()
        if model is None:
            raise SalesBriefNotFoundError(brief.id)
        await self._session.refresh(model)
        return _to_domain(model)

    async def soft_delete(self, entity_id: UUID, *, tenant_id: UUID) -> None:
        stmt = (
            update(OfferServiceSalesBriefModel)
            .where(
                OfferServiceSalesBriefModel.id == entity_id,
                OfferServiceSalesBriefModel.tenant_id == tenant_id,
                OfferServiceSalesBriefModel.deleted_at.is_(None),
            )
            .values(deleted_at=datetime.now(UTC))
        )
        await self._session.execute(stmt)
