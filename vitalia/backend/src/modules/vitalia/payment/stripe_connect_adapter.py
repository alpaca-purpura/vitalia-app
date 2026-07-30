# cap: payment.payment-gateways-latam-recurring
# story-origin: TBD
"""Vitalia Stripe Connect adapter — booking-deposit payment intents.

Per Story 11 03-arch-be.md § 11.1 + ticket T-payment-2:
- compliance_level=hipaa_lite metadata (D7 — NOT hipaa_full per Q6=B ratification).
- contains_phi=False — PHI is never sent to Stripe.
- idempotency_key=booking_id on every Stripe API call.
- HMAC webhook verification via env var VITALIA_STRIPE_WEBHOOK_SECRET.
- Explicit timeout on every HTTP call (tessl__graceful-degradation rule).

Vitalia-local scope (Story 11): Stripe Connect base is NOT in @luana/core yet.
Per 03-arch-be.md § 11.1: "extends @luana/core if base exists; Story 11.bis lifts".
Story 11 = vitalia-local OK (no cross-brand consumers for Stripe today).

Anti-duplication.md Step 0 GATE result (T-payment-2):
  grep found StripeConnectAdapter only as stub in prepaid_payment_service.py.
  This module REPLACES that stub with a real, testable implementation.
  The stub in prepaid_payment_service.py imports from this module post-ticket.

# [VITALIA-D7-HIPAA-LITE-STRIPE]
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any
from uuid import UUID

import httpx
import structlog

logger = structlog.get_logger()

# ── HIPAA-lite compliance constants (D7 — Q6=B ratified) ─────────────────────

_COMPLIANCE_LEVEL: str = "hipaa_lite"
_CONTAINS_PHI: bool = False
_BRAND_SLUG: str = "vitalia"

# Stripe API base URL
_STRIPE_API_BASE: str = "https://api.stripe.com"

# Default request timeout — every external call MUST have explicit timeout
# per tessl__graceful-degradation rule (Rule 1: every external call gets a timeout).
_DEFAULT_TIMEOUT_SECONDS: float = 10.0


# ── Result VO ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class PaymentIntentResult:
    """Result of a successful Stripe Payment Intent creation.

    Attributes:
        payment_intent_id: Stripe ``pi_*`` identifier.
        client_secret: Client secret for frontend confirmation (Stripe.js).
        status: Stripe intent status (e.g., ``requires_payment_method``).
        idempotency_key: The idempotency key used (equals ``str(booking_id)``).
        currency: ISO 4217 currency code (lower-cased per Stripe convention).
        amount_cents: Amount in minor units (e.g., 15000 = $150.00 USD).
    """

    payment_intent_id: str
    client_secret: str
    status: str
    idempotency_key: str
    currency: str
    amount_cents: int


# ── Adapter ───────────────────────────────────────────────────────────────────


@dataclass(slots=True)
class VitaliaStripeConnectAdapter:
    """Vitalia Stripe Connect booking-deposit adapter.

    Creates Stripe Payment Intents for booking deposits or full payments,
    always injecting HIPAA-lite compliance metadata. Verifies incoming
    webhook signatures using HMAC-SHA256.

    Args:
        secret_key: Stripe secret key (platform or per-tenant Connect account).
        connect_account_id: Stripe Connect account ID (``acct_*``). Used for
            Stripe-Account header on Connect-mode calls.
        webhook_secret: HMAC signing secret from VITALIA_STRIPE_WEBHOOK_SECRET
            env var. Must be non-empty to verify webhooks.
        timeout_seconds: HTTP request timeout in seconds (default 10s).
            Per tessl__graceful-degradation Rule 1 — explicit timeout mandatory.
        api_base_url: Override Stripe API base URL (useful for test doubles).
    """

    secret_key: str
    connect_account_id: str
    webhook_secret: str
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS
    api_base_url: str = _STRIPE_API_BASE

    # ── Public API ────────────────────────────────────────────────────────────

    async def create_payment_intent(
        self,
        *,
        amount: Decimal,
        currency: str,
        booking_id: UUID,
        deposit_or_full: str,
        description: str,
        customer_email: str | None = None,
    ) -> PaymentIntentResult:
        """Create a Stripe Payment Intent for a booking payment.

        Injects HIPAA-lite compliance metadata on every call (A1).
        Uses ``str(booking_id)`` as idempotency key (A3).
        Currency is forwarded from caller — never hardcoded (currency-handling rule).

        Args:
            amount: Decimal amount (e.g., Decimal("150.00")).
            currency: ISO 4217 code (e.g., "USD", "CLP"). Forwarded as-is.
            booking_id: UUID of the booking — used as Stripe idempotency key.
            deposit_or_full: "deposit" or "full" — stored in metadata for audit.
            description: Human-readable payment description.
            customer_email: Optional payer email for Stripe receipt.

        Returns:
            PaymentIntentResult with payment_intent_id, client_secret, status.

        Raises:
            httpx.HTTPStatusError: Stripe returned a non-2xx response.
            httpx.TimeoutException: Stripe did not respond within timeout_seconds.
        """
        amount_cents = int(amount * 100)
        idempotency_key = str(booking_id)

        payload: dict[str, Any] = {
            "amount": str(amount_cents),
            "currency": currency.lower(),
            "description": description,
            # A1: HIPAA-lite compliance metadata — always present
            "metadata[compliance_level]": _COMPLIANCE_LEVEL,
            "metadata[contains_phi]": str(_CONTAINS_PHI).lower(),
            "metadata[brand_slug]": _BRAND_SLUG,
            "metadata[booking_id]": str(booking_id),
            "metadata[deposit_or_full]": deposit_or_full,
        }
        if customer_email:
            payload["receipt_email"] = customer_email

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.secret_key}",
            # A3: idempotency_key = booking_id
            "Idempotency-Key": idempotency_key,
            "Content-Type": "application/x-www-form-urlencoded",
        }
        if self.connect_account_id:
            headers["Stripe-Account"] = self.connect_account_id

        url = f"{self.api_base_url}/v1/payment_intents"

        logger.info(
            "stripe_create_payment_intent",
            booking_id=str(booking_id),
            amount_cents=amount_cents,
            currency=currency,
            deposit_or_full=deposit_or_full,
        )

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(url, data=payload, headers=headers)

        resp.raise_for_status()
        data = resp.json()

        logger.info(
            "stripe_payment_intent_created",
            payment_intent_id=data["id"],
            booking_id=str(booking_id),
            status=data.get("status"),
        )

        return PaymentIntentResult(
            payment_intent_id=data["id"],
            client_secret=data.get("client_secret", ""),
            status=data.get("status", ""),
            idempotency_key=idempotency_key,
            currency=currency,
            amount_cents=amount_cents,
        )

    def verify_webhook(
        self,
        *,
        raw_body: bytes,
        stripe_signature: str,
        tolerance_seconds: int = 300,
    ) -> dict[str, Any]:
        """Verify Stripe webhook HMAC-SHA256 signature and return parsed event.

        Stripe sends ``Stripe-Signature: t=<timestamp>,v1=<hmac_hex>`` header.
        This method:
          1. Validates ``webhook_secret`` is configured.
          2. Extracts timestamp + signature from the header.
          3. Recomputes HMAC over ``{timestamp}.{raw_body}``.
          4. Compares using ``hmac.compare_digest`` (timing-safe).
          5. Checks timestamp tolerance to prevent replay attacks.

        Args:
            raw_body: Raw request body bytes (do NOT decode before passing).
            stripe_signature: Value of the ``Stripe-Signature`` HTTP header.
            tolerance_seconds: Max age of the event in seconds (default 300s).

        Returns:
            Parsed event dict (JSON-decoded from raw_body).

        Raises:
            ValueError: Signature invalid, timestamp missing, or webhook_secret empty.
        """
        if not self.webhook_secret:
            raise ValueError("webhook_secret is empty — set VITALIA_STRIPE_WEBHOOK_SECRET env var")

        # Parse Stripe-Signature header: t=<ts>,v1=<hex>
        parts: dict[str, str] = {}
        for part in stripe_signature.split(","):
            if "=" in part:
                k, _, v = part.partition("=")
                parts[k.strip()] = v.strip()

        timestamp_str = parts.get("t")
        signature_hex = parts.get("v1")

        if not timestamp_str or not signature_hex:
            raise ValueError("Invalid webhook signature header format — missing 't' or 'v1'")

        # Recompute expected signature
        signed_payload = f"{timestamp_str}.".encode() + raw_body
        expected_sig = hmac.new(self.webhook_secret.encode(), signed_payload, hashlib.sha256).hexdigest()

        # Timing-safe comparison (prevents timing attacks)
        if not hmac.compare_digest(expected_sig, signature_hex):
            raise ValueError("webhook signature mismatch — request body may have been tampered")

        # Replay attack protection
        try:
            event_ts = int(timestamp_str)
        except ValueError as exc:
            raise ValueError(f"Invalid timestamp in webhook signature: {timestamp_str!r}") from exc

        age_seconds = abs(int(time.time()) - event_ts)
        if age_seconds > tolerance_seconds:
            raise ValueError(f"webhook timestamp too old ({age_seconds}s > {tolerance_seconds}s tolerance)")

        return json.loads(raw_body)  # type: ignore[no-any-return]

    # ── Factory classmethod ────────────────────────────────────────────────────

    @classmethod
    def from_env(
        cls,
        *,
        connect_account_id: str,
        secret_key_env: str = "VITALIA_STRIPE_SECRET_KEY",
        webhook_secret_env: str = "VITALIA_STRIPE_WEBHOOK_SECRET",
    ) -> "VitaliaStripeConnectAdapter":
        """Construct adapter from environment variables.

        Args:
            connect_account_id: Stripe Connect account ID (tenant-specific).
            secret_key_env: Env var name for the Stripe secret key.
            webhook_secret_env: Env var name for the webhook signing secret.

        Returns:
            Configured adapter instance.
        """
        secret_key = os.environ.get(secret_key_env, "")
        webhook_secret = os.environ.get(webhook_secret_env, "")

        return cls(
            secret_key=secret_key,
            connect_account_id=connect_account_id,
            webhook_secret=webhook_secret,
        )
