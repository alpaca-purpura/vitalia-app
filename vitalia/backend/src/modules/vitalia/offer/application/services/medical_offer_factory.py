# cap: lisa.servicios
"""Medical-service default factory for the engine ``Offer`` aggregate.

KEYSTONE (AC-6 / AE-A1 · CONTEXT-BRIEF §14). The engine ``Offer`` aggregate
has 13 required no-default fields. A Vitalia medical service is a thin concept
(name + price + clinic content), so this factory supplies sane medical-neutral
defaults for every engine field the brand does not model, producing a valid
``Offer`` row whose ACTIVE status surfaces to Adrián via
``OfferRepository.get_all_by_tenant`` (build_identity keeps status ∈ {active, draft}).

This is the ONLY place that maps a brand service to the engine aggregate — keep
the engine consume read-only (no edit to ``core/luana-core-offer-studio``).
"""

from __future__ import annotations

import re
from uuid import UUID, uuid4

from luana_core_offer_studio.domain.enums import (
    GuaranteeType,
    OfferArchetype,
    OfferStatus,
)
from luana_core_offer_studio.domain.offer import Offer, PricingStructure
from luana_core_platform.domain.enums import AvatarPersona, FinancialCapacity

_SKU_PREFIX = "VIT-SVC"


def _slugify_sku(public_name: str) -> str:
    """Derive a stable, readable internal SKU fragment from the service name."""
    slug = re.sub(r"[^a-z0-9]+", "-", public_name.lower()).strip("-")[:24]
    return f"{_SKU_PREFIX}-{slug or 'servicio'}-{uuid4().hex[:6]}"


def build_medical_service_offer(
    *,
    tenant_id: UUID,
    public_name: str,
    price: float,
    currency: str | None,
    status: OfferStatus,
    canonical_ref: str | None,
    offer_id: UUID | None = None,
) -> Offer:
    """Build an engine ``Offer`` for a Vitalia medical service.

    Fills all 13 required no-default engine fields with medical-neutral values.
    ``validate_consistency`` auto-derives ``delivery_model`` + ``has_editions``
    from the archetype capabilities.

    Args:
        tenant_id: Owning tenant.
        public_name: Patient-facing service name (e.g. "Diseño de sonrisa").
        price: Headline price (>= 0; 0 = free consultation).
        currency: ISO currency from the tenant locale (never hardcoded).
        status: ``OfferStatus.DRAFT`` on create-on-choose, ``ACTIVE`` on activate.
        canonical_ref: Library template ref (None = personalizado).
        offer_id: Existing engine offer id when re-building for update.

    Returns:
        A validated engine ``Offer`` aggregate.
    """
    pricing = PricingStructure(
        label="Precio del servicio",
        total_amount=max(float(price), 0.0),
    )
    return Offer(
        id=offer_id,
        tenant_id=tenant_id,
        preset_id=canonical_ref,
        currency=currency,
        internal_sku=_slugify_sku(public_name),
        public_name=public_name,
        archetype=OfferArchetype.SERVICIO,
        headline_promise=public_name,
        target_avatar_match=[AvatarPersona.RESEARCHER],
        primary_outcome=public_name,
        time_to_value="Según evaluación del especialista",
        requires_application=False,
        min_financial_capacity=FinancialCapacity.MIDDLE_CLASS,
        pricing_options=[pricing],
        guarantee_type=GuaranteeType.NONE,
        guarantee_terms="",
        status=status,
    )
