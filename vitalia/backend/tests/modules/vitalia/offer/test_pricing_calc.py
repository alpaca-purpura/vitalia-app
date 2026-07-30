# cap: lisa.servicios
"""RED-first · pricing_calc derived 3-charge calc (RN-6 · mutation-critical).

derived = compute_derived(pricing):
  advance_equiv: if advance.kind == porcentaje → price * advance.amount / 100
                 if advance.kind == monto      → advance.amount
                 else None
  per_month:     (price - reservation_equiv - advance_equiv) / installments
                 only when financing.offered and installments >= 1; else None
  reservation_equiv: same %/monto resolution as advance.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.modules.vitalia.offer.domain.enums import PriceMode, ReservationKind
from src.modules.vitalia.offer.domain.pricing_calc import compute_derived
from src.modules.vitalia.offer.domain.vos import (
    AdvanceConfig,
    FinancingConfig,
    ReservationConfig,
    ThreeChargePricing,
)


def _pricing(
    *,
    price: Decimal | None = Decimal("1000"),
    reservation: ReservationConfig | None = None,
    advance: AdvanceConfig | None = None,
    financing: FinancingConfig | None = None,
) -> ThreeChargePricing:
    return ThreeChargePricing(
        price=price,
        price_mode=PriceMode.FIJO,
        price_publishable=True,
        currency="PEN",
        reservation=reservation,
        advance=advance,
        financing=financing,
    )


def test_advance_percentage_equiv() -> None:
    p = _pricing(advance=AdvanceConfig(enabled=True, amount=Decimal("20"), kind=ReservationKind.PORCENTAJE))
    out = compute_derived(p)
    assert out["advance_equiv"] == Decimal("200")  # 1000 * 20/100


def test_advance_monto_equiv() -> None:
    p = _pricing(advance=AdvanceConfig(enabled=True, amount=Decimal("150"), kind=ReservationKind.MONTO))
    out = compute_derived(p)
    assert out["advance_equiv"] == Decimal("150")


def test_advance_disabled_is_none() -> None:
    p = _pricing(advance=AdvanceConfig(enabled=False, amount=None, kind=ReservationKind.MONTO))
    out = compute_derived(p)
    assert out["advance_equiv"] is None


def test_no_advance_is_none() -> None:
    out = compute_derived(_pricing(advance=None))
    assert out["advance_equiv"] is None


def test_per_month_with_financing() -> None:
    # price 1200, reservation 200 (monto), advance 100 (monto), 5 installments
    p = _pricing(
        price=Decimal("1200"),
        reservation=ReservationConfig(enabled=True, amount=Decimal("200"), kind=ReservationKind.MONTO),
        advance=AdvanceConfig(enabled=True, amount=Decimal("100"), kind=ReservationKind.MONTO),
        financing=FinancingConfig(offered=True, installments=5, interest_kind="msi"),
    )
    out = compute_derived(p)
    # (1200 - 200 - 100) / 5 = 180
    assert out["per_month"] == Decimal("180")


def test_per_month_no_financing_is_none() -> None:
    p = _pricing(financing=FinancingConfig(offered=False, installments=None, interest_kind=None))
    out = compute_derived(p)
    assert out["per_month"] is None


def test_per_month_reservation_percentage() -> None:
    # price 1000, reservation 10% = 100, no advance, 3 installments → (1000-100)/3 = 300
    p = _pricing(
        price=Decimal("1000"),
        reservation=ReservationConfig(enabled=True, amount=Decimal("10"), kind=ReservationKind.PORCENTAJE),
        financing=FinancingConfig(offered=True, installments=3, interest_kind="con_interes"),
    )
    out = compute_derived(p)
    assert out["per_month"] == Decimal("300")


def test_per_month_not_offered_is_none() -> None:
    # installments=0 is unreachable: the FinancingConfig VO rejects it at construction
    # (RN-6 installments >= 1 when offered — covered in test_vos). Here: financing not
    # offered → per_month must be None even though installments could be set.
    p = _pricing(financing=FinancingConfig(offered=False, installments=None, interest_kind=None))
    out = compute_derived(p)
    assert out["per_month"] is None


def test_price_none_yields_none_derived() -> None:
    p = _pricing(price=None, advance=AdvanceConfig(enabled=True, amount=Decimal("20"), kind=ReservationKind.PORCENTAJE))
    out = compute_derived(p)
    assert out["advance_equiv"] is None
    assert out["per_month"] is None


@pytest.mark.parametrize(
    ("pct", "expected"),
    [(Decimal("0"), Decimal("0")), (Decimal("50"), Decimal("500")), (Decimal("100"), Decimal("1000"))],
)
def test_advance_percentage_boundaries(pct: Decimal, expected: Decimal) -> None:
    p = _pricing(advance=AdvanceConfig(enabled=True, amount=pct, kind=ReservationKind.PORCENTAJE))
    assert compute_derived(p)["advance_equiv"] == expected
