"""Unit tests — PrepaidPaymentService (T-be-6 A3).

TDD RED → GREEN. All tests use mocked repositories and adapters (no Postgres, no HTTP).

Acceptance criteria (T-be-6):
  A3: PrepaidPaymentService routes MercadoPago for AR tenants + Stripe for US tenants
      (test_gateway_routing)

Decision coverage:
  D1: DDD inside-out — services receive repos via DI, no direct DB access.
  D2: Idempotency — same idempotency_key → returns existing payment_intent.
  currency-handling: currency from offer/booking, NOT hardcoded.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.vitalia.application.services.prepaid_payment_service import (
    GeneratePaymentLinkRequest,
    GeneratePaymentLinkResult,
    PrepaidPaymentService,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def booking_id() -> uuid.UUID:
    return uuid.UUID("33333333-0000-0000-0000-000000000003")


@pytest.fixture()
def mock_payment_intent_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_by_idempotency_key = AsyncMock(return_value=None)  # no existing by default
    repo.save = AsyncMock()
    return repo


@pytest.fixture()
def mock_booking_repo() -> MagicMock:
    repo = MagicMock()
    return repo


@pytest.fixture()
def mock_session() -> MagicMock:
    session = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    return session


def _make_service(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_payment_intent_repo: MagicMock,
    mock_booking_repo: MagicMock,
    *,
    tenant_country: str = "AR",
    mp_access_token: str = "test-mp-token",
    stripe_secret_key: str = "sk_test_stripe",
    preferred_gateway: str | None = None,
) -> PrepaidPaymentService:
    return PrepaidPaymentService(
        session=mock_session,
        payment_intent_repo=mock_payment_intent_repo,
        booking_repo=mock_booking_repo,
        tenant_id=tenant_id,
        tenant_country=tenant_country,
        mp_access_token=mp_access_token,
        stripe_secret_key=stripe_secret_key,
        preferred_gateway=preferred_gateway,
    )


# ── A3: Gateway routing ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_gateway_routing(
    mock_session: MagicMock,
    mock_payment_intent_repo: MagicMock,
    mock_booking_repo: MagicMock,
    booking_id: uuid.UUID,
) -> None:
    """A3: MP for AR tenants, Stripe for US tenants.

    PrepaidPaymentService.generate_payment_link() must select gateway based on tenant_country.
    - AR → 'mercadopago'
    - US → 'stripe_connect'
    """
    # AR tenant → MercadoPago
    tenant_ar = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    svc_ar = _make_service(
        tenant_ar,
        mock_session,
        mock_payment_intent_repo,
        mock_booking_repo,
        tenant_country="AR",
    )

    request_ar = GeneratePaymentLinkRequest(
        booking_id=booking_id,
        amount=Decimal("15000.00"),
        currency="ARS",
        deposit_or_full="deposit",
        patient_email="paciente@example.com",
        offer_title="Implante Dental",
        back_url_success="https://vitalia.app/booking/success",
        back_url_failure="https://vitalia.app/booking/failure",
        back_url_pending="https://vitalia.app/booking/pending",
    )

    # Mock the MP adapter create_preference call inside service
    with _patch_mp_adapter(), _patch_stripe_adapter():
        result_ar = await svc_ar.generate_payment_link(request=request_ar)

    assert result_ar.gateway == "mercadopago", f"AR must route to mercadopago, got {result_ar.gateway}"
    assert "mp.com/checkout" in result_ar.checkout_url, "MP URL must be in checkout_url"

    # US tenant → Stripe
    tenant_us = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002")
    mock_payment_intent_repo.get_by_idempotency_key = AsyncMock(return_value=None)
    svc_us = _make_service(
        tenant_us,
        mock_session,
        mock_payment_intent_repo,
        mock_booking_repo,
        tenant_country="US",
    )

    request_us = GeneratePaymentLinkRequest(
        booking_id=booking_id,
        amount=Decimal("500.00"),
        currency="USD",
        deposit_or_full="deposit",
        patient_email="patient@example.com",
        offer_title="Dental Implant",
        back_url_success="https://vitalia.app/booking/success",
        back_url_failure="https://vitalia.app/booking/failure",
        back_url_pending="https://vitalia.app/booking/pending",
    )

    with _patch_mp_adapter(), _patch_stripe_adapter():
        result_us = await svc_us.generate_payment_link(request=request_us)

    assert result_us.gateway == "stripe_connect", f"US must route to stripe_connect, got {result_us.gateway}"
    assert "stripe.com" in result_us.checkout_url, "Stripe URL must be in checkout_url"


@pytest.mark.asyncio
async def test_gateway_routing_cl_uses_mercadopago(
    mock_session: MagicMock,
    mock_payment_intent_repo: MagicMock,
    mock_booking_repo: MagicMock,
    booking_id: uuid.UUID,
) -> None:
    """CL (Chile) tenants must route to MercadoPago (LatAm primary gateway)."""
    tenant_cl = uuid.UUID("cccccccc-0000-0000-0000-000000000003")
    svc = _make_service(
        tenant_cl,
        mock_session,
        mock_payment_intent_repo,
        mock_booking_repo,
        tenant_country="CL",
    )

    request = GeneratePaymentLinkRequest(
        booking_id=booking_id,
        amount=Decimal("50000.00"),
        currency="CLP",
        deposit_or_full="deposit",
        patient_email="paciente@cl.example.com",
        offer_title="Consulta Psicología",
        back_url_success="https://vitalia.app/ok",
        back_url_failure="https://vitalia.app/fail",
        back_url_pending="https://vitalia.app/pending",
    )

    with _patch_mp_adapter(), _patch_stripe_adapter():
        result = await svc.generate_payment_link(request=request)

    assert result.gateway == "mercadopago", f"CL must route to mercadopago, got {result.gateway}"
    assert "mp.com/checkout" in result.checkout_url


@pytest.mark.asyncio
async def test_gateway_routing_preferred_gateway_overrides(
    mock_session: MagicMock,
    mock_payment_intent_repo: MagicMock,
    mock_booking_repo: MagicMock,
    booking_id: uuid.UUID,
) -> None:
    """BrandConfig preferred_gateway must override country default."""
    tenant_ar = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    # AR normally → MP; BrandConfig override → stripe
    svc = _make_service(
        tenant_ar,
        mock_session,
        mock_payment_intent_repo,
        mock_booking_repo,
        tenant_country="AR",
        preferred_gateway="stripe_connect",
    )

    request = GeneratePaymentLinkRequest(
        booking_id=booking_id,
        amount=Decimal("20000.00"),
        currency="ARS",
        deposit_or_full="full",
        patient_email="test@test.com",
        offer_title="Consulta",
        back_url_success="https://vitalia.app/ok",
        back_url_failure="https://vitalia.app/fail",
        back_url_pending="https://vitalia.app/pending",
    )

    with _patch_mp_adapter(), _patch_stripe_adapter():
        result = await svc.generate_payment_link(request=request)

    assert result.gateway == "stripe_connect", (
        f"Preferred gateway 'stripe_connect' must override AR default mercadopago, got {result.gateway}"
    )
    assert "stripe.com" in result.checkout_url


# ── Currency forwarding (no hardcode) ────────────────────────────────────────


@pytest.mark.asyncio
async def test_currency_from_request_not_hardcoded(
    mock_session: MagicMock,
    mock_payment_intent_repo: MagicMock,
    mock_booking_repo: MagicMock,
    booking_id: uuid.UUID,
) -> None:
    """Currency must be forwarded from request, never hardcoded to USD/ARS/etc."""
    tenant_mx = uuid.UUID("dddddddd-0000-0000-0000-000000000004")
    svc = _make_service(
        tenant_mx,
        mock_session,
        mock_payment_intent_repo,
        mock_booking_repo,
        tenant_country="MX",
    )

    request = GeneratePaymentLinkRequest(
        booking_id=booking_id,
        amount=Decimal("3500.00"),
        currency="MXN",  # ← must be forwarded as-is
        deposit_or_full="deposit",
        patient_email="test@mx.example.com",
        offer_title="Sesión Psicología",
        back_url_success="https://vitalia.app/ok",
        back_url_failure="https://vitalia.app/fail",
        back_url_pending="https://vitalia.app/pending",
    )

    with _patch_mp_adapter(), _patch_stripe_adapter():
        result = await svc.generate_payment_link(request=request)

    assert result.currency == "MXN", f"Currency must be MXN from request, got {result.currency}"


# ── D2: Idempotency ──────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_generate_payment_link_idempotent(
    mock_session: MagicMock,
    mock_payment_intent_repo: MagicMock,
    mock_booking_repo: MagicMock,
    booking_id: uuid.UUID,
) -> None:
    """D2: Same idempotency_key → returns existing payment intent (no new gateway call)."""
    tenant_ar = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
    existing_intent = MagicMock()
    existing_intent.id = uuid.uuid4()
    existing_intent.gateway = "mercadopago"
    existing_intent.status = "initiated"
    existing_intent.payment_metadata = {
        "checkout_url": "https://mp.com/checkout/existing",
        "preference_id": "pref-existing-123",
    }
    existing_intent.amount = Decimal("15000.00")
    existing_intent.currency = "ARS"

    mock_payment_intent_repo.get_by_idempotency_key = AsyncMock(return_value=existing_intent)

    svc = _make_service(
        tenant_ar,
        mock_session,
        mock_payment_intent_repo,
        mock_booking_repo,
        tenant_country="AR",
    )

    request = GeneratePaymentLinkRequest(
        booking_id=booking_id,
        amount=Decimal("15000.00"),
        currency="ARS",
        deposit_or_full="deposit",
        patient_email="test@test.com",
        offer_title="Implante",
        back_url_success="https://vitalia.app/ok",
        back_url_failure="https://vitalia.app/fail",
        back_url_pending="https://vitalia.app/pending",
    )

    with _patch_mp_adapter(), _patch_stripe_adapter():
        result = await svc.generate_payment_link(request=request)

    assert result.is_new is False, "Idempotent hit must return is_new=False"
    assert result.checkout_url == "https://mp.com/checkout/existing"
    mock_payment_intent_repo.save.assert_not_called()


# ── D1: DI constructor ───────────────────────────────────────────────────────


def test_prepaid_payment_service_constructor_requires_di() -> None:
    """D1: PrepaidPaymentService must accept repos via DI."""
    import inspect

    sig = inspect.signature(PrepaidPaymentService.__init__)
    params = list(sig.parameters.keys())
    assert "session" in params
    assert "payment_intent_repo" in params
    assert "booking_repo" in params
    assert "tenant_id" in params
    assert "tenant_country" in params


def test_generate_payment_link_result_pydantic() -> None:
    """GeneratePaymentLinkResult must be Pydantic v2 model."""
    result = GeneratePaymentLinkResult(
        payment_intent_id=uuid.uuid4(),
        gateway="mercadopago",
        checkout_url="https://mp.com/checkout/abc",
        currency="ARS",
        amount=Decimal("15000.00"),
        is_new=True,
    )
    assert result.gateway == "mercadopago"
    assert result.currency == "ARS"  # not hardcoded


def test_generate_payment_link_request_forbids_hardcoded_usd() -> None:
    """GeneratePaymentLinkRequest must NOT have a default currency (forces caller to pass it)."""
    import inspect

    sig = inspect.signature(GeneratePaymentLinkRequest.__init__)
    params = sig.parameters

    # If 'currency' is a required field, it has no default → no hardcoded USD
    # Pydantic v2 required fields show PydanticUndefined as default
    # We can't easily detect PydanticUndefined here; instead verify that
    # a request without currency raises ValidationError
    _ = params.get("currency")  # confirm field exists in signature
    from pydantic import ValidationError

    with pytest.raises((ValidationError, TypeError)):
        GeneratePaymentLinkRequest(
            booking_id=uuid.uuid4(),
            amount=Decimal("100.00"),
            # omit currency — must fail
            deposit_or_full="deposit",
            patient_email="test@test.com",
            offer_title="Test",
            back_url_success="https://a.com/ok",
            back_url_failure="https://a.com/fail",
            back_url_pending="https://a.com/pend",
        )


# ── Internal patch helpers ────────────────────────────────────────────────────


def _patch_mp_adapter():
    """Patch PrepaidPaymentService._create_mp_preference (avoids luana_core_channels import chain)."""
    from unittest.mock import patch

    async def _fake_create_mp(self, request):  # noqa: ANN001
        return ("https://mp.com/checkout/pref-test-123", "pref-test-123")

    return patch(
        "src.modules.vitalia.application.services.prepaid_payment_service.PrepaidPaymentService._create_mp_preference",
        new=_fake_create_mp,
    )


def _patch_stripe_adapter():
    """Patch PrepaidPaymentService._create_stripe_session (avoids httpx call in unit tests)."""
    from unittest.mock import patch

    async def _fake_create_stripe(self, request):  # noqa: ANN001
        return ("https://checkout.stripe.com/pay/cs_test_stripe_session_123", "cs_test_stripe_session_123")

    return patch(
        "src.modules.vitalia.application.services.prepaid_payment_service.PrepaidPaymentService._create_stripe_session",
        new=_fake_create_stripe,
    )
