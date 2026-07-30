# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""Payment provider registry (Vitalia brand-internal, NOT an engine EP).

Per `03-arch-be.md` § 6.1 — dispatch table consumed by the EP-3 tool
`vitalia.capture_payment` (router lives in
`vitalia/backend/src/modules/vitalia/agenda/application/services/payment_service.py`
— landed in a future ticket). The registry maps `provider_id` → metadata +
handler callable.

Slice 1 entries (T-infra-2 scope):
  - manual_cash / manual_card / manual_transfer / manual_mp / other → manual
    captures, no external HTTP. Real router lands in T-be-agenda-payment-manual.
  - mercadopago → webhook-driven, gated on side story
    `vitalia-payment-adapter-mvp`. Slot reserved with placeholder handler that
    raises NotImplementedError per anti-patterns rule (no silent fallback).

Slice 2 candidates (NOT shipped now): mercadopago_qr_live, culqi, niubiz,
stripe_connect. Promotion to engine EP-19 candidate documented in
`vitalia/docs/product/stories/vitalia-ux-discovery/delta-arch-notes.md`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Any, Literal


def _payment_not_implemented(provider_id: str, side_story: str):
    """Build a placeholder callable that raises NotImplementedError on invocation.

    Per `.claude/rules/anti-duplication.md` + Story 11 `_not_implemented_yet`
    pattern (no silent fallback). The exception message points at the side
    story that will provide the real adapter so the dispatch caller surfaces
    a clear failure mode.
    """

    def _placeholder(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"vitalia.connections.payment provider={provider_id!r} handler is a "
            f"placeholder — real implementation lands in side story {side_story!r}. "
            f"T-infra-2 scope mounts the slot only."
        )

    return _placeholder


@dataclass(frozen=True)
class PaymentProviderDef:
    """Metadata + dispatch callable for a Vitalia payment provider slot.

    Attributes:
        provider_id: canonical slug (snake_case)
        label_es: Spanish-neutro user-facing label (tuteo per `.claude/rules/spanish-text.md`)
        capture_method: `"manual" | "webhook" | "qr_live"` per arch § 6.1
        supports_refund: whether the adapter exposes a refund call
        supports_recurring: whether the adapter supports tokenized recurring billing
        handler: zero-arg callable returning the dispatcher / adapter binding.
                 For Slice 1 manual providers, the callable resolves to the manual
                 router; for side-story-gated entries it raises NotImplementedError
                 until the side story lands.
        handler_ref: dotted path to the dispatch entry (for documentation / arch
                     fitness inspection). Must start with `vitalia.connections.payment`.
    """

    provider_id: str
    label_es: str
    capture_method: Literal["manual", "webhook", "qr_live"]
    supports_refund: bool
    supports_recurring: bool
    handler: Any  # callable; Any keeps frozen dataclass simple — see PaymentHandler protocol future
    handler_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


def _manual_dispatch_stub(provider_id: str):
    """Placeholder for manual captures until the agenda payment service lands.

    Manual captures DO NOT require an external HTTP adapter — the
    `payment_service.record_manual_capture(provider_id=...)` call writes a
    `vitalia_payment_events` row directly. T-infra-2 ships only the registry
    slot; the service lands in `T-be-agenda-payment-manual` (future ticket
    under the agenda sub-story).
    """

    def _placeholder(*args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(
            f"vitalia.connections.payment manual provider={provider_id!r} "
            f"dispatcher pending — real router lands in "
            f"T-be-agenda-payment-manual (agenda sub-story)."
        )

    return _placeholder


PAYMENT_PROVIDER_REGISTRY: dict[str, PaymentProviderDef] = {
    "manual_cash": PaymentProviderDef(
        provider_id="manual_cash",
        label_es="Efectivo",
        capture_method="manual",
        supports_refund=True,
        supports_recurring=False,
        handler=_manual_dispatch_stub("manual_cash"),
        handler_ref="vitalia.connections.payment.manual:record_cash",
    ),
    "manual_card": PaymentProviderDef(
        provider_id="manual_card",
        label_es="Tarjeta (POS manual)",
        capture_method="manual",
        supports_refund=True,
        supports_recurring=False,
        handler=_manual_dispatch_stub("manual_card"),
        handler_ref="vitalia.connections.payment.manual:record_card",
    ),
    "manual_transfer": PaymentProviderDef(
        provider_id="manual_transfer",
        label_es="Transferencia bancaria",
        capture_method="manual",
        supports_refund=True,
        supports_recurring=False,
        handler=_manual_dispatch_stub("manual_transfer"),
        handler_ref="vitalia.connections.payment.manual:record_transfer",
    ),
    "manual_mp": PaymentProviderDef(
        provider_id="manual_mp",
        label_es="Mercado Pago (link manual)",
        capture_method="manual",
        supports_refund=True,
        supports_recurring=False,
        handler=_manual_dispatch_stub("manual_mp"),
        handler_ref="vitalia.connections.payment.manual:record_manual_mp",
    ),
    "other": PaymentProviderDef(
        provider_id="other",
        label_es="Otro medio de pago",
        capture_method="manual",
        supports_refund=False,
        supports_recurring=False,
        handler=_manual_dispatch_stub("other"),
        handler_ref="vitalia.connections.payment.manual:record_other",
    ),
    "mercadopago": PaymentProviderDef(
        provider_id="mercadopago",
        label_es="Mercado Pago (depósito automático)",
        capture_method="webhook",
        supports_refund=True,
        supports_recurring=False,
        handler=_payment_not_implemented("mercadopago", "vitalia-payment-adapter-mvp"),
        handler_ref="vitalia.connections.payment.mercadopago.adapter:create_payment",
        metadata={"side_story": "vitalia-payment-adapter-mvp"},
    ),
}


def get_payment_provider(provider_id: str) -> PaymentProviderDef | None:
    """Return the registered provider def or None if unknown.

    Callers in the payment service use this for dispatch; auditor arch tests
    use it for cross-checking that EP-3 `vitalia.capture_payment` only references
    registered slugs.
    """
    return PAYMENT_PROVIDER_REGISTRY.get(provider_id)


def list_payment_providers() -> tuple[str, ...]:
    """Return the tuple of registered provider slugs (deterministic order)."""
    return tuple(PAYMENT_PROVIDER_REGISTRY.keys())


__all__: Iterable[str] = (
    "PAYMENT_PROVIDER_REGISTRY",
    "PaymentProviderDef",
    "get_payment_provider",
    "list_payment_providers",
)
