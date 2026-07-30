"""MercadoPago Checkout Preferences adapter — booking-deposit channel.

Generic base lifted to @luana/core/channels per Story 11 D4 (anti-duplication.md).
Verticals subclass via composition + override hooks (`_extra_metadata`,
`_status_overrides`) — they do NOT re-implement HTTP plumbing.

Coverage: AR (primary), MX, BR, CL, CO, PE, UY (per Story 11 03-arch-be.md § 11.2).

Distinct from `luana-core-sales-agent.application.tools.payment.providers.MercadoPagoPaymentProvider`:
the sales-agent provider returns a checkout link inside a sales chat (closer flow);
this adapter handles booking-deposit creation with idempotency + HMAC + compliance metadata.

# [VITALIA-D4-LIFT-SHARED-MERCADOPAGO]
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

import httpx
import structlog

if TYPE_CHECKING:
    from collections.abc import Mapping
    from uuid import UUID

logger = structlog.get_logger()


# ─────────────────────────────────────────────────────────────
# Domain VOs (provider-agnostic where possible)
# ─────────────────────────────────────────────────────────────


class PaymentStatusEnum(StrEnum):
    """Canonical payment status values — provider-agnostic."""

    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class PreferenceItem:
    """Single line item inside a MP checkout preference."""

    title: str
    quantity: int
    unit_price_cents: int
    currency_id: str  # ISO 4217 (ARS / MXN / BRL / CLP / COP / PEN / UYU)
    description: str | None = None


@dataclass(frozen=True, slots=True)
class PayerInfo:
    """Payer data — masked PII at adapter boundary (caller must sanitize)."""

    email: str | None = None
    name: str | None = None
    surname: str | None = None
    phone: str | None = None  # E.164 format expected


@dataclass(frozen=True, slots=True)
class BackUrls:
    """Redirect URLs after MP checkout completion."""

    success: str
    failure: str
    pending: str


@dataclass(frozen=True, slots=True)
class MpPreferenceResponse:
    """Result of MP `POST /checkout/preferences`."""

    preference_id: str
    init_point: str  # production checkout URL
    sandbox_init_point: str | None = None
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class PaymentLinkOutput:
    """Provider-agnostic payment link result (back-compat with sales-agent provider shape)."""

    external_id: str
    url: str
    provider_id: str = "mercadopago"
    amount_cents: int | None = None
    currency: str | None = None
    expires_at: Any | None = None
    metadata: Mapping[str, Any] | None = None


# ─────────────────────────────────────────────────────────────
# Adapter base class — verticals subclass + override hooks
# ─────────────────────────────────────────────────────────────


@dataclass(slots=True)
class MercadoPagoAdapter:
    """MercadoPago Checkout Preferences adapter.

    Subclass + override hooks for vertical-specific metadata (compliance_level,
    brand_slug, contains_phi flag) without re-implementing HTTP plumbing.

    Args:
        access_token: per-tenant MP access token (caller supplies via tenant
            connections config; falls back to ``MERCADOPAGO_ACCESS_TOKEN`` env
            for dev/test only).
        webhook_secret: per-tenant HMAC secret for IPN signature verification.
        timeout_seconds: request timeout (graceful-degradation rule — every
            external call MUST have explicit timeout, default 10s).
        api_base_url: override for sandbox / regional endpoints (default prod).
    """

    provider_id: str = "mercadopago"
    access_token: str = ""
    webhook_secret: str = ""
    timeout_seconds: float = 10.0
    api_base_url: str = "https://api.mercadopago.com"

    def __post_init__(self) -> None:
        if not self.access_token:
            # Dev/test fallback — production callers MUST pass per-tenant token.
            self.access_token = os.environ.get("MERCADOPAGO_ACCESS_TOKEN", "")

    # ── Override hooks (subclasses customize per vertical) ─────────────

    def _extra_metadata(
        self,
        *,
        tenant_id: UUID,
        booking_id: UUID | None,
        deposit_or_full: str,
    ) -> dict[str, Any]:
        """Per-vertical metadata injected into MP preference.

        Default: empty dict (sales-agent generic flow). Vertical adapters
        override — e.g., vitalia sets ``compliance_level=hipaa_lite``,
        ``contains_phi=False``, ``brand_slug=vitalia``.
        """
        return {}

    def _status_overrides(self) -> dict[str, PaymentStatusEnum]:
        """Per-vertical MP status code overrides.

        Default: empty dict (canonical mapping wins). Subclasses MAY override
        for partial-refund vertical-specific accounting.
        """
        return {}

    # ── Public API (Story 11 03-arch-be.md § 11.2 signature) ───────────

    async def create_preference(
        self,
        *,
        tenant_id: UUID,
        booking_id: UUID,
        items: list[PreferenceItem],
        payer: PayerInfo,
        back_urls: BackUrls,
        deposit_or_full: str = "deposit",
        client: httpx.AsyncClient | None = None,
    ) -> MpPreferenceResponse:
        """Create MP checkout preference for booking deposit.

        Idempotency: ``X-Idempotency-Key=booking_id`` header (per arch-be § 11.1
        cross-applies). MP de-duplicates concurrent retries with same key.

        Returns parsed ``MpPreferenceResponse`` with ``init_point`` (URL to
        redirect payer to MP checkout).

        Args:
            client: optional injected ``httpx.AsyncClient`` for testing
                (``httpx.MockTransport``). Production callers omit — adapter
                creates a fresh client per call with explicit ``timeout_seconds``.

        Raises:
            httpx.HTTPStatusError: MP returned non-2xx (caller decides retry policy).
            httpx.TimeoutException: MP didn't respond within ``timeout_seconds``.
        """
        metadata = {
            "tenant_id": str(tenant_id),
            "booking_id": str(booking_id),
            "deposit_or_full": deposit_or_full,
            **self._extra_metadata(
                tenant_id=tenant_id,
                booking_id=booking_id,
                deposit_or_full=deposit_or_full,
            ),
        }

        payload: dict[str, Any] = {
            "items": [
                {
                    "title": item.title,
                    "quantity": item.quantity,
                    # MP unit_price is float major-units (e.g., 1500.0 ARS), NOT cents.
                    "unit_price": item.unit_price_cents / 100,
                    "currency_id": item.currency_id,
                    **({"description": item.description} if item.description else {}),
                }
                for item in items
            ],
            "external_reference": f"{tenant_id}:{booking_id}",
            "metadata": metadata,
            "back_urls": {
                "success": back_urls.success,
                "failure": back_urls.failure,
                "pending": back_urls.pending,
            },
            "auto_return": "approved",
        }

        if any(
            (
                payer.email,
                payer.name,
                payer.surname,
                payer.phone,
            )
        ):
            payer_block: dict[str, Any] = {}
            if payer.email:
                payer_block["email"] = payer.email
            if payer.name:
                payer_block["name"] = payer.name
            if payer.surname:
                payer_block["surname"] = payer.surname
            if payer.phone:
                payer_block["phone"] = {"number": payer.phone}
            payload["payer"] = payer_block

        url = f"{self.api_base_url}/checkout/preferences"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "X-Idempotency-Key": str(booking_id),
            "Content-Type": "application/json",
        }

        if client is not None:
            resp = await client.post(url, json=payload, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as owned:
                resp = await owned.post(url, json=payload, headers=headers)

        resp.raise_for_status()
        data = resp.json()

        return MpPreferenceResponse(
            preference_id=data["id"],
            init_point=data["init_point"],
            sandbox_init_point=data.get("sandbox_init_point"),
            metadata=metadata,
        )

    async def verify_payment(
        self,
        payment_id: str,
        *,
        client: httpx.AsyncClient | None = None,
    ) -> PaymentStatusEnum:
        """Query MP `GET /v1/payments/{id}` for authoritative status.

        MP IPN webhooks contain only the payment ``id`` — a second API call is
        always required for the actual status (per MP API contract).

        Args:
            client: optional injected ``httpx.AsyncClient`` for testing.
        """
        url = f"{self.api_base_url}/v1/payments/{payment_id}"
        headers = {"Authorization": f"Bearer {self.access_token}"}

        if client is not None:
            resp = await client.get(url, headers=headers)
        else:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as owned:
                resp = await owned.get(url, headers=headers)

        resp.raise_for_status()
        data = resp.json()
        return self._map_mp_status(data.get("status", ""))

    def _map_mp_status(self, mp_status: str) -> PaymentStatusEnum:
        """Map MP status string to canonical PaymentStatusEnum."""
        canonical = {
            "approved": PaymentStatusEnum.PAID,
            "pending": PaymentStatusEnum.PENDING,
            "in_process": PaymentStatusEnum.PENDING,
            "rejected": PaymentStatusEnum.FAILED,
            "cancelled": PaymentStatusEnum.CANCELLED,
            "refunded": PaymentStatusEnum.REFUNDED,
            "charged_back": PaymentStatusEnum.REFUNDED,
        }
        overrides = self._status_overrides()
        merged = {**canonical, **overrides}
        return merged.get(mp_status, PaymentStatusEnum.PENDING)

    def verify_webhook_signature(
        self,
        *,
        payload_body: bytes,
        signature_header: str,
        request_id: str | None = None,
    ) -> bool:
        """HMAC-SHA256 signature verification for MP IPN webhook.

        Per MP webhook docs — signature header format:
        ``ts=<timestamp>,v1=<hmac-sha256-hex>`` (header name `x-signature`).

        Returns True iff computed HMAC matches the signed manifest. Returns
        False on malformed header / missing secret / mismatch (caller MUST
        reject webhook on False — anti-replay attack).

        Args:
            payload_body: raw request body bytes (NOT json-decoded).
            signature_header: value of ``x-signature`` header.
            request_id: optional ``x-request-id`` header (MP includes in
                signed manifest when present).
        """
        if not self.webhook_secret:
            logger.warning("mp_webhook_secret_missing", provider=self.provider_id)
            return False

        try:
            parts = dict(p.split("=", 1) for p in signature_header.split(",") if "=" in p)
        except ValueError:
            logger.warning("mp_webhook_signature_malformed", header=signature_header)
            return False

        ts = parts.get("ts", "")
        signature_v1 = parts.get("v1", "")
        if not ts or not signature_v1:
            logger.warning("mp_webhook_signature_incomplete", parts=list(parts.keys()))
            return False

        # MP signed manifest: id:<request_id>;request-id:<request_id>;ts:<ts>;
        # When request_id absent, manifest is just ts + body.
        manifest_parts = []
        if request_id:
            manifest_parts.append(f"id:{request_id}")
            manifest_parts.append(f"request-id:{request_id}")
        manifest_parts.append(f"ts:{ts}")
        manifest = ";".join(manifest_parts) + ";"
        digest_input = manifest.encode("utf-8") + payload_body

        computed = hmac.new(
            self.webhook_secret.encode("utf-8"),
            digest_input,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed, signature_v1)


# ─────────────────────────────────────────────────────────────
# Sync wrappers (back-compat shim for sync-callers)
# ─────────────────────────────────────────────────────────────
# Kept distinct from sales-agent provider sync impl to avoid coupling.


def create_payment_link_sync(
    adapter: MercadoPagoAdapter,
    *,
    tenant_id: UUID,
    booking_id: UUID,
    items: list[PreferenceItem],
    payer: PayerInfo,
    back_urls: BackUrls,
    deposit_or_full: str = "deposit",
) -> PaymentLinkOutput:
    """Sync-friendly wrapper around `create_preference` for legacy callers.

    Production-only convenience — tests inject mock client via
    ``adapter.create_preference(..., client=httpx.AsyncClient(transport=MockTransport(...)))``.
    """
    response = asyncio.run(
        adapter.create_preference(
            tenant_id=tenant_id,
            booking_id=booking_id,
            items=items,
            payer=payer,
            back_urls=back_urls,
            deposit_or_full=deposit_or_full,
        )
    )
    total_cents = sum(item.unit_price_cents * item.quantity for item in items)
    currency = items[0].currency_id if items else None
    return PaymentLinkOutput(
        external_id=response.preference_id,
        url=response.init_point,
        provider_id=adapter.provider_id,
        amount_cents=total_cents,
        currency=currency,
        metadata=dict(response.metadata) if response.metadata else None,
    )


__all__ = (
    "BackUrls",
    "MercadoPagoAdapter",
    "MpPreferenceResponse",
    "PayerInfo",
    "PaymentLinkOutput",
    "PaymentStatusEnum",
    "PreferenceItem",
    "create_payment_link_sync",
)


# Silence unused-import warning for `field` (kept for future per-vertical
# subclass needs without API churn).
_ = field
