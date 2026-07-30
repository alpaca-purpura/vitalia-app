# cap: lisa.servicios
# voseo-allowed: "vos" matched by hook is the value-objects module name (domain.vos), not voseo
"""Derived 3-charge pricing math (RN-6 · pure · mutation-critical).

compute_derived(pricing) returns DERIVED display values — NEVER persisted:
  advance_equiv: porcentaje → price * amount / 100 · monto → amount · else None
  per_month:     (price - reservation_equiv - advance_equiv) / installments
                 only when financing.offered and installments >= 1; else None
Any None price → all derived None (cannot compute without a base price).
"""

from __future__ import annotations

from decimal import Decimal

from src.modules.vitalia.offer.domain.enums import ReservationKind
from src.modules.vitalia.offer.domain.vos import (
    AdvanceConfig,
    ReservationConfig,
    ThreeChargePricing,
)


def _resolve_equiv(
    config: ReservationConfig | AdvanceConfig | None,
    price: Decimal,
) -> Decimal | None:
    """Resolve a %/monto charge into an absolute amount against ``price``."""
    if config is None or not config.enabled or config.amount is None:
        return None
    if config.kind is ReservationKind.PORCENTAJE:
        return price * config.amount / Decimal("100")
    return config.amount  # MONTO — absolute


def compute_derived(pricing: ThreeChargePricing) -> dict[str, Decimal | None]:
    """Compute display-only derived charges. Returns ``advance_equiv`` + ``per_month``."""
    price = pricing.price
    if price is None:
        return {"advance_equiv": None, "per_month": None}

    advance_equiv = _resolve_equiv(pricing.advance, price)

    per_month: Decimal | None = None
    financing = pricing.financing
    if financing is not None and financing.offered and financing.installments and financing.installments >= 1:
        reservation_equiv = _resolve_equiv(pricing.reservation, price) or Decimal("0")
        adv = advance_equiv or Decimal("0")
        financed_base = price - reservation_equiv - adv
        per_month = financed_base / Decimal(financing.installments)

    return {"advance_equiv": advance_equiv, "per_month": per_month}
