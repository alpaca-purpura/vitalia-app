# cap: lisa.servicios
"""Offer value objects — frozen, immutable, invariant-enforcing.

Pure domain (zero framework import). Invariants in __post_init__:
  RN-11: price >= 0 (ThreeChargePricing.price, ServiceVariant.price).
  RN-29: ServiceVariant requires non-empty name.
  RN-31: ValueWithUnit.value >= 1 (typed numeric interval, never free text).
  RN-6 : ThreeChargePricing holds reservation/advance/financing independently.
Currency is str | None from tenant_locale — NEVER hardcode 'USD' (currency-handling).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from src.modules.vitalia.offer.domain.enums import IntervalUnit, PriceMode, ReservationKind


def _require_text(value: str | None, field: str) -> None:
    if value is None or not value.strip():
        raise ValueError(f"{field} must be non-empty")


@dataclass(frozen=True)
class ValueWithUnit:
    """RN-31 — a typed numeric interval (value >= 1) with a unit."""

    value: int
    unit: IntervalUnit

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError("value must be >= 1")


@dataclass(frozen=True)
class ServiceVariant:
    """RN-29 / RN-11 — a named price variant (e.g. body zone), price >= 0."""

    name: str
    price: Decimal
    note: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.name, "name")
        if self.price < 0:
            raise ValueError("price must be >= 0")


@dataclass(frozen=True)
class ReservationConfig:
    """First charge — deposit to hold the appointment."""

    enabled: bool
    amount: Decimal | None
    kind: ReservationKind


@dataclass(frozen=True)
class AdvanceConfig:
    """Second charge — advance payment before the procedure."""

    enabled: bool
    amount: Decimal | None
    kind: ReservationKind


@dataclass(frozen=True)
class FinancingConfig:
    """Third charge — installment financing. installments >= 1 when offered."""

    offered: bool
    installments: int | None
    interest_kind: str | None
    finance_partner: str | None = None

    def __post_init__(self) -> None:
        if self.offered and (self.installments is None or self.installments < 1):
            raise ValueError("installments must be >= 1 when financing offered")


@dataclass(frozen=True)
class ThreeChargePricing:
    """RN-6 / RN-11 — headline price + 3 independent charge components."""

    price: Decimal | None
    price_mode: PriceMode
    price_publishable: bool
    currency: str | None
    reservation: ReservationConfig | None
    advance: AdvanceConfig | None
    financing: FinancingConfig | None

    def __post_init__(self) -> None:
        if self.price is not None and self.price < 0:
            raise ValueError("price must be >= 0")


@dataclass(frozen=True)
class FaqPair:
    """Sales brief FAQ entry."""

    question: str
    answer: str

    def __post_init__(self) -> None:
        _require_text(self.question, "question")
        _require_text(self.answer, "answer")


@dataclass(frozen=True)
class ObjectionPair:
    """Sales brief objection/response entry."""

    objection_type: str
    response: str

    def __post_init__(self) -> None:
        _require_text(self.objection_type, "objection_type")
        _require_text(self.response, "response")
