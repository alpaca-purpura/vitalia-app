"""Integration tests for MercadoPago IPN webhook receiver.

Acceptance criteria (03-arch-be.md § 6.8 + ticket T-be-8):
  - HMAC verify + idempotency (MP payment ID dedup)
  - Replay attack → replay_skipped

All tests use httpx.AsyncClient + ASGITransport (no live Postgres required).
Env var VITALIA_MERCADOPAGO_WEBHOOK_SECRET is monkeypatched per test.

NOTE: Tests do NOT carry @pytest.mark.integration — they only use
ASGITransport (no Postgres connection needed).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

# ── Constants ──────────────────────────────────────────────────────────────────

_TEST_SECRET = "mp_test_webhook_secret_for_integration_tests"
_WEBHOOK_URL = "/api/v1/vitalia/webhooks/mercadopago"


def _make_mp_signature_simple(secret: str, payload: bytes) -> str:
    """Compute MP simple HMAC-SHA256 hex signature (bare format)."""
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _make_mp_signature_structured(secret: str, payload: bytes, ts: int | None = None) -> str:
    """Compute MP structured X-Signature header: ts=<ts>,v1=<hex>."""
    timestamp = ts if ts is not None else int(time.time())
    sig_hex = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return f"ts={timestamp},v1={sig_hex}"


def _mp_ipn_payload(payment_id: str = "123456789") -> bytes:
    """Generate a minimal MercadoPago IPN notification payload."""
    return json.dumps(
        {
            "id": payment_id,
            "topic": "payment",
            "type": "payment",
            "data": {"id": payment_id},
        }
    ).encode()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def test_app(monkeypatch: pytest.MonkeyPatch):  # noqa: ANN201
    """FastAPI app with VITALIA_MERCADOPAGO_WEBHOOK_SECRET patched."""
    monkeypatch.setenv("VITALIA_MERCADOPAGO_WEBHOOK_SECRET", _TEST_SECRET)
    from src.main import app
    from src.modules.vitalia.api import webhook_routes

    webhook_routes._seen_event_ids.clear()
    return app


# ── HMAC verification tests ───────────────────────────────────────────────────


class TestMercadoPagoWebhookHmac:
    """HMAC verify tests for MercadoPago IPN receiver."""

    async def test_valid_simple_signature_returns_200(self, test_app: Any) -> None:
        """Valid simple HMAC signature → 200 received."""
        payload = _mp_ipn_payload("mp_100001")
        sig = _make_mp_signature_simple(_TEST_SECRET, payload)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "x-signature": sig},
            )

        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "received"

    async def test_valid_structured_signature_returns_200(self, test_app: Any) -> None:
        """Valid structured ts=<ts>,v1=<hex> signature → 200 received."""
        payload = _mp_ipn_payload("mp_100002")
        sig = _make_mp_signature_structured(_TEST_SECRET, payload)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "x-signature": sig},
            )

        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "received"

    async def test_invalid_signature_returns_400(self, test_app: Any) -> None:
        """Invalid HMAC signature → 400."""
        payload = _mp_ipn_payload("mp_100003")
        bad_sig = "badhexsignature00000000000000000000000000000000000000000000000000"

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "x-signature": bad_sig},
            )

        assert resp.status_code == 400, resp.text

    async def test_no_signature_header_proceeds(self, test_app: Any) -> None:
        """Missing X-Signature header → 200 (IPN legacy mode, warning logged)."""
        payload = _mp_ipn_payload("mp_100004")

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json"},
                # No x-signature header
            )

        # Should still succeed (warning logged but not blocked)
        assert resp.status_code == 200, resp.text


# ── Idempotency / replay tests ────────────────────────────────────────────────


class TestMercadoPagoWebhookIdempotency:
    """Idempotency + replay attack protection tests."""

    async def test_idempotent_same_payment_id(self, test_app: Any) -> None:
        """Same MP payment_id sent twice → second call returns replay_skipped."""
        payment_id = "mp_idempotent_9999"
        payload = _mp_ipn_payload(payment_id)
        sig = _make_mp_signature_simple(_TEST_SECRET, payload)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "x-signature": sig},
            )
            assert resp1.status_code == 200
            assert resp1.json()["status"] == "received"

            resp2 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "x-signature": sig},
            )
            assert resp2.status_code == 200
            assert resp2.json()["status"] == "replay_skipped"

    async def test_stale_structured_timestamp_rejected(self, test_app: Any) -> None:
        """Structured signature with stale timestamp → 400 replay rejection."""
        payload = _mp_ipn_payload("mp_stale_ts")
        stale_ts = int(time.time()) - 400  # 400s old > 300s tolerance
        sig = _make_mp_signature_structured(_TEST_SECRET, payload, ts=stale_ts)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "x-signature": sig},
            )

        assert resp.status_code == 400, resp.text

    async def test_different_payment_ids_both_processed(self, test_app: Any) -> None:
        """Two different payment IDs → both return received (no false-positive dedup)."""
        payload_a = _mp_ipn_payload("mp_unique_a")
        payload_b = _mp_ipn_payload("mp_unique_b")
        sig_a = _make_mp_signature_simple(_TEST_SECRET, payload_a)
        sig_b = _make_mp_signature_simple(_TEST_SECRET, payload_b)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp_a = await client.post(
                _WEBHOOK_URL,
                content=payload_a,
                headers={"Content-Type": "application/json", "x-signature": sig_a},
            )
            resp_b = await client.post(
                _WEBHOOK_URL,
                content=payload_b,
                headers={"Content-Type": "application/json", "x-signature": sig_b},
            )

        assert resp_a.status_code == 200
        assert resp_a.json()["status"] == "received"
        assert resp_b.status_code == 200
        assert resp_b.json()["status"] == "received"
