# cap: lisa.servicios
"""Offer SQLAlchemy 2.0 models (maps to migration 045_vitalia_offer_service_tables)."""

from src.modules.vitalia.offer.infrastructure.models.offer_service_case_model import OfferServiceCaseModel
from src.modules.vitalia.offer.infrastructure.models.offer_service_ext_model import OfferServiceExtModel
from src.modules.vitalia.offer.infrastructure.models.offer_service_sales_brief_model import (
    OfferServiceSalesBriefModel,
)
from src.modules.vitalia.offer.infrastructure.models.offer_service_specialist_link_model import (
    OfferServiceSpecialistLinkModel,
)
from src.modules.vitalia.offer.infrastructure.models.offer_service_testimonial_model import (
    OfferServiceTestimonialModel,
)

__all__ = [
    "OfferServiceCaseModel",
    "OfferServiceExtModel",
    "OfferServiceSalesBriefModel",
    "OfferServiceSpecialistLinkModel",
    "OfferServiceTestimonialModel",
]
