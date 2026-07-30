# cap: lisa.servicios
"""RED-first · VO DTO → domain invariant enforcement — T-R1 § A.1.

DTO `.to_domain()` builds the frozen domain VO; domain __post_init__ enforces
invariants so an invalid payload raises ValueError at the service boundary
(FastAPI catches that and returns 422).
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.modules.vitalia.offer.api.dtos import (
    AdvanceConfigDTO,
    FinancingConfigDTO,
    ReservationConfigDTO,
    ServiceVariantDTO,
    ThreeChargePricingDTO,
    ValueWithUnitDTO,
)
from src.modules.vitalia.offer.domain.enums import IntervalUnit, PriceMode, ReservationKind

# ── ValueWithUnitDTO ──────────────────────────────────────────────────────────


def test_value_with_unit_dto_ok() -> None:
    dto = ValueWithUnitDTO(value=4, unit=IntervalUnit.SEMANAS)
    vo = dto.to_domain()
    assert vo.value == 4
    assert vo.unit == IntervalUnit.SEMANAS


def test_value_with_unit_dto_zero_raises_value_error() -> None:
    dto = ValueWithUnitDTO(value=0, unit=IntervalUnit.DIAS)
    with pytest.raises(ValueError, match="value"):
        dto.to_domain()


def test_value_with_unit_dto_negative_raises_value_error() -> None:
    dto = ValueWithUnitDTO(value=-3, unit=IntervalUnit.MESES)
    with pytest.raises(ValueError, match="value"):
        dto.to_domain()


def test_value_with_unit_dto_min_value_ok() -> None:
    dto = ValueWithUnitDTO(value=1, unit=IntervalUnit.ANIOS)
    vo = dto.to_domain()
    assert vo.value == 1


# ── ServiceVariantDTO ─────────────────────────────────────────────────────────


def test_service_variant_dto_ok() -> None:
    dto = ServiceVariantDTO(name="Zona pequeña", price=Decimal("250"), note="Por sesión")
    vo = dto.to_domain()
    assert vo.name == "Zona pequeña"
    assert vo.price == Decimal("250")
    assert vo.note == "Por sesión"


def test_service_variant_dto_empty_name_raises_value_error() -> None:
    dto = ServiceVariantDTO(name="  ", price=Decimal("100"), note=None)
    with pytest.raises(ValueError, match="name"):
        dto.to_domain()


def test_service_variant_dto_negative_price_raises_value_error() -> None:
    dto = ServiceVariantDTO(name="OK", price=Decimal("-1"), note=None)
    with pytest.raises(ValueError, match="price"):
        dto.to_domain()


def test_service_variant_dto_zero_price_ok() -> None:
    dto = ServiceVariantDTO(name="Cortesía", price=Decimal("0"), note=None)
    vo = dto.to_domain()
    assert vo.price == Decimal("0")


# ── ThreeChargePricingDTO ─────────────────────────────────────────────────────


def test_three_charge_dto_ok() -> None:
    dto = ThreeChargePricingDTO(
        price=Decimal("1500"),
        price_mode=PriceMode.FIJO,
        price_publishable=True,
        currency="PEN",
        reservation=ReservationConfigDTO(enabled=True, amount=Decimal("300"), kind=ReservationKind.MONTO),
        advance=AdvanceConfigDTO(enabled=False, amount=None, kind=ReservationKind.MONTO),
        financing=FinancingConfigDTO(offered=True, installments=6, interest_kind="msi"),
    )
    vo = dto.to_domain()
    assert vo.price == Decimal("1500")
    assert vo.currency == "PEN"
    assert vo.reservation is not None
    assert vo.reservation.enabled is True
    assert vo.financing is not None
    assert vo.financing.installments == 6


def test_three_charge_dto_negative_price_raises_value_error() -> None:
    dto = ThreeChargePricingDTO(
        price=Decimal("-100"),
        price_mode=PriceMode.FIJO,
        price_publishable=True,
        currency="PEN",
        reservation=None,
        advance=None,
        financing=None,
    )
    with pytest.raises(ValueError, match="price"):
        dto.to_domain()


def test_three_charge_dto_none_price_ok() -> None:
    dto = ThreeChargePricingDTO(
        price=None,
        price_mode=PriceMode.RANGO,
        price_publishable=False,
        currency=None,
        reservation=None,
        advance=None,
        financing=None,
    )
    vo = dto.to_domain()
    assert vo.price is None
    assert vo.currency is None  # NEVER default 'USD' (currency-handling rule)


def test_three_charge_dto_financing_zero_installments_raises() -> None:
    dto = ThreeChargePricingDTO(
        price=Decimal("500"),
        price_mode=PriceMode.FIJO,
        price_publishable=True,
        currency="MXN",
        reservation=None,
        advance=None,
        financing=FinancingConfigDTO(offered=True, installments=0, interest_kind=None),
    )
    with pytest.raises(ValueError, match="installments"):
        dto.to_domain()


def test_three_charge_dto_financing_none_installments_not_offered_ok() -> None:
    dto = ThreeChargePricingDTO(
        price=Decimal("500"),
        price_mode=PriceMode.FIJO,
        price_publishable=True,
        currency="MXN",
        reservation=None,
        advance=None,
        financing=FinancingConfigDTO(offered=False, installments=None, interest_kind=None),
    )
    vo = dto.to_domain()
    assert vo.financing is not None
    assert vo.financing.offered is False
