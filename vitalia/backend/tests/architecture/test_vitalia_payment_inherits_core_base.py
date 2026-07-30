"""Architecture fitness — Story 11 T-payment-1 anti-duplication enforcement.

Per `.claude/rules/anti-duplication.md` § 0 cardinal:
  Vitalia payment adapters MUST EXTEND `luana_core_channels.payment` base
  classes. NEVER mirror HTTP plumbing / idempotency / HMAC / status mapping.

This test inspects the inheritance graph + verifies vitalia subclasses do NOT
re-define methods owned by the core base (composition over inheritance for
behavior — only override hooks).

# [VITALIA-D4-ARCH-FITNESS-INHERITANCE]
"""

from __future__ import annotations

import inspect

from luana_core_channels.payment import MercadoPagoAdapter

from src.modules.vitalia.payment import VitaliaMercadoPagoAdapter


def test_vitalia_mercadopago_adapter_extends_core_base() -> None:
    """`VitaliaMercadoPagoAdapter` subclasses `luana_core_channels.payment.MercadoPagoAdapter`."""
    assert issubclass(VitaliaMercadoPagoAdapter, MercadoPagoAdapter)


def test_vitalia_mercadopago_adapter_does_not_override_create_preference() -> None:
    """Vertical adapter MUST NOT re-implement HTTP plumbing — inherits from core base."""
    assert (
        VitaliaMercadoPagoAdapter.create_preference  # type: ignore[comparison-overlap]
        is MercadoPagoAdapter.create_preference
    ), (
        "VitaliaMercadoPagoAdapter.create_preference must inherit from MercadoPagoAdapter — "
        "vertical adapters override `_extra_metadata` / `_status_overrides` ONLY."
    )


def test_vitalia_mercadopago_adapter_does_not_override_verify_payment() -> None:
    """Vertical adapter MUST NOT re-implement status query — inherits from core base."""
    assert (
        VitaliaMercadoPagoAdapter.verify_payment  # type: ignore[comparison-overlap]
        is MercadoPagoAdapter.verify_payment
    )


def test_vitalia_mercadopago_adapter_does_not_override_webhook_signature() -> None:
    """HMAC verification lives in core base — vertical never overrides (security-critical)."""
    assert (
        VitaliaMercadoPagoAdapter.verify_webhook_signature  # type: ignore[comparison-overlap]
        is MercadoPagoAdapter.verify_webhook_signature
    )


def test_vitalia_mercadopago_adapter_overrides_extra_metadata() -> None:
    """Vertical adapter MUST override `_extra_metadata` to inject medical metadata."""
    assert (
        VitaliaMercadoPagoAdapter._extra_metadata  # type: ignore[comparison-overlap]
        is not MercadoPagoAdapter._extra_metadata
    )


def test_vitalia_extra_metadata_returns_hipaa_lite_compliance() -> None:
    """`compliance_level=hipaa_lite` per Story 11 Q6=B ratification."""
    from uuid import uuid4

    adapter = VitaliaMercadoPagoAdapter(access_token="X", webhook_secret="Y")
    metadata = adapter._extra_metadata(
        tenant_id=uuid4(),
        booking_id=uuid4(),
        deposit_or_full="deposit",
    )
    assert metadata["compliance_level"] == "hipaa_lite"
    assert metadata["contains_phi"] is False
    assert metadata["brand_slug"] == "vitalia"
    assert metadata["audit_category"] == "payment_intent_created"


def test_vitalia_adapter_no_local_http_calls_outside_core_methods() -> None:
    """No local httpx calls — confirms vertical adapter is pure metadata override."""
    src = inspect.getsource(VitaliaMercadoPagoAdapter)
    # Vertical must not contain HTTP primitives — those live in core base ONLY.
    assert "httpx" not in src, (
        "VitaliaMercadoPagoAdapter must not import/use httpx directly. "
        "All HTTP calls live in luana_core_channels.payment.MercadoPagoAdapter."
    )
    assert "AsyncClient" not in src
    assert ".post(" not in src
    assert ".get(" not in src


def test_vitalia_adapter_constants_exist() -> None:
    """Compliance constants exposed for cross-test/audit reference."""
    assert VitaliaMercadoPagoAdapter.COMPLIANCE_LEVEL == "hipaa_lite"
    assert VitaliaMercadoPagoAdapter.BRAND_SLUG == "vitalia"
    assert VitaliaMercadoPagoAdapter.CONTAINS_PHI is False
