# cap: lisa.servicios
"""KEYSTONE (AC-6 / AE-A1) — medical default factory produces a valid engine Offer.

RED-first (TDD): this test is written BEFORE the factory exists. It pins the
single highest-stakes mechanical contract (CONTEXT-BRIEF §14): the engine
``Offer`` aggregate has 13 required no-default fields; the medical factory must
fill all of them so that an ACTIVE service offer surfaces to Adrián via
``OfferRepository.get_all_by_tenant`` (status ∈ {active, draft}).

Pure-domain test (no DB): asserts the factory output is a well-formed engine
``Offer`` with archetype=SERVICIO, status=ACTIVE, and a non-empty pricing option.
"""

from __future__ import annotations

from uuid import uuid4

from luana_core_offer_studio.domain.enums import OfferArchetype, OfferStatus
from luana_core_offer_studio.domain.offer import Offer


def test_medical_factory_fills_all_required_engine_fields() -> None:
    from src.modules.vitalia.offer.application.services.medical_offer_factory import (
        build_medical_service_offer,
    )

    tenant_id = uuid4()
    offer = build_medical_service_offer(
        tenant_id=tenant_id,
        public_name="Diseño de sonrisa",
        price=1500.0,
        currency="PEN",
        status=OfferStatus.ACTIVE,
        canonical_ref="diseno_de_sonrisa",
    )

    assert isinstance(offer, Offer)
    assert offer.tenant_id == tenant_id
    assert offer.public_name == "Diseño de sonrisa"
    assert offer.archetype == OfferArchetype.SERVICIO
    assert offer.status == OfferStatus.ACTIVE
    # 13 required no-default fields all present + non-empty.
    assert offer.internal_sku
    assert offer.headline_promise
    assert offer.target_avatar_match  # non-empty list
    assert offer.primary_outcome
    assert offer.time_to_value
    assert offer.requires_application is False
    assert offer.min_financial_capacity is not None
    assert len(offer.pricing_options) == 1
    assert offer.pricing_options[0].total_amount == 1500.0
    assert offer.pricing_options[0].label
    assert offer.guarantee_type is not None
    assert offer.guarantee_terms is not None  # may be "" but field present
    assert offer.currency == "PEN"


def test_medical_factory_draft_status_for_create_on_choose() -> None:
    """RN-16 — create-on-choose makes a DRAFT (not phantom): status=DRAFT default."""
    from src.modules.vitalia.offer.application.services.medical_offer_factory import (
        build_medical_service_offer,
    )

    offer = build_medical_service_offer(
        tenant_id=uuid4(),
        public_name="Carillas de porcelana",
        price=0.0,
        currency=None,
        status=OfferStatus.DRAFT,
        canonical_ref=None,
    )
    assert offer.status == OfferStatus.DRAFT
    # Surfacing contract: build_identity keeps status ∈ {active, draft}.
    assert offer.status.value in ("active", "draft")


def test_medical_factory_pricing_zero_allowed() -> None:
    """RN-6/RN-11 — price >= 0 (a free consultation is valid)."""
    from src.modules.vitalia.offer.application.services.medical_offer_factory import (
        build_medical_service_offer,
    )

    offer = build_medical_service_offer(
        tenant_id=uuid4(),
        public_name="Consulta informativa gratuita",
        price=0.0,
        currency="PEN",
        status=OfferStatus.ACTIVE,
        canonical_ref=None,
    )
    assert offer.pricing_options[0].total_amount == 0.0
