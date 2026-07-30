"""Stripe Connect Payment Intent adapter — booking-deposit + subscription channel.

Generic base lifted to @luana/core/channels per Story 12 T-payment-1
(anti-duplication.md: Story 11 kept vitalia-local; lift happens here Story 12).

Verticals subclass via composition + override hooks (`_extra_metadata`,
`_compliance_metadata`) — they do NOT re-implement HTTP plumbing.

Distinct from `luana-core-sales-agent.application.tools.payment` (sales-agent
CLOSER tool that returns a checkout link inside chat). This adapter handles:
- Booking-deposit payment intent creation with idempotency + HMAC + compliance metadata.
- Connect account routing (Stripe-Account header for platform billing).
- Webhook verification (HMAC-SHA256, replay-attack protection).

Currency: forwarded from caller — NEVER hardcoded (master-data.md + currency-handling.md).

# [STORY12-T-PAYMENT-1-LIFT-STRIPE-CONNECT]
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

# Stripe API base URL
_STRIPE_API_BASE: str = "https://api.stripe.com"

# Default request timeout — every external call MUST have explicit timeout
# per tessl__graceful-degradation rule (Rule 1: every external call gets a timeout).
_DEFAULT_TIMEOUT_SECONDS: float = 10.0


# ── Result VO ─────────────────────────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class StripePaymentIntentResult:
    """Result of a successful Stripe Payment Intent creation.

    Attributes:
        payment_intent_id: Stripe ``pi_*`` identifier.
        client_secret: Client secret for frontend confirmation (Stripe.js).
        status: Stripe intent status (e.g., ``requires_payment_method``).
        idempotency_key: The idempotency key used.
        currency: ISO 4217 currency code (lower-cased per Stripe convention).
        amount_cents: Amount in minor units (e.g., 15000 = $150.00 USD).
    """

    payment_intent_id: str
    client_secret: str
    status: str
    idempotency_key: str
    currency: str
    amount_cents: int


# ── Adapter base class — verticals subclass + override hooks ──────────────────


@dataclass(slots=True)
class StripeConnectAdapter:
    """Generic Stripe Connect booking-deposit + subscription adapter.

    Subclass + override hooks for vertical-specific metadata (compliance_level,
    brand_slug, application_fee, etc.) without re-implementing HTTP plumbing.

    Args:
        secret_key: Stripe secret key (platform or per-tenant Connect account).
            Falls back to ``STRIPE_SECRET_KEY`` env var for dev/test only.
        connect_account_id: Stripe Connect account ID (``acct_*``). Used for
            Stripe-Account header on Connect-mode calls. Empty = platform call.
        webhook_secret: HMAC signing secret. Must be non-empty to verify webhooks.
            Falls back to ``STRIPE_WEBHOOK_SECRET`` env var for dev/test only.
        timeout_seconds: HTTP request timeout (default 10s).
            Per tessl__graceful-degradation Rule 1 — explicit timeout mandatory.
        api_base_url: Override Stripe API base URL (useful for test doubles).
    """

    secret_key: str = ""
    connect_account_id: str = ""
    webhook_secret: str = ""
    timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS
    api_base_url: str = _STRIPE_API_BASE

    def __post_init__(self) -> None:
        if not self.secret_key:
            self.secret_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not self.webhook_secret:
            self.webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")

    # ── Override hooks (subclasses customize per vertical) ─────────────────────

    def _compliance_metadata(self) -> dict[str, str]:
        """Per-vertical compliance metadata injected into Stripe metadata.

        Default: empty dict (generic flow). Vertical adapters override:
        - Vitalia: ``compliance_level=hipaa_lite, contains_phi=false, brand_slug=vitalia``
        - Comunify: ``compliance_level=creator_economy, brand_slug=comunify``
        """
        return {}

    def _application_fee_amount(
        self,
        *,
        amount_cents: int,
        **_kwargs: Any,
    ) -> int | None:
        """Per-vertical application fee amount in cents.

        Default: None (no application fee). Subclasses override for
        platform billing (e.g., comunify charges 5-10% per plan_tier).

        Args:
            amount_cents: Full charge amount in cents.

        Returns:
            Application fee in cents, or None to skip the field.
        """
        return None

    # ── Public API ─────────────────────────────────────────────────────────────

    async def create_payment_intent(
        self,
        *,
        amount: Decimal,
        currency: str,
        booking_id: UUID,
        deposit_or_full: str,
        description: str,
        customer_email: str | None = None,
        extra_kwargs: dict[str, Any] | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> StripePaymentIntentResult:
        """Create a Stripe Payment Intent for a booking or subscription payment.

        Injects compliance metadata on every call via ``_compliance_metadata()``.
        Uses ``str(booking_id)`` as idempotency key (prevents double-charges on retry).
        Currency is forwarded from caller — never hardcoded (currency-handling rule).

        Args:
            amount: Decimal amount (e.g., Decimal("150.00")).
            currency: ISO 4217 code (e.g., "USD", "ARS"). Forwarded as-is.
            booking_id: UUID used as Stripe idempotency key.
            deposit_or_full: "deposit" or "full" — stored in metadata for audit.
            description: Human-readable payment description.
            customer_email: Optional payer email for Stripe receipt.
            extra_kwargs: Optional additional Stripe API params (e.g., customer_id).
            client: Optional injected ``httpx.AsyncClient`` for testing.

        Returns:
            StripePaymentIntentResult with payment_intent_id, client_secret, status.

        Raises:
            httpx.HTTPStatusError: Stripe returned a non-2xx response.
            httpx.TimeoutException: Stripe did not respond within timeout_seconds.
        """
        amount_cents = int(amount * 100)
        idempotency_key = str(booking_id)

        compliance = self._compliance_metadata()

        payload: dict[str, Any] = {
            "amount": str(amount_cents),
            "currency": currency.lower(),
            "description": description,
            "metadata[booking_id]": str(booking_id),
            "metadata[deposit_or_full]": deposit_or_full,
        }

        for k, v in compliance.items():
            payload[f"metadata[{k}]"] = v

        if customer_email:
            payload["receipt_email"] = customer_email

        fee = self._application_fee_amount(amount_cents=amount_cents)
        if fee is not None:
            payload["application_fee_amount"] = str(fee)

        if extra_kwargs:
            payload.update(extra_kwargs)

        headers: dict[str, str] = {
            "Authorization": f"Bearer {self.secret_key}",
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

        if client is not None:
            resp = await client.post(url, data=payload, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as owned:
                resp = await owned.post(url, data=payload, headers=headers)

        resp.raise_for_status()
        data = resp.json()

        logger.info(
            "stripe_payment_intent_created",
            payment_intent_id=data["id"],
            booking_id=str(booking_id),
            status=data.get("status"),
        )

        return StripePaymentIntentResult(
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
        Steps:
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
            raise ValueError("webhook_secret is empty — set STRIPE_WEBHOOK_SECRET env var")

        parts: dict[str, str] = {}
        for part in stripe_signature.split(","):
            if "=" in part:
                k, _, v = part.partition("=")
                parts[k.strip()] = v.strip()

        timestamp_str = parts.get("t")
        signature_hex = parts.get("v1")

        if not timestamp_str or not signature_hex:
            raise ValueError("Invalid webhook signature header format — missing 't' or 'v1'")

        signed_payload = f"{timestamp_str}.".encode() + raw_body
        expected_sig = hmac.new(self.webhook_secret.encode(), signed_payload, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected_sig, signature_hex):
            raise ValueError("webhook signature mismatch — request body may have been tampered")

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
        connect_account_id: str = "",
        secret_key_env: str = "STRIPE_SECRET_KEY",
        webhook_secret_env: str = "STRIPE_WEBHOOK_SECRET",
    ) -> "StripeConnectAdapter":
        """Construct adapter from environment variables.

        Args:
            connect_account_id: Stripe Connect account ID (tenant-specific).
            secret_key_env: Env var name for the Stripe secret key.
            webhook_secret_env: Env var name for the webhook signing secret.

        Returns:
            Configured adapter instance.
        """
        return cls(
            secret_key=os.environ.get(secret_key_env, ""),
            connect_account_id=connect_account_id,
            webhook_secret=os.environ.get(webhook_secret_env, ""),
        )


__all__ = (
    "StripeConnectAdapter",
    "StripePaymentIntentResult",
)
