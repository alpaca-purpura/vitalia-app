# cap: lisa.servicios
"""RED-first · value objects (RN-6 · RN-11 · RN-29 · RN-31).

VOs are frozen dataclasses (immutable). Invariants enforced in __post_init__:
  - RN-11: price >= 0; ServiceVariant.price >= 0.
  - RN-31: ValueWithUnit.value >= 1 (typed numeric, never free text).
  - RN-29: ServiceVariant requires non-empty name.
  - RN-6: ThreeChargePricing holds reservation/advance/financing independently.
"""

from __future__ import annotations

import dataclasses
from decimal import Decimal

import pytest

from src.modules.vitalia.offer.domain.enums import IntervalUnit, PriceMode, ReservationKind
from src.modules.vitalia.offer.domain.vos import (
    AdvanceConfig,
    FaqPair,
    FinancingConfig,
    ObjectionPair,
    ReservationConfig,
    ServiceVariant,
    ThreeChargePricing,
    ValueWithUnit,
)


# RN-31 — ValueWithUnit typed numeric, value >= 1
def test_value_with_unit_ok() -> None:
    v = ValueWithUnit(value=4, unit=IntervalUnit.SEMANAS)
    assert v.value == 4
    assert v.unit is IntervalUnit.SEMANAS


def test_value_with_unit_rejects_zero() -> None:
    with pytest.raises(ValueError, match="value"):
        ValueWithUnit(value=0, unit=IntervalUnit.DIAS)


def test_value_with_unit_rejects_negative() -> None:
    with pytest.raises(ValueError, match="value"):
        ValueWithUnit(value=-2, unit=IntervalUnit.MESES)


def test_value_with_unit_is_frozen() -> None:
    v = ValueWithUnit(value=1, unit=IntervalUnit.ANIOS)
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.value = 9  # type: ignore[misc]


# RN-29 + RN-11 — ServiceVariant name required, price >= 0
def test_service_variant_ok() -> None:
    sv = ServiceVariant(name="Zona pequeña", price=Decimal("250"), note="Por sesión")
    assert sv.name == "Zona pequeña"
    assert sv.price == Decimal("250")


def test_service_variant_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="name"):
        ServiceVariant(name="  ", price=Decimal("100"), note=None)


def test_service_variant_rejects_negative_price() -> None:
    with pytest.raises(ValueError, match="price"):
        ServiceVariant(name="X", price=Decimal("-1"), note=None)


def test_service_variant_zero_price_ok() -> None:
    sv = ServiceVariant(name="Cortesía", price=Decimal("0"), note=None)
    assert sv.price == Decimal("0")


# RN-11 — ThreeChargePricing price >= 0
def test_three_charge_rejects_negative_price() -> None:
    with pytest.raises(ValueError, match="price"):
        ThreeChargePricing(
            price=Decimal("-5"),
            price_mode=PriceMode.FIJO,
            price_publishable=True,
            currency="PEN",
            reservation=None,
            advance=None,
            financing=None,
        )


def test_three_charge_price_none_ok() -> None:
    p = ThreeChargePricing(
        price=None,
        price_mode=PriceMode.RANGO,
        price_publishable=False,
        currency=None,
        reservation=None,
        advance=None,
        financing=None,
    )
    assert p.price is None
    assert p.currency is None  # never default 'USD'


# RN-6 — three charges independent
def test_three_charge_independent_components() -> None:
    p = ThreeChargePricing(
        price=Decimal("1000"),
        price_mode=PriceMode.FIJO,
        price_publishable=True,
        currency="PEN",
        reservation=ReservationConfig(enabled=True, amount=Decimal("100"), kind=ReservationKind.MONTO),
        advance=AdvanceConfig(enabled=False, amount=None, kind=ReservationKind.MONTO),
        financing=FinancingConfig(offered=True, installments=6, interest_kind="msi"),
    )
    assert p.reservation is not None and p.reservation.enabled is True
    assert p.advance is not None and p.advance.enabled is False
    assert p.financing is not None and p.financing.offered is True


def test_financing_rejects_zero_installments_when_offered() -> None:
    with pytest.raises(ValueError, match="installments"):
        FinancingConfig(offered=True, installments=0, interest_kind="msi")


def test_financing_not_offered_allows_none_installments() -> None:
    f = FinancingConfig(offered=False, installments=None, interest_kind=None)
    assert f.offered is False
    assert f.installments is None


def test_faq_pair_requires_both() -> None:
    fp = FaqPair(question="¿Duele?", answer="Mínimo.")
    assert fp.question and fp.answer
    with pytest.raises(ValueError, match="question"):
        FaqPair(question="", answer="x")


def test_objection_pair_requires_both() -> None:
    op = ObjectionPair(objection_type="precio", response="Financiamiento disponible.")
    assert op.objection_type and op.response
    with pytest.raises(ValueError, match="response"):
        ObjectionPair(objection_type="precio", response="  ")
