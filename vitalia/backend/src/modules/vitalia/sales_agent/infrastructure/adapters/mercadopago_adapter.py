# cap: sales_agent.adrian-3-tools-mvp
# story-origin: TBD
"""MercadoPago payment adapter for Vitalia Adrián sales_agent.

Creates payment preferences (deposit links) and validates webhook
HMAC signatures. Per tessl__graceful-degradation: 10s timeout + 1 retry
with 2s backoff.

Per 03-arch-be.md § 1 + 06-tickets.yaml T-be-services-2:
  - create_preference(appointment_id, amount, deposit_percent) → {init_point: URL}
  - validate_webhook_signature(payload, signature_header) → bool

HIPAA-lite: payment preference payloads MUST NOT contain PHI fields.
Guard: PaymentLinkService calls channel guard BEFORE this adapter.

downstream-regression-na: brand-local MercadoPago adapter for vitalia
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
from typing import Any

import structlog

logger = structlog.get_logger()

_TIMEOUT_SECONDS = 10
_RETRY_BACKOFF_SECONDS = 2
_MAX_RETRIES = 1


class MercadoPagoAdapter:
    """Async adapter for MercadoPago Preferences API.

    Creates payment links for appointment deposits. Validates inbound
    webhooks with HMAC-SHA256 signature check.

    Timeout: 10 seconds per request.
    Retry policy: 1 retry with 2s backoff on transient 5xx errors.
    """

    def __init__(
        self,
        access_token: str,
        webhook_secret: str,
        base_url: str = "https://api.mercadopago.com",
    ) -> None:
        """Initialize with MercadoPago credentials.

        Args:
            access_token: MP bearer token for API auth.
            webhook_secret: Shared secret for HMAC webhook signature validation.
            base_url: MP API base URL (overridable for testing).
        """
        self._access_token = access_token
        self._webhook_secret = webhook_secret
        self._base_url = base_url

    async def create_preference(
        self,
        appointment_id: str,
        amount: float,
        deposit_percent: int,
        currency: str = "ARS",
        back_urls: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Create a MercadoPago payment preference for an appointment deposit.

        Args:
            appointment_id: Vitalia appointment UUID (used as external_reference).
            amount: Total appointment amount in tenant currency.
            deposit_percent: Percentage to charge upfront (e.g. 30 = 30%).
            currency: ISO 4217 currency code (defaults to ARS — tenant overrides).
            back_urls: Optional dict with success/failure/pending URLs.

        Returns:
            dict with at minimum {'id': str, 'init_point': str} — the payment URL.

        Raises:
            RuntimeError: On transient MP API error after retries exhausted.
        """
        deposit_amount = round(amount * deposit_percent / 100, 2)

        payload: dict[str, Any] = {
            "items": [
                {
                    "title": "Depósito de reserva",
                    "quantity": 1,
                    "unit_price": deposit_amount,
                    "currency_id": currency,
                }
            ],
            "external_reference": appointment_id,
        }
        if back_urls:
            payload["back_urls"] = back_urls
            payload["auto_return"] = "approved"

        logger.info(
            "mercadopago.create_preference.start",
            appointment_id=appointment_id,
            deposit_percent=deposit_percent,
            currency=currency,
        )

        for attempt in range(_MAX_RETRIES + 1):
            try:
                result = await self._post_with_timeout(
                    path="/checkout/preferences",
                    payload=payload,
                )
                logger.info(
                    "mercadopago.create_preference.ok",
                    preference_id=result.get("id"),
                    appointment_id=appointment_id,
                )
                return result
            except asyncio.TimeoutError:
                logger.warning(
                    "mercadopago.create_preference.timeout",
                    attempt=attempt,
                    appointment_id=appointment_id,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(_RETRY_BACKOFF_SECONDS)
                else:
                    raise RuntimeError(
                        f"MercadoPago preference creation timed out after "
                        f"{_MAX_RETRIES + 1} attempts for appointment {appointment_id}"
                    )
            except Exception as exc:
                logger.error(
                    "mercadopago.create_preference.error",
                    error=str(exc),
                    appointment_id=appointment_id,
                )
                raise

        # Unreachable — loop above either returns or raises
        raise RuntimeError("MercadoPago create_preference: unexpected loop exit")

    def validate_webhook_signature(
        self,
        payload_bytes: bytes,
        signature_header: str,
        timestamp_header: str | None = None,
    ) -> bool:
        """Validate MercadoPago webhook HMAC-SHA256 signature.

        Vitalia requires webhook signature validation per hipaa-lite.md
        § Encryption in transit: "Webhooks de integraciones validados con
        HMAC signature + timestamp window 5min."

        Args:
            payload_bytes: Raw request body bytes.
            signature_header: Value of x-signature header from MP.
            timestamp_header: Optional x-request-id or ts= from signature header.

        Returns:
            True if signature is valid.

        Raises:
            ValueError: If signature is missing or does not match.
        """
        if not signature_header:
            raise ValueError("Missing MercadoPago x-signature header")

        # MP sends: ts=<timestamp>,v1=<hmac>
        parts = dict(part.split("=", 1) for part in signature_header.split(",") if "=" in part)
        received_sig = parts.get("v1", "")

        signed_template = f"id:{parts.get('id', '')};request-id:{parts.get('request-id', '')};ts:{parts.get('ts', '')};"
        expected = hmac.new(
            self._webhook_secret.encode(),
            signed_template.encode(),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected, received_sig):
            logger.warning(
                "mercadopago.webhook_signature_mismatch",
                received=received_sig[:8] + "...",
            )
            raise ValueError("MercadoPago webhook signature validation failed")

        return True

    async def _post_with_timeout(
        self,
        path: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute authenticated POST with timeout.

        Uses httpx.AsyncClient per project convention (not requests).
        Timeout set to _TIMEOUT_SECONDS.
        """
        import httpx  # noqa: PLC0415

        url = f"{self._base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
