# cap: lisa.servicios
# voseo-allowed: "vos" matched by hook is the value-objects module name (domain.vos), not voseo
"""VO ↔ JSONB serializers for offer persistence.

VO bundles (variants, pricing, intervals, faq, objections) persist as JSONB.
Decimals round-trip as strings (lossless); enums as their .value. These helpers
keep the repos thin and the (de)serialization in one auditable place.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

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


def _dec(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


# — ServiceVariant —
def variant_to_dict(v: ServiceVariant) -> dict[str, Any]:
    return {"name": v.name, "price": str(v.price), "note": v.note}


def variant_from_dict(d: dict[str, Any]) -> ServiceVariant:
    return ServiceVariant(name=d["name"], price=Decimal(d["price"]), note=d.get("note"))


def variants_to_list(vs: list[ServiceVariant]) -> list[dict[str, Any]]:
    return [variant_to_dict(v) for v in vs]


def variants_from_list(raw: list[dict[str, Any]] | None) -> list[ServiceVariant]:
    return [variant_from_dict(d) for d in (raw or [])]


# — ValueWithUnit —
def interval_to_dict(iv: ValueWithUnit | None) -> dict[str, Any] | None:
    if iv is None:
        return None
    return {"value": iv.value, "unit": iv.unit.value}


def interval_from_dict(d: dict[str, Any] | None) -> ValueWithUnit | None:
    if d is None:
        return None
    return ValueWithUnit(value=d["value"], unit=IntervalUnit(d["unit"]))


# — ThreeChargePricing —
def _reservation_to_dict(r: ReservationConfig | None) -> dict[str, Any] | None:
    if r is None:
        return None
    return {"enabled": r.enabled, "amount": str(r.amount) if r.amount is not None else None, "kind": r.kind.value}


def _advance_to_dict(a: AdvanceConfig | None) -> dict[str, Any] | None:
    if a is None:
        return None
    return {"enabled": a.enabled, "amount": str(a.amount) if a.amount is not None else None, "kind": a.kind.value}


def _financing_to_dict(f: FinancingConfig | None) -> dict[str, Any] | None:
    if f is None:
        return None
    return {
        "offered": f.offered,
        "installments": f.installments,
        "interest_kind": f.interest_kind,
        "finance_partner": f.finance_partner,
    }


def pricing_to_dict(p: ThreeChargePricing | None) -> dict[str, Any] | None:
    if p is None:
        return None
    return {
        "price": str(p.price) if p.price is not None else None,
        "price_mode": p.price_mode.value,
        "price_publishable": p.price_publishable,
        "currency": p.currency,
        "reservation": _reservation_to_dict(p.reservation),
        "advance": _advance_to_dict(p.advance),
        "financing": _financing_to_dict(p.financing),
    }


def pricing_from_dict(d: dict[str, Any] | None) -> ThreeChargePricing | None:
    if d is None:
        return None
    res = d.get("reservation")
    adv = d.get("advance")
    fin = d.get("financing")
    return ThreeChargePricing(
        price=_dec(d.get("price")),
        price_mode=PriceMode(d["price_mode"]),
        price_publishable=d["price_publishable"],
        currency=d.get("currency"),
        reservation=(
            ReservationConfig(enabled=res["enabled"], amount=_dec(res["amount"]), kind=ReservationKind(res["kind"]))
            if res is not None
            else None
        ),
        advance=(
            AdvanceConfig(enabled=adv["enabled"], amount=_dec(adv["amount"]), kind=ReservationKind(adv["kind"]))
            if adv is not None
            else None
        ),
        financing=(
            FinancingConfig(
                offered=fin["offered"],
                installments=fin.get("installments"),
                interest_kind=fin.get("interest_kind"),
                finance_partner=fin.get("finance_partner"),
            )
            if fin is not None
            else None
        ),
    )


# — FaqPair / ObjectionPair —
def faq_to_list(faq: list[FaqPair]) -> list[dict[str, Any]]:
    return [{"question": f.question, "answer": f.answer} for f in faq]


def faq_from_list(raw: list[dict[str, Any]] | None) -> list[FaqPair]:
    return [FaqPair(question=d["question"], answer=d["answer"]) for d in (raw or [])]


def objections_to_list(objs: list[ObjectionPair]) -> list[dict[str, Any]]:
    return [{"objection_type": o.objection_type, "response": o.response} for o in objs]


def objections_from_list(raw: list[dict[str, Any]] | None) -> list[ObjectionPair]:
    return [ObjectionPair(objection_type=d["objection_type"], response=d["response"]) for d in (raw or [])]
