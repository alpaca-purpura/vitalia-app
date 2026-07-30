# cap: lisa.servicios
# voseo-allowed: "vos" matched by hook is the value-objects module name (domain.vos), not voseo
"""SalesBrief aggregate — Adrián-facing sales material for an offer.

Pure domain. 1:1 with an offer. Service-layer write-through to the engine Offer
happens at the application layer (T-2/T-4), not here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from src.modules.vitalia.offer.domain.vos import FaqPair, ObjectionPair


@dataclass
class SalesBrief:
    """Sales brief projection (1:1 per offer)."""

    tenant_id: UUID
    offer_id: UUID
    candidate_ideal: str | None = None
    contraindications: str | None = None  # safety RN-22
    qualification_questions: str | None = None
    escalation_conditions: str | None = None  # safety RN-22
    requires_evaluation: bool = False
    emotional_benefits: str | None = None
    pain_of_not_treating: str | None = None
    differentiators: str | None = None
    promos: str | None = None
    faq: list[FaqPair] = field(default_factory=list)
    objections: list[ObjectionPair] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)  # RN-16 inbound channel match
    problems_solved: str | None = None
    language_to_avoid: str | None = None
    id: UUID = field(default_factory=uuid4)
    created_at: datetime | None = None
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
