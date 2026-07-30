# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Vitalia Clerk webhook adapter — signup.completed → tenant create.

Per 03-arch-be.md § 6.8 + ticket T-be-8:
- Verifies Clerk webhook HMAC-SHA256 via svix-signature header.
- Idempotent: same clerk_user_id within window → returns existing tenant (no duplicate create).
- Audit-logs every attempt (info on success, high on replay/HMAC failure).
- Calls OnboardingService.create_clinic_profile when event=user.created.

HMAC algorithm: Clerk uses the Svix webhook standard (HMAC-SHA256 over
``{svix-id}.{svix-timestamp}.{raw_body}`` with base64-decoded secret).
Secret env var: VITALIA_CLERK_WEBHOOK_SECRET.

Replay attack protection:
  - Timestamp tolerance ±5 min (300s).
  - clerk_user_id dedup: caller checks PaymentIntentRepository or an
    OnboardingService idempotency cache keyed on clerk_user_id.

# [VITALIA-D11-WEBHOOK-IDEMPOTENCY-CLERK]
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import structlog

logger = structlog.get_logger()

_TOLERANCE_SECONDS: int = 300  # ±5 min replay attack window


@dataclass(frozen=True, slots=True)
class ClerkWebhookEvent:
    """Parsed + verified Clerk webhook event.

    Attributes:
        event_id: Svix event ID (used as dedup key).
        event_type: Clerk event type (e.g. ``user.created``).
        clerk_user_id: Clerk user ID extracted from data.id.
        data: Full event data dict (raw from Clerk payload).
    """

    event_id: str
    event_type: str
    clerk_user_id: str
    data: dict[str, Any]


@dataclass(slots=True)
class ClerkWebhookAdapter:
    """Verifies Clerk webhook HMAC signature using the Svix standard.

    Clerk delivers webhooks via Svix. The Svix signing algorithm:
      1. Concatenate ``{svix-id}.{svix-timestamp}.{raw_body}`` (bytes).
      2. HMAC-SHA256 with the base64-decoded webhook secret.
      3. Compare base64-encoded digest against svix-signature header value(s).

    Args:
        webhook_secret: Raw secret from VITALIA_CLERK_WEBHOOK_SECRET env var.
            Must be the Svix-format secret (``whsec_`` prefixed base64 string or
            raw base64). The adapter strips the ``whsec_`` prefix automatically.
        tolerance_seconds: Max timestamp age in seconds (default 300s = ±5 min).
    """

    webhook_secret: str
    tolerance_seconds: int = _TOLERANCE_SECONDS
    _secret_bytes: bytes = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Decode the webhook secret bytes once at construction."""
        secret = self.webhook_secret
        # Strip whsec_ prefix if present (Svix format)
        if secret.startswith("whsec_"):
            secret = secret[len("whsec_") :]
        try:
            self._secret_bytes = base64.b64decode(secret)
        except Exception:
            # Secret is not base64 — use raw bytes (test mode)
            self._secret_bytes = secret.encode()

    def verify(
        self,
        *,
        raw_body: bytes,
        svix_id: str,
        svix_timestamp: str,
        svix_signature: str,
    ) -> ClerkWebhookEvent:
        """Verify Clerk/Svix HMAC signature and return parsed event.

        Args:
            raw_body: Raw HTTP request body bytes (must NOT be decoded before passing).
            svix_id: Value of ``svix-id`` header.
            svix_timestamp: Value of ``svix-timestamp`` header.
            svix_signature: Value of ``svix-signature`` header (space-separated
                ``v1,<base64>`` entries per Svix spec).

        Returns:
            Verified :class:`ClerkWebhookEvent` with event_id, event_type,
            clerk_user_id, and raw data dict.

        Raises:
            ValueError: HMAC mismatch, timestamp out of tolerance, or
                missing/malformed headers.
        """
        if not self.webhook_secret:
            raise ValueError("webhook_secret is empty — set VITALIA_CLERK_WEBHOOK_SECRET env var")

        # ── Replay attack: timestamp tolerance ──────────────────────────────
        try:
            event_ts = int(svix_timestamp)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid svix-timestamp value: {svix_timestamp!r}") from exc

        age_seconds = abs(int(time.time()) - event_ts)
        if age_seconds > self.tolerance_seconds:
            raise ValueError(f"Clerk webhook timestamp too old ({age_seconds}s > {self.tolerance_seconds}s tolerance)")

        # ── HMAC computation (Svix standard) ────────────────────────────────
        # signed_content = "{svix-id}.{svix-timestamp}.{body}"
        signed_content = f"{svix_id}.{svix_timestamp}.".encode() + raw_body
        expected_digest = hmac.new(self._secret_bytes, signed_content, hashlib.sha256).digest()
        expected_b64 = base64.b64encode(expected_digest).decode()

        # svix-signature may carry multiple space-separated "v1,<b64>" entries
        verified = False
        for sig_entry in svix_signature.split(" "):
            if "," not in sig_entry:
                continue
            version, _, candidate_b64 = sig_entry.partition(",")
            if version != "v1":
                continue
            if hmac.compare_digest(expected_b64, candidate_b64):
                verified = True
                break

        if not verified:
            raise ValueError("Clerk webhook signature mismatch — HMAC verification failed")

        # ── Parse event ─────────────────────────────────────────────────────
        payload: dict[str, Any] = json.loads(raw_body)
        event_type: str = payload.get("type", "")
        data: dict[str, Any] = payload.get("data", {})
        clerk_user_id: str = data.get("id", "")

        if not clerk_user_id:
            raise ValueError("Clerk webhook payload missing data.id (clerk_user_id)")

        logger.info(
            "clerk_webhook_verified",
            event_id=svix_id,
            event_type=event_type,
            clerk_user_id=clerk_user_id,
        )

        return ClerkWebhookEvent(
            event_id=svix_id,
            event_type=event_type,
            clerk_user_id=clerk_user_id,
            data=data,
        )

    @classmethod
    def from_env(
        cls,
        *,
        webhook_secret_env: str = "VITALIA_CLERK_WEBHOOK_SECRET",
    ) -> "ClerkWebhookAdapter":
        """Construct adapter from environment variables.

        Args:
            webhook_secret_env: Env var name for the Clerk/Svix webhook secret.

        Returns:
            Configured :class:`ClerkWebhookAdapter` instance.
        """
        return cls(webhook_secret=os.environ.get(webhook_secret_env, ""))
