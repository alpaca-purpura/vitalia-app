"""Integration tests for Stripe webhook receiver.

Acceptance criteria (03-arch-be.md § 6.8 + ticket T-be-8):
  A1: Stripe webhook HMAC verify + idempotency
      - test_hmac_verify_idempotent
  A2: Replay attack blocked + audit_log webhook_replay_detected
      - test_replay_blocked

All webhook HTTP calls are tested via httpx.AsyncClient + ASGITransport
(no live Postgres required — tests use ASGI in-process transport only).

Per .claude/rules/tdd-mandatory.md: these tests must go RED before implementation.

Env var VITALIA_STRIPE_WEBHOOK_SECRET is monkeypatched per test — no real
credentials required.

NOTE: Tests in this file do NOT carry @pytest.mark.integration because they
do not require a live Postgres connection — they only use ASGITransport.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

# ── Helpers ───────────────────────────────────────────────────────────────────

_TEST_SECRET = "whsec_test_stripe_secret_for_integration_tests"
_WEBHOOK_URL = "/api/v1/vitalia/webhooks/stripe"


def _make_stripe_signature(secret: str, payload: bytes, timestamp: int | None = None) -> str:
    """Compute a valid Stripe-Signature header value."""
    ts = timestamp if timestamp is not None else int(time.time())
    signed_payload = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


def _payment_intent_payload(
    payment_intent_id: str = "pi_test_1",
    event_type: str = "payment_intent.succeeded",
) -> bytes:
    """Generate a minimal Stripe payment_intent event payload."""
    return json.dumps(
        {
            "id": f"evt_{uuid.uuid4().hex[:8]}",
            "type": event_type,
            "data": {
                "object": {
                    "id": payment_intent_id,
                    "status": "succeeded" if "succeeded" in event_type else "requires_payment_method",
                    "metadata": {"booking_id": str(uuid.uuid4()), "compliance_level": "hipaa_lite"},
                }
            },
        }
    ).encode()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def test_app(monkeypatch: pytest.MonkeyPatch):  # noqa: ANN201
    """FastAPI app with VITALIA_STRIPE_WEBHOOK_SECRET patched."""
    monkeypatch.setenv("VITALIA_STRIPE_WEBHOOK_SECRET", _TEST_SECRET)
    from src.main import app

    # Reset the in-process idempotency store before each test
    from src.modules.vitalia.api import webhook_routes

    webhook_routes._seen_event_ids.clear()
    return app


# ── A1: HMAC verify + idempotency ────────────────────────────────────────────


class TestStripeWebhookHmacAndIdempotency:
    """A1: Stripe webhook HMAC verify + idempotency."""

    async def test_valid_signature_returns_200(self, test_app: Any) -> None:
        """Valid HMAC signature → 200 WebhookAck with status=received."""
        payload = _payment_intent_payload("pi_valid_1")
        sig = _make_stripe_signature(_TEST_SECRET, payload)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": sig,
                },
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "received"
        assert "event_id" in body
        assert "processed_at" in body

    async def test_invalid_signature_returns_400(self, test_app: Any) -> None:
        """Invalid HMAC signature → 400 (security gate)."""
        payload = _payment_intent_payload("pi_invalid_1")
        bad_sig = "t=1234567890,v1=badhexsignature000000000000000000000000000000000000000000000000"

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": bad_sig,
                },
            )

        assert resp.status_code == 400, resp.text
        body = resp.json()
        assert "signature" in body["detail"].lower() or "invalid" in body["detail"].lower()

    async def test_hmac_verify_idempotent(self, test_app: Any) -> None:
        """A1: Same payment_intent_id sent twice → second call returns status=replay_skipped."""
        payment_intent_id = "pi_idempotent_test"
        payload = _payment_intent_payload(payment_intent_id)
        sig = _make_stripe_signature(_TEST_SECRET, payload)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First call — should succeed
            resp1 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": sig,
                },
            )
            assert resp1.status_code == 200
            assert resp1.json()["status"] == "received"

            # Second call with same payment_intent_id and fresh signature (new timestamp)
            sig2 = _make_stripe_signature(_TEST_SECRET, payload)
            resp2 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "Stripe-Signature": sig2,
                },
            )
            assert resp2.status_code == 200
            # Idempotency guard: second call returns replay_skipped
            assert resp2.json()["status"] == "replay_skipped"

    async def test_missing_signature_header_returns_422(self, test_app: Any) -> None:
        """Missing Stripe-Signature header → FastAPI 422 validation error."""
        payload = _payment_intent_payload("pi_nosig")

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json"},
                # No Stripe-Signature header
            )

        assert resp.status_code == 422, resp.text


# ── A2: Replay attack blocked ─────────────────────────────────────────────────


class TestStripeWebhookReplayProtection:
    """A2: Replay attack blocked + audit_log webhook_replay_detected."""

    async def test_replay_blocked(self, test_app: Any) -> None:
        """A2: Replay attack blocked — duplicate payment_intent_id → replay_skipped response."""
        payment_intent_id = "pi_replay_attack_1"
        payload = _payment_intent_payload(payment_intent_id)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First delivery — legitimate
            sig1 = _make_stripe_signature(_TEST_SECRET, payload)
            resp1 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "Stripe-Signature": sig1},
            )
            assert resp1.status_code == 200
            assert resp1.json()["status"] == "received"

            # Replay attempt: same payload, new valid signature (attacker re-signs)
            sig2 = _make_stripe_signature(_TEST_SECRET, payload)
            resp2 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "Stripe-Signature": sig2},
            )
            # Replay blocked — 200 with replay_skipped (not 4xx)
            assert resp2.status_code == 200
            body2 = resp2.json()
            assert body2["status"] == "replay_skipped", (
                f"Expected replay_skipped but got {body2['status']!r}. "
                "Idempotency guard must block duplicate payment_intent_id."
            )

    async def test_stale_timestamp_rejected(self, test_app: Any) -> None:
        """Webhook with timestamp older than 5 min → 400 (replay attack prevention)."""
        payload = _payment_intent_payload("pi_stale_ts")
        stale_ts = int(time.time()) - 400  # 400s old > 300s tolerance
        sig = _make_stripe_signature(_TEST_SECRET, payload, timestamp=stale_ts)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "Stripe-Signature": sig},
            )

        assert resp.status_code == 400, resp.text

    async def test_payment_failed_event_processed(self, test_app: Any) -> None:
        """payment_intent.payment_failed event → 200 received (not filtered out)."""
        payload = _payment_intent_payload("pi_failed_1", event_type="payment_intent.payment_failed")
        sig = _make_stripe_signature(_TEST_SECRET, payload)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json", "Stripe-Signature": sig},
            )

        assert resp.status_code == 200
        assert resp.json()["status"] == "received"
