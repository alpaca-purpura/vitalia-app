"""Vitalia integration test — MercadoPago adapter end-to-end with mocked MP API.

Verifies the EXTENDS contract is wired correctly:
- Vertical metadata (compliance_level=hipaa_lite + brand_slug=vitalia) flows
  through to the MP preference payload via core base's `create_preference`.
- Idempotency key + Authorization header still applied (inherited behavior).

# [VITALIA-D4-INTEGRATION-MERCADOPAGO]
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

import httpx
import pytest
from luana_core_channels.payment import (
    BackUrls,
    PayerInfo,
    PreferenceItem,
)

from src.modules.vitalia.payment import VitaliaMercadoPagoAdapter

if TYPE_CHECKING:
    from collections.abc import Callable


def _mp_preferences_handler(
    capture: list[httpx.Request],
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/checkout/preferences" and request.method == "POST":
            capture.append(request)
            return httpx.Response(
                201,
                json={
                    "id": "PREF-VITALIA-INT-001",
                    "init_point": "https://www.mercadopago.com.ar/checkout/v1/redirect?pref_id=PREF-VITALIA-INT-001",
                    "sandbox_init_point": "https://sandbox.mercadopago.com.ar/checkout/v1/redirect?pref_id=PREF-VITALIA-INT-001",
                },
            )
        return httpx.Response(404, json={"error": "not_mocked"})

    return handler


@pytest.fixture
def vitalia_adapter() -> VitaliaMercadoPagoAdapter:
    return VitaliaMercadoPagoAdapter(
        access_token="VITALIA-TEST-TOKEN",
        webhook_secret="VITALIA-WEBHOOK-SECRET",
        timeout_seconds=5.0,
    )


@pytest.fixture
def aurora_dental_booking() -> tuple[UUID, UUID, list[PreferenceItem], PayerInfo, BackUrls]:
    """Aurora Odontologia (AR fixture) — dental consult booking deposit."""
    tenant_id = uuid4()
    booking_id = uuid4()
    items = [
        PreferenceItem(
            title="Reserva consulta dental — Aurora Odontologia",
            quantity=1,
            unit_price_cents=15_000_00,  # 15.000,00 ARS
            currency_id="ARS",
            description="Seña reembolsable hasta 24h antes",
        )
    ]
    # PII masked at adapter boundary — only initials + masked phone reach MP.
    payer = PayerInfo(
        email="paciente@masked.example.com",
        name="J.",
        surname="P.",
        phone="+54***5678",
    )
    back_urls = BackUrls(
        success="https://aurora.vitalia.health/booking/success",
        failure="https://aurora.vitalia.health/booking/failure",
        pending="https://aurora.vitalia.health/booking/pending",
    )
    return tenant_id, booking_id, items, payer, back_urls


@pytest.mark.asyncio
async def test_vitalia_create_preference_injects_hipaa_lite_metadata(
    vitalia_adapter: VitaliaMercadoPagoAdapter,
    aurora_dental_booking: tuple[UUID, UUID, list[PreferenceItem], PayerInfo, BackUrls],
) -> None:
    """End-to-end: vertical metadata MUST land in MP preference payload."""
    tenant_id, booking_id, items, payer, back_urls = aurora_dental_booking

    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_mp_preferences_handler(captured))

    async with httpx.AsyncClient(transport=transport) as client:
        response = await vitalia_adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=items,
            payer=payer,
            back_urls=back_urls,
            deposit_or_full="deposit",
            client=client,
        )

    assert response.preference_id == "PREF-VITALIA-INT-001"
    assert "vitalia.health" in response.init_point or "mercadopago.com" in response.init_point

    body = json.loads(captured[0].read())
    metadata = body["metadata"]
    # Base metadata
    assert metadata["tenant_id"] == str(tenant_id)
    assert metadata["booking_id"] == str(booking_id)
    # Vertical injection
    assert metadata["compliance_level"] == "hipaa_lite"
    assert metadata["contains_phi"] is False
    assert metadata["brand_slug"] == "vitalia"
    assert metadata["audit_category"] == "payment_intent_created"
    assert metadata["deposit_or_full"] == "deposit"


@pytest.mark.asyncio
async def test_vitalia_create_preference_idempotency_key_inherited(
    vitalia_adapter: VitaliaMercadoPagoAdapter,
    aurora_dental_booking: tuple[UUID, UUID, list[PreferenceItem], PayerInfo, BackUrls],
) -> None:
    """`X-Idempotency-Key=booking_id` from core base must still apply post-extend."""
    tenant_id, booking_id, items, payer, back_urls = aurora_dental_booking

    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_mp_preferences_handler(captured))

    async with httpx.AsyncClient(transport=transport) as client:
        await vitalia_adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=items,
            payer=payer,
            back_urls=back_urls,
            client=client,
        )

    assert captured[0].headers.get("x-idempotency-key") == str(booking_id)
    assert captured[0].headers.get("authorization") == "Bearer VITALIA-TEST-TOKEN"


@pytest.mark.asyncio
async def test_vitalia_create_preference_uses_ars_currency_not_usd(
    vitalia_adapter: VitaliaMercadoPagoAdapter,
    aurora_dental_booking: tuple[UUID, UUID, list[PreferenceItem], PayerInfo, BackUrls],
) -> None:
    """Aurora AR tenant → ARS, NEVER hardcoded USD (master-data + currency-handling rules)."""
    tenant_id, booking_id, items, payer, back_urls = aurora_dental_booking

    captured: list[httpx.Request] = []
    transport = httpx.MockTransport(_mp_preferences_handler(captured))

    async with httpx.AsyncClient(transport=transport) as client:
        await vitalia_adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=items,
            payer=payer,
            back_urls=back_urls,
            client=client,
        )

    body = json.loads(captured[0].read())
    assert body["items"][0]["currency_id"] == "ARS"
    assert body["items"][0]["unit_price"] == 15000.0  # cents → major units
