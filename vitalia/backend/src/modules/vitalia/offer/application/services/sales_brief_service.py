# cap: lisa.servicios
"""SalesBriefService — Adrián-facing sales material, CRUD + idempotent autosave (T-2 § 6).

Owns the brand-local SalesBrief (1:1 per offer, NOT PHI). The first ``save`` for
an offer creates the row; later saves patch the SAME row in place (idempotent
autosave — no duplicate rows, RN-16). Only known SalesBrief attributes are
applied; unknown keys are ignored.

D-2 write-through: the sales-brief fields (faq/objections/keywords/
contraindications/candidate_ideal/…) are vitalia-specific and have NO direct
engine ``Offer`` home today, so the write-through to the engine is a documented
no-op — this service stays the SSoT for the brief. Should an engine field
mapping appear (T-4), it plugs in here via an injected port without touching
callers.
"""

from __future__ import annotations

from typing import Any, Protocol
from uuid import UUID

import structlog

from src.modules.vitalia.offer.domain.sales_brief import SalesBrief
from src.modules.vitalia.offer.infrastructure.serializers import faq_from_list, objections_from_list

logger = structlog.get_logger()

# Attributes a caller may set through ``save`` (the brief's editable surface).
_EDITABLE = (
    "candidate_ideal",
    "contraindications",
    "qualification_questions",
    "escalation_conditions",
    "requires_evaluation",
    "emotional_benefits",
    "pain_of_not_treating",
    "differentiators",
    "promos",
    "faq",
    "objections",
    "keywords",
    "problems_solved",
    "language_to_avoid",
)


class _BriefRepo(Protocol):
    async def get_by_offer(self, offer_id: UUID, *, tenant_id: UUID) -> SalesBrief | None: ...
    async def create(self, brief: SalesBrief) -> SalesBrief: ...
    async def update(self, brief: SalesBrief) -> SalesBrief: ...


class SalesBriefService:
    """CRUD + idempotent autosave for the sales brief (1:1 per offer)."""

    def __init__(self, *, brief_repo: _BriefRepo) -> None:
        self._repo = brief_repo

    async def get(self, *, tenant_id: UUID, offer_id: UUID) -> SalesBrief | None:
        return await self._repo.get_by_offer(offer_id, tenant_id=tenant_id)

    async def save(self, *, tenant_id: UUID, offer_id: UUID, fields: dict[str, Any]) -> SalesBrief:
        """Create on first save, patch the same row afterwards (idempotent)."""
        current = await self._repo.get_by_offer(offer_id, tenant_id=tenant_id)
        if current is None:
            brief = SalesBrief(tenant_id=tenant_id, offer_id=offer_id)
            _apply(brief, fields)
            saved = await self._repo.create(brief)
        else:
            _apply(current, fields)
            saved = await self._repo.update(current)
        # D-2 write-through: no engine Offer field maps to brief content today (no-op).
        logger.debug("sales_brief_saved", tenant_id=str(tenant_id), offer_id=str(offer_id))
        return saved


def _apply(brief: SalesBrief, fields: dict[str, Any]) -> None:
    for key, value in fields.items():
        if key not in _EDITABLE:
            continue
        if key == "faq":
            value = faq_from_list(value)
        elif key == "objections":
            value = objections_from_list(value)
        setattr(brief, key, value)
