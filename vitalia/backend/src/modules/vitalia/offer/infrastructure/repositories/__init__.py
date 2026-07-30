# cap: lisa.servicios
"""Offer infrastructure repositories (async, tenant-scoped, soft-delete)."""

from src.modules.vitalia.offer.infrastructure.repositories.case_repository import CaseRepository
from src.modules.vitalia.offer.infrastructure.repositories.offer_ext_repository import OfferServiceExtRepository
from src.modules.vitalia.offer.infrastructure.repositories.sales_brief_repository import SalesBriefRepository
from src.modules.vitalia.offer.infrastructure.repositories.specialist_link_repository import (
    ServiceSpecialistLinkRepository,
)
from src.modules.vitalia.offer.infrastructure.repositories.testimonial_repository import TestimonialRepository

__all__ = [
    "CaseRepository",
    "OfferServiceExtRepository",
    "SalesBriefRepository",
    "ServiceSpecialistLinkRepository",
    "TestimonialRepository",
]
