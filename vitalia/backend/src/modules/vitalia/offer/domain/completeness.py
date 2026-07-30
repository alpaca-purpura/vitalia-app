# cap: lisa.servicios
# voseo-allowed: "vos" matched by hook is the value-objects module name (domain.vos), not voseo
"""Service completeness scoring (AC-19 · pure · mutation-critical).

compute_completeness counts how many of the 26 MVP must-have fields are populated.
It is PURELY INFORMATIONAL: it NEVER blocks is_active (a fully-empty service can be
active — RN-10 / AC-19). A field counts as filled when non-None and, for strings,
non-whitespace. Lists count as filled when non-empty.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.modules.vitalia.offer.domain.offer_ext import OfferExt
from src.modules.vitalia.offer.domain.sales_brief import SalesBrief
from src.modules.vitalia.offer.domain.vos import ThreeChargePricing

# The 26 MVP must-have fields, in display order. Keys are stable identifiers used
# by the FE completeness checklist. (offer_ext: 18 · pricing: 1 · sales_brief: 7)
_EXT_FIELDS: tuple[str, ...] = (
    "description_long",
    "includes",
    "excludes",
    "warranty",
    "procedure_steps",
    "anesthesia_pain",
    "prep",
    "aftercare",
    "downtime",
    "expected_result",
    "result_timing",
    "result_lifespan",
    "realistic_expectations",
    "risks",
    "red_flags",
    "initial_appt_type",
    "initial_appt_duration_minutes",
    "category",
)
_PRICING_FIELDS: tuple[str, ...] = ("price",)
_BRIEF_FIELDS: tuple[str, ...] = (
    "candidate_ideal",
    "contraindications",
    "qualification_questions",
    "emotional_benefits",
    "differentiators",
    "problems_solved",
    "keywords",
)

MUST_HAVE_TOTAL = len(_EXT_FIELDS) + len(_PRICING_FIELDS) + len(_BRIEF_FIELDS)  # == 26


@dataclass(frozen=True)
class CompletenessResult:
    """Outcome of completeness scoring — informational only."""

    filled: int
    total: int
    missing: list[str]


def _is_filled(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def compute_completeness(
    offer_ext: OfferExt,
    sales_brief: SalesBrief,
    pricing: ThreeChargePricing,
) -> CompletenessResult:
    """Score the 26 must-have fields. Never blocks activation."""
    missing: list[str] = []
    filled = 0

    for key in _EXT_FIELDS:
        if _is_filled(getattr(offer_ext, key, None)):
            filled += 1
        else:
            missing.append(key)

    for key in _PRICING_FIELDS:
        if _is_filled(getattr(pricing, key, None)):
            filled += 1
        else:
            missing.append(key)

    for key in _BRIEF_FIELDS:
        if _is_filled(getattr(sales_brief, key, None)):
            filled += 1
        else:
            missing.append(key)

    return CompletenessResult(filled=filled, total=MUST_HAVE_TOTAL, missing=missing)
