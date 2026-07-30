"""Story 11 T-payment-1 — `MercadoPagoAdapter` base class (LIFT SHARED to @luana/core/channels).

Verifies:
- API surface matches Story 11 03-arch-be.md § 11.2 (`create_preference` + `verify_payment` + HMAC).
- Idempotency header `X-Idempotency-Key=booking_id` per arch-be § 11 cross-applies.
- Status canonical mapping (MP `approved`→PAID, `pending`→PENDING, etc).
- HMAC-SHA256 webhook signature verification (anti-replay attack guard).
- Override hooks (`_extra_metadata`, `_status_overrides`) for vertical subclass customization.
- Currency from data (NO hardcoded 'USD' — LATAM uses ARS/CLP/MXN/COP/PEN/UYU/BRL).
- Amounts in cents (int) — adapter converts to MP's float major-units internally.
- Graceful degradation: explicit timeout (10s default) per `tessl__graceful-degradation`.

Codebase HTTP-mocking pattern: `httpx.MockTransport(handler)` injected via `client=`
(matches `core/luana-core-copilot/tests/test_trafilatura_client.py` precedent — no `respx` dep).

# [VITALIA-D4-LIFT-SHARED-MERCADOPAGO-TEST]
"""

from __future__ import annotations

import hashlib
import hmac as hmac_mod
import json
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import httpx
import pytest
from luana_core_channels.payment import (
    BackUrls,
    MercadoPagoAdapter,
    MpPreferenceResponse,
    PayerInfo,
    PaymentStatusEnum,
    PreferenceItem,
)

if TYPE_CHECKING:
    from collections.abc import Callable


# ─────────────────────────────────────────────────────────────
# Test helpers — MockTransport handler factory
# ─────────────────────────────────────────────────────────────


def _make_handler(
    *,
    pref_response: dict | None = None,
    pref_status: int = 201,
    pref_capture: list[httpx.Request] | None = None,
    payment_status_value: str | None = None,
) -> Callable[[httpx.Request], httpx.Response]:
    """Create MockTransport handler covering both POST /checkout/preferences and GET /v1/payments/{id}."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/checkout/preferences" and request.method == "POST":
            if pref_capture is not None:
                pref_capture.append(request)
            body = pref_response or {
                "id": "PREF-DEFAULT",
                "init_point": "https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=PREF-DEFAULT",
            }
            return httpx.Response(pref_status, json=body)
        if request.url.path.startswith("/v1/payments/") and request.method == "GET":
            return httpx.Response(200, json={"status": payment_status_value or "approved"})
        return httpx.Response(404, json={"error": "not_mocked"})

    return handler


# ─────────────────────────────────────────────────────────────
# Factory fixtures
# ─────────────────────────────────────────────────────────────


@pytest.fixture
def adapter() -> MercadoPagoAdapter:
    """Default base adapter (no vertical override)."""
    return MercadoPagoAdapter(
        access_token="TEST-ACCESS-TOKEN",
        webhook_secret="TEST-WEBHOOK-SECRET",
        timeout_seconds=5.0,
    )


@pytest.fixture
def tenant_id() -> UUID:
    return uuid4()


@pytest.fixture
def booking_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_items() -> list[PreferenceItem]:
    """Vitalia-style booking items (ARS pricing, dental consult)."""
    return [
        PreferenceItem(
            title="Consulta dental — Aurora Odontologia",
            quantity=1,
            unit_price_cents=15_000_00,  # 15.000,00 ARS in cents
            currency_id="ARS",
            description="Reserva confirmada con seña 100% reembolsable hasta 24h antes",
        )
    ]


@pytest.fixture
def sample_payer() -> PayerInfo:
    return PayerInfo(
        email="paciente@example.com",
        name="J.",
        surname="P.",
        phone="+541112345678",
    )


@pytest.fixture
def sample_back_urls() -> BackUrls:
    return BackUrls(
        success="https://vitalia.health/booking/success",
        failure="https://vitalia.health/booking/failure",
        pending="https://vitalia.health/booking/pending",
    )


# ─────────────────────────────────────────────────────────────
# create_preference happy path
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_preference_returns_init_point_url(
    adapter: MercadoPagoAdapter,
    tenant_id: UUID,
    booking_id: UUID,
    sample_items: list[PreferenceItem],
    sample_payer: PayerInfo,
    sample_back_urls: BackUrls,
) -> None:
    """Happy path — MP returns 201 with init_point + sandbox_init_point."""
    handler = _make_handler(
        pref_response={
            "id": "PREF-12345",
            "init_point": "https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=PREF-12345",
            "sandbox_init_point": "https://sandbox.mercadopago.com.ar/checkout/v1/redirect?pref_id=PREF-12345",
        }
    )
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=sample_items,
            payer=sample_payer,
            back_urls=sample_back_urls,
            client=client,
        )

    assert isinstance(result, MpPreferenceResponse)
    assert result.preference_id == "PREF-12345"
    assert result.init_point.startswith("https://www.mercadopago.com.ar/")
    assert result.sandbox_init_point is not None


@pytest.mark.asyncio
async def test_create_preference_sends_idempotency_key_booking_id_header(
    adapter: MercadoPagoAdapter,
    tenant_id: UUID,
    booking_id: UUID,
    sample_items: list[PreferenceItem],
    sample_payer: PayerInfo,
    sample_back_urls: BackUrls,
) -> None:
    """`X-Idempotency-Key=booking_id` MUST be present (per arch-be § 11)."""
    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_make_handler(pref_capture=captured))
    async with httpx.AsyncClient(transport=transport) as client:
        await adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=sample_items,
            payer=sample_payer,
            back_urls=sample_back_urls,
            client=client,
        )

    assert len(captured) == 1
    assert captured[0].headers.get("x-idempotency-key") == str(booking_id)


@pytest.mark.asyncio
async def test_create_preference_sends_authorization_bearer_header(
    adapter: MercadoPagoAdapter,
    tenant_id: UUID,
    booking_id: UUID,
    sample_items: list[PreferenceItem],
    sample_payer: PayerInfo,
    sample_back_urls: BackUrls,
) -> None:
    """Authorization: Bearer <access_token> per MP API contract."""
    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_make_handler(pref_capture=captured))
    async with httpx.AsyncClient(transport=transport) as client:
        await adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=sample_items,
            payer=sample_payer,
            back_urls=sample_back_urls,
            client=client,
        )

    assert captured[0].headers.get("authorization") == "Bearer TEST-ACCESS-TOKEN"


@pytest.mark.asyncio
async def test_create_preference_converts_cents_to_major_units(
    adapter: MercadoPagoAdapter,
    tenant_id: UUID,
    booking_id: UUID,
    sample_payer: PayerInfo,
    sample_back_urls: BackUrls,
) -> None:
    """Items.unit_price_cents = 15_000_00 → MP unit_price = 15000.0 (float major)."""
    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_make_handler(pref_capture=captured))
    items = [PreferenceItem(title="X", quantity=2, unit_price_cents=15_000_00, currency_id="ARS")]
    async with httpx.AsyncClient(transport=transport) as client:
        await adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=items,
            payer=sample_payer,
            back_urls=sample_back_urls,
            client=client,
        )

    parsed = json.loads(captured[0].read())
    assert parsed["items"][0]["unit_price"] == 15000.0
    assert parsed["items"][0]["quantity"] == 2
    assert parsed["items"][0]["currency_id"] == "ARS"


@pytest.mark.asyncio
async def test_create_preference_currency_from_data_not_hardcoded(
    adapter: MercadoPagoAdapter,
    tenant_id: UUID,
    booking_id: UUID,
    sample_payer: PayerInfo,
    sample_back_urls: BackUrls,
) -> None:
    """LATAM tenants use ARS / CLP / MXN / COP / PEN / UYU / BRL. NO hardcoded 'USD'."""
    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_make_handler(pref_capture=captured))
    async with httpx.AsyncClient(transport=transport) as client:
        for currency in ("ARS", "CLP", "MXN", "COP", "PEN", "UYU", "BRL"):
            items = [PreferenceItem(title="X", quantity=1, unit_price_cents=1000, currency_id=currency)]
            await adapter.create_preference(
                tenant_id=tenant_id,
                booking_id=booking_id,
                items=items,
                payer=sample_payer,
                back_urls=sample_back_urls,
                client=client,
            )

    sent_currencies = {json.loads(r.read())["items"][0]["currency_id"] for r in captured}
    assert sent_currencies == {"ARS", "CLP", "MXN", "COP", "PEN", "UYU", "BRL"}


@pytest.mark.asyncio
async def test_create_preference_includes_external_reference_tenant_booking(
    adapter: MercadoPagoAdapter,
    tenant_id: UUID,
    booking_id: UUID,
    sample_items: list[PreferenceItem],
    sample_payer: PayerInfo,
    sample_back_urls: BackUrls,
) -> None:
    """`external_reference` lets MP IPN webhooks correlate to internal IDs."""
    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_make_handler(pref_capture=captured))
    async with httpx.AsyncClient(transport=transport) as client:
        await adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=sample_items,
            payer=sample_payer,
            back_urls=sample_back_urls,
            client=client,
        )

    body = json.loads(captured[0].read())
    assert body["external_reference"] == f"{tenant_id}:{booking_id}"
    assert body["metadata"]["tenant_id"] == str(tenant_id)
    assert body["metadata"]["booking_id"] == str(booking_id)
    assert body["metadata"]["deposit_or_full"] == "deposit"


@pytest.mark.asyncio
async def test_create_preference_back_urls_and_auto_return(
    adapter: MercadoPagoAdapter,
    tenant_id: UUID,
    booking_id: UUID,
    sample_items: list[PreferenceItem],
    sample_payer: PayerInfo,
    sample_back_urls: BackUrls,
) -> None:
    """back_urls.{success,failure,pending} + auto_return=approved per MP best practice."""
    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_make_handler(pref_capture=captured))
    async with httpx.AsyncClient(transport=transport) as client:
        await adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=sample_items,
            payer=sample_payer,
            back_urls=sample_back_urls,
            client=client,
        )

    body = json.loads(captured[0].read())
    assert body["back_urls"]["success"] == "https://vitalia.health/booking/success"
    assert body["back_urls"]["failure"] == "https://vitalia.health/booking/failure"
    assert body["back_urls"]["pending"] == "https://vitalia.health/booking/pending"
    assert body["auto_return"] == "approved"


@pytest.mark.asyncio
async def test_create_preference_payer_info_optional(
    adapter: MercadoPagoAdapter,
    tenant_id: UUID,
    booking_id: UUID,
    sample_items: list[PreferenceItem],
    sample_back_urls: BackUrls,
) -> None:
    """Payer block omitted entirely when all PayerInfo fields are None (anti-PII default)."""
    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_make_handler(pref_capture=captured))
    async with httpx.AsyncClient(transport=transport) as client:
        await adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=sample_items,
            payer=PayerInfo(),  # all None
            back_urls=sample_back_urls,
            client=client,
        )

    body = json.loads(captured[0].read())
    assert "payer" not in body


@pytest.mark.asyncio
async def test_create_preference_propagates_http_error(
    adapter: MercadoPagoAdapter,
    tenant_id: UUID,
    booking_id: UUID,
    sample_items: list[PreferenceItem],
    sample_payer: PayerInfo,
    sample_back_urls: BackUrls,
) -> None:
    """4xx/5xx from MP raises HTTPStatusError (caller retries with backoff per graceful-degradation)."""
    handler = _make_handler(pref_response={"message": "invalid_token"}, pref_status=401)
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(httpx.HTTPStatusError):
            await adapter.create_preference(
                tenant_id=tenant_id,
                booking_id=booking_id,
                items=sample_items,
                payer=sample_payer,
                back_urls=sample_back_urls,
                client=client,
            )


# ─────────────────────────────────────────────────────────────
# verify_payment status mapping
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("mp_status", "expected"),
    [
        ("approved", PaymentStatusEnum.PAID),
        ("pending", PaymentStatusEnum.PENDING),
        ("in_process", PaymentStatusEnum.PENDING),
        ("rejected", PaymentStatusEnum.FAILED),
        ("cancelled", PaymentStatusEnum.CANCELLED),
        ("refunded", PaymentStatusEnum.REFUNDED),
        ("charged_back", PaymentStatusEnum.REFUNDED),
        ("unknown_future_value", PaymentStatusEnum.PENDING),  # safe default
    ],
)
async def test_verify_payment_canonical_status_map(
    adapter: MercadoPagoAdapter,
    mp_status: str,
    expected: PaymentStatusEnum,
) -> None:
    handler = _make_handler(payment_status_value=mp_status)
    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await adapter.verify_payment("MP-PAYMENT-12345", client=client)
    assert result == expected


# ─────────────────────────────────────────────────────────────
# Override hooks — vertical customization
# ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_extra_metadata_override_hook_injects_vertical_metadata(
    tenant_id: UUID,
    booking_id: UUID,
    sample_items: list[PreferenceItem],
    sample_payer: PayerInfo,
    sample_back_urls: BackUrls,
) -> None:
    """Subclass can inject `compliance_level` / `brand_slug` / `contains_phi` per vertical."""

    class VerticalSubclass(MercadoPagoAdapter):
        def _extra_metadata(
            self,
            *,
            tenant_id: UUID,  # noqa: ARG002
            booking_id: UUID | None,  # noqa: ARG002
            deposit_or_full: str,  # noqa: ARG002
        ) -> dict[str, object]:
            return {
                "compliance_level": "hipaa_lite",
                "contains_phi": False,
                "brand_slug": "vitalia",
            }

    sub = VerticalSubclass(access_token="X", webhook_secret="Y")
    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_make_handler(pref_capture=captured))
    async with httpx.AsyncClient(transport=transport) as client:
        await sub.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=sample_items,
            payer=sample_payer,
            back_urls=sample_back_urls,
            client=client,
        )

    body = json.loads(captured[0].read())
    assert body["metadata"]["compliance_level"] == "hipaa_lite"
    assert body["metadata"]["contains_phi"] is False
    assert body["metadata"]["brand_slug"] == "vitalia"
    # Base metadata still present
    assert body["metadata"]["tenant_id"] == str(tenant_id)
    assert body["metadata"]["booking_id"] == str(booking_id)


def test_status_overrides_hook_used_in_mapping(adapter: MercadoPagoAdapter) -> None:
    """Subclass can override mapping (e.g., `partially_refunded` → REFUNDED)."""

    class CustomMappingAdapter(MercadoPagoAdapter):
        def _status_overrides(self) -> dict[str, PaymentStatusEnum]:
            return {"partially_refunded": PaymentStatusEnum.REFUNDED}

    sub = CustomMappingAdapter(access_token="X")
    assert sub._map_mp_status("partially_refunded") == PaymentStatusEnum.REFUNDED
    # Canonical mapping still wins for known statuses
    assert sub._map_mp_status("approved") == PaymentStatusEnum.PAID


# ─────────────────────────────────────────────────────────────
# HMAC webhook signature verification (anti-replay)
# ─────────────────────────────────────────────────────────────


def test_verify_webhook_signature_valid_returns_true(
    adapter: MercadoPagoAdapter,
) -> None:
    """Correct HMAC-SHA256 over MP signed manifest returns True."""
    payload = b'{"action":"payment.updated","data":{"id":"123"}}'
    request_id = "req-abc-123"
    ts = "1709000000"
    manifest = f"id:{request_id};request-id:{request_id};ts:{ts};".encode()
    expected_sig = hmac_mod.new(
        b"TEST-WEBHOOK-SECRET",
        manifest + payload,
        hashlib.sha256,
    ).hexdigest()

    header = f"ts={ts},v1={expected_sig}"
    assert adapter.verify_webhook_signature(
        payload_body=payload,
        signature_header=header,
        request_id=request_id,
    )


def test_verify_webhook_signature_tampered_payload_returns_false(
    adapter: MercadoPagoAdapter,
) -> None:
    """Modified payload bytes → HMAC mismatch → False (anti-replay)."""
    original = b'{"action":"payment.updated","data":{"id":"123"}}'
    tampered = b'{"action":"payment.updated","data":{"id":"999"}}'
    request_id = "req-abc-123"
    ts = "1709000000"
    manifest = f"id:{request_id};request-id:{request_id};ts:{ts};".encode()
    sig_for_original = hmac_mod.new(
        b"TEST-WEBHOOK-SECRET",
        manifest + original,
        hashlib.sha256,
    ).hexdigest()

    header = f"ts={ts},v1={sig_for_original}"
    assert not adapter.verify_webhook_signature(
        payload_body=tampered,
        signature_header=header,
        request_id=request_id,
    )


def test_verify_webhook_signature_missing_secret_returns_false() -> None:
    """No webhook_secret configured → reject (no silent passes)."""
    adapter_no_secret = MercadoPagoAdapter(access_token="X", webhook_secret="")
    assert not adapter_no_secret.verify_webhook_signature(
        payload_body=b"{}",
        signature_header="ts=1,v1=abc",
        request_id="x",
    )


def test_verify_webhook_signature_malformed_header_returns_false(
    adapter: MercadoPagoAdapter,
) -> None:
    """Missing v1=... or ts=... → reject."""
    assert not adapter.verify_webhook_signature(
        payload_body=b"{}",
        signature_header="not-a-valid-header",
        request_id="x",
    )


def test_verify_webhook_signature_no_request_id_uses_ts_only_manifest(
    adapter: MercadoPagoAdapter,
) -> None:
    """Webhooks without request_id sign over ts + body only."""
    payload = b'{"action":"payment.updated"}'
    ts = "1709000000"
    manifest = f"ts:{ts};".encode()
    expected_sig = hmac_mod.new(
        b"TEST-WEBHOOK-SECRET",
        manifest + payload,
        hashlib.sha256,
    ).hexdigest()

    header = f"ts={ts},v1={expected_sig}"
    assert adapter.verify_webhook_signature(
        payload_body=payload,
        signature_header=header,
        request_id=None,
    )


# ─────────────────────────────────────────────────────────────
# Graceful degradation — explicit timeout
# ─────────────────────────────────────────────────────────────


def test_adapter_default_timeout_explicit_per_graceful_degradation_rule() -> None:
    """`timeout_seconds` default 10s — never None, never infinite."""
    a = MercadoPagoAdapter(access_token="X")
    assert a.timeout_seconds == 10.0
    assert a.timeout_seconds > 0


def test_adapter_access_token_falls_back_to_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    """Empty ctor token → env fallback (dev/test only — production callers MUST pass per-tenant token)."""
    monkeypatch.setenv("MERCADOPAGO_ACCESS_TOKEN", "ENV-FALLBACK-TOKEN")
    a = MercadoPagoAdapter(access_token="")
    assert a.access_token == "ENV-FALLBACK-TOKEN"


# ─────────────────────────────────────────────────────────────
# Provider id stable
# ─────────────────────────────────────────────────────────────


def test_provider_id_default_mercadopago(adapter: MercadoPagoAdapter) -> None:
    """provider_id == 'mercadopago' (canonical key for registry lookups)."""
    assert adapter.provider_id == "mercadopago"
