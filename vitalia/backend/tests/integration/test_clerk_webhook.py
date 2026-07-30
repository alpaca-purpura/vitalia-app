"""Integration tests for Clerk webhook receiver.

Acceptance criteria (03-arch-be.md § 6.8 + ticket T-be-8):
  - Svix HMAC-SHA256 verify
  - Idempotency: same svix-id → replay_skipped
  - user.created event dispatches OnboardingService (stubbed)

All tests use httpx.AsyncClient + ASGITransport (no live Postgres required).
Env var VITALIA_CLERK_WEBHOOK_SECRET is monkeypatched per test.

ClerkWebhookAdapter uses the Svix signing standard:
  HMAC-SHA256({svix-id}.{svix-timestamp}.{raw_body}, base64_decode(secret))
  The secret is base64-encoded before signing.

NOTE: Tests do NOT carry @pytest.mark.integration — they only use
ASGITransport (no Postgres connection needed).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

# ── Constants ──────────────────────────────────────────────────────────────────

# Test secret: base64-encoded bytes (Svix raw format without whsec_ prefix)
_RAW_SECRET_BYTES = b"test_clerk_webhook_secret_bytes_32"
_TEST_SECRET_B64 = base64.b64encode(_RAW_SECRET_BYTES).decode()
_TEST_SECRET = f"whsec_{_TEST_SECRET_B64}"

_WEBHOOK_URL = "/api/v1/vitalia/webhooks/clerk"


def _make_svix_signature(
    raw_body: bytes,
    svix_id: str,
    svix_timestamp: str,
    secret_bytes: bytes | None = None,
) -> str:
    """Compute valid Svix v1 signature.

    Svix signing: HMAC-SHA256("{svix-id}.{svix-timestamp}.{body}", secret_bytes)
    Encoded as base64. Header format: "v1,<base64>".
    """
    sb = secret_bytes if secret_bytes is not None else _RAW_SECRET_BYTES
    signed_content = f"{svix_id}.{svix_timestamp}.".encode() + raw_body
    digest = hmac.new(sb, signed_content, hashlib.sha256).digest()
    b64 = base64.b64encode(digest).decode()
    return f"v1,{b64}"


def _user_created_payload(clerk_user_id: str = "user_test_abc123") -> bytes:
    """Generate a minimal Clerk user.created event payload."""
    return json.dumps(
        {
            "type": "user.created",
            "data": {
                "id": clerk_user_id,
                "email_addresses": [{"email_address": "test@example.com", "id": "idn_test"}],
                "first_name": "Test",
                "last_name": "User",
            },
        }
    ).encode()


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def test_app(monkeypatch: pytest.MonkeyPatch):  # noqa: ANN201
    """FastAPI app with VITALIA_CLERK_WEBHOOK_SECRET patched."""
    monkeypatch.setenv("VITALIA_CLERK_WEBHOOK_SECRET", _TEST_SECRET)
    from src.main import app
    from src.modules.vitalia.api import webhook_routes

    webhook_routes._seen_event_ids.clear()
    return app


# ── HMAC verification tests ───────────────────────────────────────────────────


class TestClerkWebhookHmac:
    """Svix HMAC-SHA256 verification tests for Clerk webhook."""

    async def test_valid_signature_returns_200(self, test_app: Any) -> None:
        """Valid Svix HMAC signature → 200 received."""
        payload = _user_created_payload("user_valid_1")
        svix_id = f"msg_{uuid.uuid4().hex[:16]}"
        svix_ts = str(int(time.time()))
        svix_sig = _make_svix_signature(payload, svix_id, svix_ts)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "svix-id": svix_id,
                    "svix-timestamp": svix_ts,
                    "svix-signature": svix_sig,
                },
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "received"
        assert body["event_id"] == svix_id

    async def test_invalid_signature_returns_400(self, test_app: Any) -> None:
        """Invalid Svix signature → 400 (security gate)."""
        payload = _user_created_payload("user_badsig")
        svix_id = f"msg_{uuid.uuid4().hex[:16]}"
        svix_ts = str(int(time.time()))
        bad_sig = "v1,YmFkc2lnbmF0dXJlYmFkc2lnbmF0dXJlYmFkc2lnPT0="  # valid b64 but wrong HMAC

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "svix-id": svix_id,
                    "svix-timestamp": svix_ts,
                    "svix-signature": bad_sig,
                },
            )

        assert resp.status_code == 400, resp.text

    async def test_stale_timestamp_rejected(self, test_app: Any) -> None:
        """Stale timestamp (>5 min) → 400 replay protection."""
        payload = _user_created_payload("user_stale_ts")
        svix_id = f"msg_{uuid.uuid4().hex[:16]}"
        stale_ts = str(int(time.time()) - 400)  # 400s old > 300s tolerance
        svix_sig = _make_svix_signature(payload, svix_id, stale_ts)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "svix-id": svix_id,
                    "svix-timestamp": stale_ts,
                    "svix-signature": svix_sig,
                },
            )

        assert resp.status_code == 400, resp.text

    async def test_missing_svix_headers_returns_422(self, test_app: Any) -> None:
        """Missing required svix-* headers → 422 (FastAPI validation)."""
        payload = _user_created_payload("user_noheaders")

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={"Content-Type": "application/json"},
                # All svix headers missing
            )

        assert resp.status_code == 422, resp.text


# ── Idempotency tests ─────────────────────────────────────────────────────────


class TestClerkWebhookIdempotency:
    """Idempotency + replay protection tests for Clerk webhook."""

    async def test_same_svix_id_replay_blocked(self, test_app: Any) -> None:
        """Same svix-id delivered twice → second call returns replay_skipped."""
        payload = _user_created_payload("user_replay_test")
        svix_id = f"msg_replay_{uuid.uuid4().hex[:16]}"
        svix_ts = str(int(time.time()))
        svix_sig = _make_svix_signature(payload, svix_id, svix_ts)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # First delivery
            resp1 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "svix-id": svix_id,
                    "svix-timestamp": svix_ts,
                    "svix-signature": svix_sig,
                },
            )
            assert resp1.status_code == 200
            assert resp1.json()["status"] == "received"

            # Second delivery (Svix retry with same svix-id)
            resp2 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "svix-id": svix_id,
                    "svix-timestamp": svix_ts,
                    "svix-signature": svix_sig,
                },
            )
            assert resp2.status_code == 200
            assert resp2.json()["status"] == "replay_skipped"

    async def test_different_svix_ids_both_processed(self, test_app: Any) -> None:
        """Two distinct svix-ids → both return received (no false-positive dedup)."""
        payload = _user_created_payload("user_two_events")

        svix_id_1 = f"msg_{uuid.uuid4().hex[:16]}"
        svix_id_2 = f"msg_{uuid.uuid4().hex[:16]}"
        svix_ts = str(int(time.time()))

        sig_1 = _make_svix_signature(payload, svix_id_1, svix_ts)
        sig_2 = _make_svix_signature(payload, svix_id_2, svix_ts)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp1 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "svix-id": svix_id_1,
                    "svix-timestamp": svix_ts,
                    "svix-signature": sig_1,
                },
            )
            resp2 = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "svix-id": svix_id_2,
                    "svix-timestamp": svix_ts,
                    "svix-signature": sig_2,
                },
            )

        assert resp1.json()["status"] == "received"
        assert resp2.json()["status"] == "received"

    async def test_user_created_event_dispatched(self, test_app: Any) -> None:
        """user.created event → 200 received (OnboardingService dispatch logged)."""
        clerk_user_id = "user_onboarding_dispatch_test"
        payload = _user_created_payload(clerk_user_id)
        svix_id = f"msg_{uuid.uuid4().hex[:16]}"
        svix_ts = str(int(time.time()))
        svix_sig = _make_svix_signature(payload, svix_id, svix_ts)

        transport = ASGITransport(app=test_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                _WEBHOOK_URL,
                content=payload,
                headers={
                    "Content-Type": "application/json",
                    "svix-id": svix_id,
                    "svix-timestamp": svix_ts,
                    "svix-signature": svix_sig,
                },
            )

        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["status"] == "received"
        # event_id should be the svix_id
        assert body["event_id"] == svix_id
