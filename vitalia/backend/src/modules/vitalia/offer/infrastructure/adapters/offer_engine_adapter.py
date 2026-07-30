# cap: lisa.servicios
"""OfferEngineAdapter — async→sync bridge to the engine ``OfferRepository``.

D-1 seam. The engine offer-studio repo is SYNC (``Session``); the brand offer
module runs on ``AsyncSession``. ``AsyncSession.run_sync`` hands a sync ``Session``
to a callback executed in the greenlet, so we can call the engine repo there.
The medical defaults live in ``medical_offer_factory`` (the single brand→engine
mapping). Keystone parity: ``list_service_offers`` mirrors the sync
``get_all_by_tenant`` that ``TenantKnowledgeBuilder`` consumes.
"""

from __future__ import annotations

from uuid import UUID

from luana_core_offer_studio.domain.enums import OfferStatus
from luana_core_offer_studio.domain.offer import Offer
from luana_core_platform.links.ports.offer import get_offer_repository
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from src.modules.vitalia.offer.application.ports.offer_engine_port import OfferEnginePort
from src.modules.vitalia.offer.application.services.medical_offer_factory import (
    build_medical_service_offer,
)


class OfferEngineAdapter(OfferEnginePort):
    """Bridge the async brand session to the sync engine offer repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_service_offer(
        self,
        *,
        tenant_id: UUID,
        public_name: str,
        price: float,
        currency: str | None,
        status: OfferStatus,
        canonical_ref: str | None,
    ) -> Offer:
        offer = build_medical_service_offer(
            tenant_id=tenant_id,
            public_name=public_name,
            price=price,
            currency=currency,
            status=status,
            canonical_ref=canonical_ref,
        )

        def _create(sync_session: Session) -> Offer:
            repo = get_offer_repository(sync_session)
            return repo.create(offer)  # type: ignore[attr-defined,no-any-return]

        return await self._session.run_sync(_create)

    async def update_service_offer(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        public_name: str | None = None,
        price: float | None = None,
        currency: str | None = None,
        status: OfferStatus | None = None,
    ) -> Offer:
        def _update(sync_session: Session) -> Offer:
            repo = get_offer_repository(sync_session)
            current: Offer | None = repo.get_by_id(offer_id, tenant_id)  # type: ignore[attr-defined]
            if current is None:
                raise OfferEngineNotFoundError(offer_id)
            rebuilt = build_medical_service_offer(
                tenant_id=tenant_id,
                public_name=public_name if public_name is not None else current.public_name,
                price=(price if price is not None else _headline_price(current)),
                currency=currency if currency is not None else current.currency,
                status=status if status is not None else current.status,
                canonical_ref=current.preset_id,
                offer_id=offer_id,
            )
            # Keep the engine-generated SKU stable across updates.
            rebuilt.internal_sku = current.internal_sku
            return repo.update(rebuilt, tenant_id)  # type: ignore[attr-defined,no-any-return]

        return await self._session.run_sync(_update)

    async def get(self, *, tenant_id: UUID, offer_id: UUID) -> Offer | None:
        def _get(sync_session: Session) -> Offer | None:
            repo = get_offer_repository(sync_session)
            return repo.get_by_id(offer_id, tenant_id)  # type: ignore[attr-defined,no-any-return]

        return await self._session.run_sync(_get)

    async def list_service_offers(self, *, tenant_id: UUID) -> list[Offer]:
        def _list(sync_session: Session) -> list[Offer]:
            repo = get_offer_repository(sync_session)
            return repo.get_all_by_tenant(tenant_id)  # type: ignore[attr-defined,no-any-return]

        return await self._session.run_sync(_list)


class OfferEngineNotFoundError(Exception):
    """Raised when updating an engine Offer that does not exist in the tenant scope."""

    def __init__(self, offer_id: UUID) -> None:
        super().__init__(f"Engine Offer {offer_id} not found in tenant scope.")


def _headline_price(offer: Offer) -> float:
    """Read the headline price back from the engine Offer's first pricing option."""
    if offer.pricing_options:
        return float(offer.pricing_options[0].total_amount)
    return 0.0
