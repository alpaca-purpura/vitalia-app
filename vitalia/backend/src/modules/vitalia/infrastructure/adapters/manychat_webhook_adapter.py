# cap: booking.prepaid-booking-advisory-locks
# story-origin: TBD
"""Vitalia ManyChat webhook adapter — IG DM inbound → sales_agent dispatch.

Per 03-arch-be.md § 6.8 + ticket T-be-8:
- Verifies ManyChat webhook HMAC-SHA256 via X-MC-Signature header.
- Idempotent: same (subscriber_id, message_id) → skip duplicate dispatch.
- Audit-logs every attempt (info on success, high on replay/HMAC failure).

HMAC algorithm:
  X-MC-Signature = HMAC-SHA256(raw_body, VITALIA_MANYCHAT_WEBHOOK_SECRET)
  The header value is the hex digest (lowercase).

Replay protection:
  - Timestamp tolerance ±5 min if ``timestamp`` field present in payload.
  - Dedup key: (subscriber_id, message_id) — caller tracks in audit_log.

# [VITALIA-D11-WEBHOOK-IDEMPOTENCY-MANYCHAT]
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger()

_TOLERANCE_SECONDS: int = 300  # ±5 min replay attack window


@dataclass(frozen=True, slots=True)
class ManychatInboundEvent:
    """Parsed + verified ManyChat inbound IG DM event.

    Attributes:
        subscriber_id: ManyChat subscriber ID (dedup key component).
        message_id: ManyChat message ID (dedup key component).
        message_text: Inbound message text content (may be empty for media).
        channel: Channel type (``instagram`` for IG DM).
        raw_data: Full parsed payload dict.
    """

    subscriber_id: str
    message_id: str
    message_text: str
    channel: str
    raw_data: dict[str, Any]


@dataclass(slots=True)
class ManychatWebhookAdapter:
    """Verifies ManyChat webhook HMAC-SHA256 signature (X-MC-Signature).

    ManyChat signs the raw request body with HMAC-SHA256 using the webhook
    secret. The signature is a hex-encoded digest (lowercase) delivered in
    the ``X-MC-Signature`` header.

    Args:
        webhook_secret: Secret from VITALIA_MANYCHAT_WEBHOOK_SECRET env var.
        tolerance_seconds: Max timestamp age in seconds (default 300s = ±5 min).
            Applied only when the payload contains a ``timestamp`` field.
    """

    webhook_secret: str
    tolerance_seconds: int = _TOLERANCE_SECONDS

    def verify(
        self,
        *,
        raw_body: bytes,
        mc_signature: str,
    ) -> ManychatInboundEvent:
        """Verify ManyChat HMAC signature and return parsed event.

        Args:
            raw_body: Raw HTTP request body bytes.
            mc_signature: Value of ``X-MC-Signature`` header (hex digest).

        Returns:
            Verified :class:`ManychatInboundEvent`.

        Raises:
            ValueError: HMAC mismatch, timestamp out of tolerance window, or
                empty webhook_secret.
        """
        if not self.webhook_secret:
            raise ValueError("webhook_secret is empty — set VITALIA_MANYCHAT_WEBHOOK_SECRET env var")

        # ── HMAC verification ────────────────────────────────────────────────
        expected_sig = hmac.new(
            self.webhook_secret.encode(),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_sig, mc_signature.lower()):
            raise ValueError("ManyChat webhook signature mismatch — HMAC verification failed")

        # ── Parse payload ────────────────────────────────────────────────────
        payload: dict[str, Any] = json.loads(raw_body)

        # Optional timestamp-based replay check
        ts_value = payload.get("timestamp")
        if ts_value is not None:
            try:
                event_ts = int(ts_value)
                age_seconds = abs(int(time.time()) - event_ts)
                if age_seconds > self.tolerance_seconds:
                    raise ValueError(
                        f"ManyChat webhook timestamp too old ({age_seconds}s > {self.tolerance_seconds}s tolerance)"
                    )
            except (TypeError, ValueError) as exc:
                # Re-raise only if it's our tolerance check, skip bad-ts silently for non-ts issue
                if "too old" in str(exc):
                    raise

        # ── Extract standard ManyChat IG DM fields ───────────────────────────
        # ManyChat payload structure for IG DM inbound varies by trigger type.
        # We extract the most common fields defensively.
        subscriber_id: str = str(payload.get("subscriber_id") or payload.get("id") or "")
        message_id: str = str(payload.get("message_id") or payload.get("mid") or "")
        message_text: str = str(payload.get("text") or payload.get("message", {}).get("text") or "")
        channel: str = str(payload.get("channel") or "instagram")

        if not subscriber_id:
            logger.warning("manychat_webhook_missing_subscriber_id", payload_keys=list(payload.keys()))

        logger.info(
            "manychat_webhook_verified",
            subscriber_id=subscriber_id,
            message_id=message_id,
            channel=channel,
        )

        return ManychatInboundEvent(
            subscriber_id=subscriber_id,
            message_id=message_id,
            message_text=message_text,
            channel=channel,
            raw_data=payload,
        )

    @classmethod
    def from_env(
        cls,
        *,
        webhook_secret_env: str = "VITALIA_MANYCHAT_WEBHOOK_SECRET",
    ) -> "ManychatWebhookAdapter":
        """Construct adapter from environment variables.

        Args:
            webhook_secret_env: Env var name for the ManyChat webhook secret.

        Returns:
            Configured :class:`ManychatWebhookAdapter` instance.
        """
        return cls(webhook_secret=os.environ.get(webhook_secret_env, ""))
