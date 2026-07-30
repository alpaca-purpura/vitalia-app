# cap: lisa.servicios
"""OfferEnginePort — bridge to the engine ``Offer`` aggregate (offer-studio).

D-1 sync/async seam: the engine ``OfferRepository`` (consumed via
``luana_core_platform.links.ports.offer.get_offer_repository``) is SYNC. The
brand offer repos are async. This port exposes an async-friendly surface and
its infrastructure impl bridges to the sync engine repo. ``TenantKnowledgeBuilder``
consumes the same sync repo (``get_all_by_tenant``) — the keystone surfacing
path must stay intact.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from luana_core_offer_studio.domain.enums import OfferStatus
from luana_core_offer_studio.domain.offer import Offer


class OfferEnginePort(ABC):
    """Create/read/update service offers in the engine offer-studio aggregate."""

    @abstractmethod
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
        """Create an engine Offer for a medical service. Returns the persisted Offer."""

    @abstractmethod
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
        """Patch the engine Offer mapped to a service. Returns the updated Offer."""

    @abstractmethod
    async def get(self, *, tenant_id: UUID, offer_id: UUID) -> Offer | None:
        """Fetch one engine Offer scoped to tenant. None if not found."""

    @abstractmethod
    async def list_service_offers(self, *, tenant_id: UUID) -> list[Offer]:
        """List active engine Offers for the tenant (keystone surfacing parity)."""
