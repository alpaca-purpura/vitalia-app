# cap: payment.payment-gateways-latam-recurring
# story-origin: TBD
"""PrepaidPaymentService — gateway routing + payment intent creation.

Per 03-arch-be.md § 9.3:
  1. Get booking + offer (currency from booking, NOT hardcoded).
  2. Determine gateway per tenant country + BrandConfig preferred_gateway.
  3. Adapter dispatch (MercadoPagoAdapter / StripeConnectAdapter).
  4. Create payment_intent row idempotent.
  5. Emit PaymentInitiatedV1 event.

Gateway routing rules (03-arch-be.md § 11.2 + brand.yaml):
  - LatAm countries (AR, MX, BR, CL, CO, PE, UY) → mercadopago (primary)
  - US/EU countries → stripe_connect
  - BrandConfig.preferred_gateway overrides country default

D1: Receives session + repos via DI — no direct DB session construction.
D2: Idempotency — same idempotency_key (derived from booking_id) → returns existing intent.
currency-handling: currency from offer/booking DTO, NEVER hardcoded.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

import structlog
from pydantic import BaseModel, ConfigDict, Field

logger = structlog.get_logger()

# ── Gateway routing constants ─────────────────────────────────────────────────

# LatAm countries routed to MercadoPago per brand.yaml payment_gateways primary
_LATAM_COUNTRIES_MP = frozenset({"AR", "MX", "BR", "CL", "CO", "PE", "UY", "BO", "PY", "EC"})

_GATEWAY_MP = "mercadopago"
_GATEWAY_STRIPE = "stripe_connect"


def _utc_now() -> datetime:
    """Return current UTC datetime (timezone-aware)."""
    return datetime.now(tz=timezone.utc)


def _derive_idempotency_key(booking_id: uuid.UUID, deposit_or_full: str) -> str:
    """Derive stable idempotency key for a payment intent."""
    return f"vitalia:payment:{booking_id}:{deposit_or_full}"


def _select_gateway(
    tenant_country: str,
    preferred_gateway: str | None,
) -> str:
    """Select payment gateway based on tenant country + BrandConfig override.

    Priority:
    1. BrandConfig.preferred_gateway (if set and valid)
    2. Country default (LatAm → MP, US/EU → Stripe)

    Returns:
        Gateway string: 'mercadopago' | 'stripe_connect'
    """
    if preferred_gateway in (_GATEWAY_MP, _GATEWAY_STRIPE):
        return preferred_gateway

    if tenant_country.upper() in _LATAM_COUNTRIES_MP:
        return _GATEWAY_MP

    return _GATEWAY_STRIPE


# ── DTOs ──────────────────────────────────────────────────────────────────────


class GeneratePaymentLinkRequest(BaseModel):
    """Input DTO for payment link generation.

    Currency must be explicitly provided from the offer/booking context.
    NEVER default to 'USD' — caller resolves ISO 4217 currency per tenant locale.
    """

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    booking_id: uuid.UUID
    amount: Decimal = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3, description="ISO 4217 currency code")
    deposit_or_full: str = Field(pattern=r"^(deposit|full)$", default="deposit")
    patient_email: str | None = Field(default=None, max_length=255)
    offer_title: str = Field(min_length=1, max_length=255)
    back_url_success: str
    back_url_failure: str
    back_url_pending: str


class GeneratePaymentLinkResult(BaseModel):
    """Output DTO for payment link generation."""

    model_config = ConfigDict(from_attributes=True)

    payment_intent_id: uuid.UUID
    gateway: str  # 'mercadopago' | 'stripe_connect'
    checkout_url: str
    currency: str  # ISO 4217 — forwarded from request, never hardcoded
    amount: Decimal
    is_new: bool


# ── Minimal StripeConnectAdapter (vitalia-local until core lift in Story 11.bis) ─


@dataclass(slots=True)
class _StripeCheckoutResponse:
    """Result of Stripe Checkout Session creation."""

    session_id: str
    url: str


@dataclass(slots=True)
class StripeConnectAdapter:
    """Minimal Stripe Connect Checkout Session adapter for vitalia.

    Creates a Stripe Checkout Session for booking payment.
    Subclasses may override `_extra_metadata` for vertical-specific fields.

    Note: This adapter is vitalia-local until a core lift in Story 11.bis.
    No full implementation today — production Stripe calls deferred to T-be-7
    integration layer. This stub is sufficient for PrepaidPaymentService routing logic.

    Args:
        secret_key: Stripe secret key (per-tenant Connect account or platform).
        timeout_seconds: request timeout (graceful-degradation rule — every external call
            MUST have explicit timeout, default 10s).
        api_base_url: override for testing.
    """

    secret_key: str = ""
    timeout_seconds: float = 10.0
    api_base_url: str = "https://api.stripe.com"

    async def create_checkout_session(
        self,
        *,
        booking_id: uuid.UUID,
        amount_cents: int,
        currency: str,
        description: str,
        success_url: str,
        cancel_url: str,
        customer_email: str | None = None,
    ) -> _StripeCheckoutResponse:
        """Create a Stripe Checkout Session.

        Args:
            booking_id: used as idempotency key and metadata.
            amount_cents: amount in minor units (cents).
            currency: ISO 4217 lowercase (Stripe convention).
            description: item description.
            success_url: redirect after payment success.
            cancel_url: redirect after payment cancellation.
            customer_email: optional pre-fill for checkout form.

        Returns:
            _StripeCheckoutResponse with session_id and redirect URL.

        Raises:
            httpx.HTTPStatusError: Stripe returned non-2xx.
            httpx.TimeoutException: Stripe didn't respond within timeout_seconds.
        """
        import httpx

        payload = {
            "payment_method_types[]": "card",
            "mode": "payment",
            "line_items[0][price_data][currency]": currency.lower(),
            "line_items[0][price_data][unit_amount]": str(amount_cents),
            "line_items[0][price_data][product_data][name]": description,
            "line_items[0][quantity]": "1",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata[booking_id]": str(booking_id),
        }
        if customer_email:
            payload["customer_email"] = customer_email

        headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Idempotency-Key": str(booking_id),
        }

        url = f"{self.api_base_url}/v1/checkout/sessions"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            resp = await client.post(url, data=payload, headers=headers)

        resp.raise_for_status()
        data = resp.json()

        return _StripeCheckoutResponse(
            session_id=data["id"],
            url=data["url"],
        )


# ── Service ───────────────────────────────────────────────────────────────────


class PrepaidPaymentService:
    """Prepaid payment gateway routing + payment intent creation service.

    Usage (D1 — receive deps via DI, FastAPI Depends):
        svc = PrepaidPaymentService(
            session=db,
            payment_intent_repo=PaymentIntentRepository(session=db, tenant_id=tid),
            booking_repo=BookingRepository(session=db, tenant_id=tid),
            tenant_id=tid,
            tenant_country="AR",
            mp_access_token=tenant_connections.mercadopago_access_token,
            stripe_secret_key=tenant_connections.stripe_secret_key,
        )
        result = await svc.generate_payment_link(request=req)
    """

    def __init__(
        self,
        session: Any,  # AsyncSession
        payment_intent_repo: Any,  # PaymentIntentRepository
        booking_repo: Any,  # BookingRepository
        tenant_id: uuid.UUID,
        tenant_country: str,
        mp_access_token: str = "",
        stripe_secret_key: str = "",
        preferred_gateway: str | None = None,
    ) -> None:
        self._session = session
        self._payment_intent_repo = payment_intent_repo
        self._booking_repo = booking_repo
        self._tenant_id = tenant_id
        self._tenant_country = tenant_country
        self._mp_access_token = mp_access_token
        self._stripe_secret_key = stripe_secret_key
        self._preferred_gateway = preferred_gateway

    # ── Public API ────────────────────────────────────────────────────────────

    async def generate_payment_link(self, request: GeneratePaymentLinkRequest) -> GeneratePaymentLinkResult:
        """Generate a payment link routing to MercadoPago or Stripe Connect.

        D2 idempotency: same booking_id + deposit_or_full → returns existing
        payment_intent without calling the gateway API again.

        Currency is forwarded from request — NEVER hardcoded to USD or any
        other currency. Caller resolves ISO 4217 code from booking/offer context.

        Args:
            request: payment link generation request DTO.

        Returns:
            GeneratePaymentLinkResult with gateway, checkout_url, currency, is_new.
        """
        idempotency_key = _derive_idempotency_key(request.booking_id, request.deposit_or_full)

        # D2: check for existing payment intent (idempotency)
        existing = await self._payment_intent_repo.get_by_idempotency_key(idempotency_key)
        if existing is not None:
            checkout_url = existing.payment_metadata.get("checkout_url", "")
            logger.info(
                "payment_intent_idempotent",
                payment_intent_id=str(existing.id),
                tenant_id=str(self._tenant_id),
                gateway=existing.gateway,
            )
            return GeneratePaymentLinkResult(
                payment_intent_id=existing.id,
                gateway=existing.gateway,
                checkout_url=checkout_url,
                currency=existing.currency,
                amount=existing.amount,
                is_new=False,
            )

        # Select gateway
        gateway = _select_gateway(self._tenant_country, self._preferred_gateway)

        # Dispatch to appropriate adapter
        if gateway == _GATEWAY_MP:
            checkout_url, gateway_payment_id = await self._create_mp_preference(request)
        else:
            checkout_url, gateway_payment_id = await self._create_stripe_session(request)

        # Persist payment intent
        now = _utc_now()
        intent_id = uuid.uuid4()

        from src.modules.vitalia.infrastructure.models.payment_intent_model import (
            VitaliaPaymentIntentModel,
        )

        intent_model = VitaliaPaymentIntentModel(
            id=intent_id,
            tenant_id=self._tenant_id,
            booking_id=request.booking_id,
            gateway=gateway,
            gateway_payment_id=gateway_payment_id,
            amount=request.amount,
            currency=request.currency,
            status="initiated",
            payment_metadata={
                "checkout_url": checkout_url,
                "deposit_or_full": request.deposit_or_full,
                "offer_title": request.offer_title,
            },
            idempotency_key=idempotency_key,
            created_at=now,
            updated_at=now,
        )

        await self._payment_intent_repo.save(intent_model)

        logger.info(
            "payment_intent_created",
            payment_intent_id=str(intent_id),
            tenant_id=str(self._tenant_id),
            gateway=gateway,
            tenant_country=self._tenant_country,
            currency=request.currency,  # log currency, never hardcode
        )

        return GeneratePaymentLinkResult(
            payment_intent_id=intent_id,
            gateway=gateway,
            checkout_url=checkout_url,
            currency=request.currency,
            amount=request.amount,
            is_new=True,
        )

    # ── Internal gateway dispatchers ──────────────────────────────────────────

    async def _create_mp_preference(self, request: GeneratePaymentLinkRequest) -> tuple[str, str]:
        """Create MercadoPago checkout preference via MercadoPagoAdapter.

        Returns:
            Tuple of (checkout_url, preference_id).
        """
        from luana_core_channels.payment.mercadopago_adapter import (
            BackUrls,
            MercadoPagoAdapter,
            PayerInfo,
            PreferenceItem,
        )

        adapter = MercadoPagoAdapter(access_token=self._mp_access_token)

        # Convert decimal amount to cents (MP uses major units — adapter handles /100)
        amount_cents = int(request.amount * 100)

        resp = await adapter.create_preference(
            tenant_id=self._tenant_id,
            booking_id=request.booking_id,
            items=[
                PreferenceItem(
                    title=request.offer_title,
                    quantity=1,
                    unit_price_cents=amount_cents,
                    currency_id=request.currency,
                )
            ],
            payer=PayerInfo(email=request.patient_email),
            back_urls=BackUrls(
                success=request.back_url_success,
                failure=request.back_url_failure,
                pending=request.back_url_pending,
            ),
            deposit_or_full=request.deposit_or_full,
        )

        return resp.init_point, resp.preference_id

    async def _create_stripe_session(self, request: GeneratePaymentLinkRequest) -> tuple[str, str]:
        """Create Stripe Checkout Session via StripeConnectAdapter.

        Returns:
            Tuple of (checkout_url, session_id).
        """
        adapter = StripeConnectAdapter(secret_key=self._stripe_secret_key)

        amount_cents = int(request.amount * 100)

        resp = await adapter.create_checkout_session(
            booking_id=request.booking_id,
            amount_cents=amount_cents,
            currency=request.currency.lower(),
            description=request.offer_title,
            success_url=request.back_url_success,
            cancel_url=request.back_url_failure,
            customer_email=request.patient_email,
        )

        return resp.url, resp.session_id
