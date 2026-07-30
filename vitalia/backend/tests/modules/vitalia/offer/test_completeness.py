# cap: lisa.servicios
"""RED-first · completeness 26 must-have (AC-19 · mutation-critical).

compute_completeness(offer_ext, sales_brief, pricing) -> CompletenessResult:
  - total == 26 (the MVP must-have field count)
  - filled == count of must-have fields populated (non-None / non-empty)
  - missing == ordered list of unfilled must-have field keys
  - is_active is NEVER part of completeness (AC-19: completeness never blocks activation)
"""

from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from src.modules.vitalia.offer.domain.completeness import compute_completeness
from src.modules.vitalia.offer.domain.enums import (
    InitialApptType,
    PriceMode,
    ServiceModality,
)
from src.modules.vitalia.offer.domain.offer_ext import OfferExt
from src.modules.vitalia.offer.domain.sales_brief import SalesBrief
from src.modules.vitalia.offer.domain.vos import ThreeChargePricing


def _empty_ext() -> OfferExt:
    return OfferExt(tenant_id=uuid4(), offer_id=uuid4(), modality=ServiceModality.UNICA)


def _empty_brief(ext: OfferExt) -> SalesBrief:
    return SalesBrief(tenant_id=ext.tenant_id, offer_id=ext.offer_id)


def _empty_pricing() -> ThreeChargePricing:
    return ThreeChargePricing(
        price=None,
        price_mode=PriceMode.FIJO,
        price_publishable=False,
        currency="PEN",
        reservation=None,
        advance=None,
        financing=None,
    )


def test_total_is_26() -> None:
    res = compute_completeness(_empty_ext(), _empty_brief(_empty_ext()), _empty_pricing())
    assert res.total == 26


def test_empty_yields_zero_filled_all_missing() -> None:
    ext = _empty_ext()
    res = compute_completeness(ext, _empty_brief(ext), _empty_pricing())
    assert res.filled == 0
    assert len(res.missing) == 26


def test_partial_fill_counts() -> None:
    ext = _empty_ext()
    ext.description_long = "Tratamiento estético facial completo."
    ext.includes = "Consulta + procedimiento + control."
    ext.expected_result = "Piel más firme en 4 semanas."
    res = compute_completeness(ext, _empty_brief(ext), _empty_pricing())
    assert res.filled == 3
    assert len(res.missing) == 23
    assert "description_long" not in res.missing
    assert "includes" not in res.missing


def test_pricing_price_counts_as_filled() -> None:
    ext = _empty_ext()
    pricing = ThreeChargePricing(
        price=Decimal("500"),
        price_mode=PriceMode.FIJO,
        price_publishable=True,
        currency="PEN",
        reservation=None,
        advance=None,
        financing=None,
    )
    res = compute_completeness(ext, _empty_brief(ext), pricing)
    assert "price" not in res.missing
    assert res.filled >= 1


def test_initial_appt_fields_count() -> None:
    ext = _empty_ext()
    ext.initial_appt_type = InitialApptType.VALORACION_DIAGNOSTICO  # 1 of 3 fixed RN-32
    ext.initial_appt_duration_minutes = 30
    res = compute_completeness(ext, _empty_brief(ext), _empty_pricing())
    assert "initial_appt_type" not in res.missing
    assert "initial_appt_duration_minutes" not in res.missing


def test_sales_brief_fields_count() -> None:
    ext = _empty_ext()
    brief = _empty_brief(ext)
    brief.candidate_ideal = "Adultos 30-55 buscando rejuvenecimiento."
    brief.differentiators = "Tecnología láser de última generación."
    res = compute_completeness(ext, brief, _empty_pricing())
    assert "candidate_ideal" not in res.missing
    assert "differentiators" not in res.missing
    assert res.filled == 2


def test_completeness_never_blocks_is_active() -> None:
    # AC-19: even a fully-empty service can be active. completeness MUST be informational.
    ext = _empty_ext()
    ext.is_active = True
    res = compute_completeness(ext, _empty_brief(ext), _empty_pricing())
    # is_active is not a completeness field and the function returns regardless.
    assert res.filled == 0
    assert "is_active" not in res.missing
    assert ext.is_active is True


def test_empty_string_is_not_filled() -> None:
    ext = _empty_ext()
    ext.description_long = "   "  # whitespace-only counts as empty
    res = compute_completeness(ext, _empty_brief(ext), _empty_pricing())
    assert "description_long" in res.missing
