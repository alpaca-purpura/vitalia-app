"""Integration tests for VitaliaStripeConnectAdapter.

Acceptance criteria (03-arch-be.md § 11.1 + ticket T-payment-2):
  A1: payment_intent metadata.compliance_level=hipaa_lite always
  A2: HMAC webhook verification (valid sig → dict; invalid sig → ValueError)
  A3: idempotency_key=booking_id in Stripe API call

All Stripe HTTP calls are mocked — no real Stripe API credentials required.

Per .claude/rules/tdd-mandatory.md: these tests must go RED before implementation.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_stripe_signature(secret: str, payload: bytes, timestamp: int | None = None) -> str:
    """Compute a valid Stripe-Signature header value."""
    ts = timestamp if timestamp is not None else int(time.time())
    signed_payload = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed_payload, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestStripeConnectAdapterCompliance:
    """A1: metadata.compliance_level=hipaa_lite always."""

    @pytest.mark.integration
    async def test_compliance_metadata(self) -> None:
        """A1: payment_intent metadata must always carry compliance_level=hipaa_lite."""
        from src.modules.vitalia.payment.stripe_connect_adapter import VitaliaStripeConnectAdapter

        adapter = VitaliaStripeConnectAdapter(
            secret_key="sk_test_fake",
            connect_account_id="acct_test_123",
            webhook_secret="whsec_test_fake",
        )

        # Mock the httpx call — we inspect what payload was sent
        captured_payload: dict = {}

        async def _mock_post(url: str, *, data: dict, headers: dict) -> MagicMock:  # noqa: ARG001
            captured_payload.update(data)
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {
                "id": "pi_test_123",
                "client_secret": "pi_test_123_secret",
                "status": "requires_payment_method",
            }
            return mock_resp

        booking_id = uuid.uuid4()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = _mock_post
            mock_client_cls.return_value = mock_client

            result = await adapter.create_payment_intent(
                amount=Decimal("150.00"),
                currency="USD",
                booking_id=booking_id,
                deposit_or_full="deposit",
                description="Consulta dental — Aurora",
            )

        # A1: compliance metadata present
        assert captured_payload.get("metadata[compliance_level]") == "hipaa_lite"
        assert captured_payload.get("metadata[contains_phi]") == "false"
        assert captured_payload.get("metadata[brand_slug]") == "vitalia"
        # A3: idempotency_key=booking_id
        assert result.idempotency_key == str(booking_id)

    @pytest.mark.integration
    async def test_compliance_metadata_always_present_full_payment(self) -> None:
        """A1: compliance_level=hipaa_lite also for full payments (not just deposits)."""
        from src.modules.vitalia.payment.stripe_connect_adapter import VitaliaStripeConnectAdapter

        adapter = VitaliaStripeConnectAdapter(
            secret_key="sk_test_fake",
            connect_account_id="acct_test_123",
            webhook_secret="whsec_test_fake",
        )

        captured_payload: dict = {}

        async def _mock_post(url: str, *, data: dict, headers: dict) -> MagicMock:  # noqa: ARG001
            captured_payload.update(data)
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {
                "id": "pi_test_456",
                "client_secret": "pi_test_456_secret",
                "status": "requires_payment_method",
            }
            return mock_resp

        booking_id = uuid.uuid4()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = _mock_post
            mock_client_cls.return_value = mock_client

            await adapter.create_payment_intent(
                amount=Decimal("500.00"),
                currency="USD",
                booking_id=booking_id,
                deposit_or_full="full",
                description="Tratamiento completo de ortodoncia",
            )

        assert captured_payload.get("metadata[compliance_level]") == "hipaa_lite"
        assert captured_payload.get("metadata[contains_phi]") == "false"


class TestStripeConnectAdapterIdempotency:
    """A3: idempotency_key=booking_id in Stripe API call."""

    @pytest.mark.integration
    async def test_idempotency_key_is_booking_id(self) -> None:
        """A3: Stripe API call MUST include Idempotency-Key header equal to booking_id."""
        from src.modules.vitalia.payment.stripe_connect_adapter import VitaliaStripeConnectAdapter

        adapter = VitaliaStripeConnectAdapter(
            secret_key="sk_test_fake",
            connect_account_id="acct_test_123",
            webhook_secret="whsec_test_fake",
        )

        captured_headers: dict = {}

        async def _mock_post(url: str, *, data: dict, headers: dict) -> MagicMock:  # noqa: ARG001
            captured_headers.update(headers)
            mock_resp = MagicMock()
            mock_resp.raise_for_status = MagicMock()
            mock_resp.json.return_value = {
                "id": "pi_test_789",
                "client_secret": "pi_test_789_secret",
                "status": "requires_payment_method",
            }
            return mock_resp

        booking_id = uuid.uuid4()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client.post = _mock_post
            mock_client_cls.return_value = mock_client

            await adapter.create_payment_intent(
                amount=Decimal("75.00"),
                currency="CLP",
                booking_id=booking_id,
                deposit_or_full="deposit",
                description="Sesión psicología",
            )

        assert "Idempotency-Key" in captured_headers
        assert captured_headers["Idempotency-Key"] == str(booking_id)


class TestStripeConnectAdapterWebhook:
    """HMAC webhook verification tests."""

    @pytest.mark.integration
    def test_verify_webhook_valid_signature(self) -> None:
        """Valid HMAC signature → returns parsed event dict."""
        from src.modules.vitalia.payment.stripe_connect_adapter import VitaliaStripeConnectAdapter

        secret = "whsec_test_valid_secret"
        adapter = VitaliaStripeConnectAdapter(
            secret_key="sk_test_fake",
            connect_account_id="acct_test_123",
            webhook_secret=secret,
        )

        payload = json.dumps(
            {
                "id": "evt_test_1",
                "type": "payment_intent.succeeded",
                "data": {"object": {"id": "pi_test_1", "metadata": {"booking_id": "abc-123"}}},
            }
        ).encode()

        ts = int(time.time())
        sig_header = _make_stripe_signature(secret, payload, timestamp=ts)

        event = adapter.verify_webhook(raw_body=payload, stripe_signature=sig_header)

        assert event["type"] == "payment_intent.succeeded"
        assert event["data"]["object"]["id"] == "pi_test_1"

    @pytest.mark.integration
    def test_verify_webhook_invalid_signature_raises(self) -> None:
        """Invalid HMAC signature → ValueError raised (security gate)."""
        from src.modules.vitalia.payment.stripe_connect_adapter import VitaliaStripeConnectAdapter

        adapter = VitaliaStripeConnectAdapter(
            secret_key="sk_test_fake",
            connect_account_id="acct_test_123",
            webhook_secret="whsec_real_secret",
        )

        payload = json.dumps({"type": "payment_intent.succeeded"}).encode()
        bad_sig = "t=1234567890,v1=badhexsignature"

        with pytest.raises(ValueError, match="webhook signature"):
            adapter.verify_webhook(raw_body=payload, stripe_signature=bad_sig)

    @pytest.mark.integration
    def test_verify_webhook_tampered_payload_raises(self) -> None:
        """Payload tampered after signing → ValueError."""
        from src.modules.vitalia.payment.stripe_connect_adapter import VitaliaStripeConnectAdapter

        secret = "whsec_test_tamper"
        adapter = VitaliaStripeConnectAdapter(
            secret_key="sk_test_fake",
            connect_account_id="acct_test_123",
            webhook_secret=secret,
        )

        original_payload = json.dumps({"type": "payment_intent.succeeded"}).encode()
        tampered_payload = json.dumps({"type": "payment_intent.FORGED"}).encode()

        ts = int(time.time())
        sig_header = _make_stripe_signature(secret, original_payload, timestamp=ts)

        with pytest.raises(ValueError, match="webhook signature"):
            adapter.verify_webhook(raw_body=tampered_payload, stripe_signature=sig_header)

    @pytest.mark.integration
    def test_verify_webhook_missing_secret_raises(self) -> None:
        """Webhook verification without configured secret raises at instantiation."""
        from src.modules.vitalia.payment.stripe_connect_adapter import VitaliaStripeConnectAdapter

        adapter = VitaliaStripeConnectAdapter(
            secret_key="sk_test_fake",
            connect_account_id="acct_test_123",
            webhook_secret="",  # empty secret
        )

        payload = json.dumps({"type": "test"}).encode()
        fake_sig = "t=123,v1=abc"

        with pytest.raises(ValueError, match="webhook_secret"):
            adapter.verify_webhook(raw_body=payload, stripe_signature=fake_sig)


class TestStripeConnectAdapterTimeout:
    """Graceful degradation: external call has timeout."""

    @pytest.mark.integration
    async def test_timeout_propagated_to_httpx(self) -> None:
        """Timeout setting passed to httpx.AsyncClient."""
        from src.modules.vitalia.payment.stripe_connect_adapter import VitaliaStripeConnectAdapter

        adapter = VitaliaStripeConnectAdapter(
            secret_key="sk_test_fake",
            connect_account_id="acct_test_123",
            webhook_secret="whsec_fake",
            timeout_seconds=7.5,
        )

        captured_timeout = None

        with patch("httpx.AsyncClient") as mock_client_cls:

            def _check_timeout(*args, **kwargs):  # noqa: ANN001, ANN002, ANN003
                nonlocal captured_timeout
                captured_timeout = kwargs.get("timeout")
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=None)

                async def _post(url, *, data, headers):  # noqa: ANN001, ANN202
                    mock_resp = MagicMock()
                    mock_resp.raise_for_status = MagicMock()
                    mock_resp.json.return_value = {
                        "id": "pi_timeout_test",
                        "client_secret": "s",
                        "status": "requires_payment_method",
                    }
                    return mock_resp

                mock_client.post = _post
                return mock_client

            mock_client_cls.side_effect = _check_timeout

            booking_id = uuid.uuid4()
            await adapter.create_payment_intent(
                amount=Decimal("100.00"),
                currency="USD",
                booking_id=booking_id,
                deposit_or_full="deposit",
                description="Test timeout",
            )

        assert captured_timeout == 7.5
