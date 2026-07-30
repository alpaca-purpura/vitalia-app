"""Shared test helpers for luana-core-offer-studio tests.

Provides create_product_model, TENANT_A, TENANT_B constants reused
across multiple test modules. Extracted from conftest.py to allow
direct import (pytest conftest.py is not importable by module path
in luana-platform).
"""

from __future__ import annotations

import uuid

from luana_core_offer_studio.domain.enums import OfferArchetype, OfferStatus, OfferValueLevel
from luana_core_offer_studio.infrastructure.models.product_model import ProductModel

TENANT_A = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TENANT_B = uuid.UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


def create_product_model(
    tenant_id: uuid.UUID,
    *,
    archetype: str = OfferArchetype.PRODUCTO.value,
    status: str = OfferStatus.ACTIVE.value,
    name: str = "Test Offer",
    value_level: str | None = OfferValueLevel.ACTIVACION.value,
    **overrides,
) -> ProductModel:
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "name": name,
        "archetype": archetype,
        "status": status,
        "value_level": value_level,
        "format_hint": None,
        "is_lead_magnet": False,
        "has_editions": True,
        "pricing": [],
        "currency": "USD",
        "specific_details": {},
        "deliverables": [],
        "headline_promise": "Headline",
        "primary_outcome": "Outcome",
        "time_to_value": "1 week",
        "marketing_pain_points": [],
        "marketing_desires": [],
        "objections": [],
        "target_avatar_match": [],
        "access_duration": None,
        "access_duration_text": None,
        "support_duration_days": None,
        "delivery_model": "diy",
        "requires_application": False,
        "min_financial_capacity": "LOW_INCOME",
        "prerequisites": [],
        "anti_avatar_keywords": [],
        "guarantee_type": "none",
        "guarantee_terms": "",
        "downsell_product_id": None,
        "upsell_product_id": None,
        "includes_offers": [],
        "onboarding_action": None,
        "onboarding_url": None,
        "calendar_type_id": None,
        "checkout_page_url": None,
        "vsl_link": None,
        "landing_page_config": {},
        "metadata_info": {},
        "archived_at": None,
        "deleted_at": None,
    }
    defaults.update(overrides)
    return ProductModel(**defaults)
