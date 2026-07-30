"""Unit tests — ConsentService (T-be-6 A1).

TDD RED → GREEN. All tests use mocked repositories (no Postgres needed).

Acceptance criteria (T-be-6):
  A1: Consent URL HMAC verifies + 24h expiry default
      (test_hmac_verify, test_consent_url_expiry_24h_default)

Decision coverage:
  D1: DDD inside-out — services receive repos via DI, no direct DB access.
  D2: Idempotency — same (patient_id, booking_id, template_slug) within TTL → returns existing.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.vitalia.application.services.consent_service import (
    ConsentService,
    ConsentUrlResult,
    RequestConsentRequest,
    SignConsentRequest,
)

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture()
def tenant_id() -> uuid.UUID:
    return uuid.UUID("11111111-0000-0000-0000-000000000001")


@pytest.fixture()
def patient_id() -> uuid.UUID:
    return uuid.UUID("22222222-0000-0000-0000-000000000002")


@pytest.fixture()
def booking_id() -> uuid.UUID:
    return uuid.UUID("33333333-0000-0000-0000-000000000003")


@pytest.fixture()
def consent_id() -> uuid.UUID:
    return uuid.UUID("44444444-0000-0000-0000-000000000004")


@pytest.fixture()
def request_consent(patient_id: uuid.UUID, booking_id: uuid.UUID) -> RequestConsentRequest:
    return RequestConsentRequest(
        patient_id=patient_id,
        booking_id=booking_id,
        consent_template_slug="informed_consent_dental_v1",
        delivery_channels=["whatsapp", "email"],
    )


@pytest.fixture()
def mock_consent_repo() -> MagicMock:
    repo = MagicMock()
    repo.get_pending_by_booking = AsyncMock(return_value=None)  # no existing by default
    repo.save = AsyncMock()
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
    mock_consent_repo: MagicMock,
    *,
    hmac_secret: str = "test-secret-key",
) -> ConsentService:
    return ConsentService(
        session=mock_session,
        consent_repo=mock_consent_repo,
        tenant_id=tenant_id,
        hmac_secret=hmac_secret,
    )


# ── A1: HMAC verify ──────────────────────────────────────────────────────────


def test_hmac_verify(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_consent_repo: MagicMock,
    consent_id: uuid.UUID,
) -> None:
    """A1: The signed consent URL HMAC must be verifiable with the secret.

    ConsentService.build_consent_url() produces HMAC-SHA256 token for consent_id.
    ConsentService.verify_consent_url() must return True for that token.
    """
    secret = "vitalia-consent-hmac-secret-test"
    svc = _make_service(tenant_id, mock_session, mock_consent_repo, hmac_secret=secret)

    url = svc.build_consent_url(consent_id=consent_id, base_url="https://vitalia.app")
    assert "token=" in url, "URL must contain HMAC token param"

    # Token extracted from URL
    token = url.split("token=")[1].split("&")[0]
    assert svc.verify_consent_token(consent_id=consent_id, token=token), (
        "HMAC token must verify against consent_id with same secret"
    )


def test_hmac_verify_tampered_token_fails(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_consent_repo: MagicMock,
    consent_id: uuid.UUID,
) -> None:
    """A1 defensive: tampered HMAC token must NOT verify."""
    svc = _make_service(tenant_id, mock_session, mock_consent_repo, hmac_secret="secret-key")

    tampered_token = "deadbeefdeadbeef" * 4
    assert not svc.verify_consent_token(consent_id=consent_id, token=tampered_token)


def test_hmac_verify_wrong_consent_id_fails(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_consent_repo: MagicMock,
    consent_id: uuid.UUID,
) -> None:
    """A1 defensive: token for consent A must NOT verify against consent B."""
    svc = _make_service(tenant_id, mock_session, mock_consent_repo, hmac_secret="secret-key")
    other_consent_id = uuid.uuid4()

    url = svc.build_consent_url(consent_id=consent_id, base_url="https://vitalia.app")
    token = url.split("token=")[1].split("&")[0]

    assert not svc.verify_consent_token(consent_id=other_consent_id, token=token), (
        "Token for consent A must not verify against consent B"
    )


# ── A1: 24h expiry default ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_consent_url_expiry_24h_default(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_consent_repo: MagicMock,
    request_consent: RequestConsentRequest,
    consent_id: uuid.UUID,
) -> None:
    """A1: request_consent creates record with expires_at = now + 24h (default)."""

    svc = _make_service(tenant_id, mock_session, mock_consent_repo)

    before_call = datetime.now(tz=timezone.utc)
    result = await svc.request_consent(request=request_consent, base_url="https://vitalia.app")
    after_call = datetime.now(tz=timezone.utc)

    # Verify expires_at is within 24h ± 1 minute tolerance
    min_expiry = before_call + timedelta(hours=24) - timedelta(minutes=1)
    max_expiry = after_call + timedelta(hours=24) + timedelta(minutes=1)

    assert min_expiry <= result.expires_at <= max_expiry, (
        f"expires_at={result.expires_at} must be ~now+24h, got outside [{min_expiry}, {max_expiry}]"
    )


@pytest.mark.asyncio
async def test_consent_expiry_custom_hours(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_consent_repo: MagicMock,
    patient_id: uuid.UUID,
    booking_id: uuid.UUID,
) -> None:
    """request_consent must honor custom expiry_hours override (48h, 72h)."""
    svc = _make_service(tenant_id, mock_session, mock_consent_repo)

    request_48h = RequestConsentRequest(
        patient_id=patient_id,
        booking_id=booking_id,
        consent_template_slug="surgery_consent_v1",
        delivery_channels=["email"],
        expiry_hours=48,
    )

    before_call = datetime.now(tz=timezone.utc)
    result = await svc.request_consent(request=request_48h, base_url="https://vitalia.app")
    after_call = datetime.now(tz=timezone.utc)

    min_expiry = before_call + timedelta(hours=48) - timedelta(minutes=1)
    max_expiry = after_call + timedelta(hours=48) + timedelta(minutes=1)

    assert min_expiry <= result.expires_at <= max_expiry, f"48h expiry out of range [{min_expiry}, {max_expiry}]"


# ── D2: Idempotency — same booking, same template → returns existing ──────────


@pytest.mark.asyncio
async def test_request_consent_idempotent_same_booking(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_consent_repo: MagicMock,
    request_consent: RequestConsentRequest,
    booking_id: uuid.UUID,
    consent_id: uuid.UUID,
) -> None:
    """D2: Same booking_id + template_slug → returns existing pending consent (no new row)."""
    from unittest.mock import MagicMock as MM

    existing_consent = MM()
    existing_consent.id = consent_id
    existing_consent.status = "pending_signature"
    existing_consent.expires_at = datetime.now(tz=timezone.utc) + timedelta(hours=20)
    existing_consent.consent_template_slug = request_consent.consent_template_slug
    existing_consent.delivery_channels = ["whatsapp"]

    mock_consent_repo.get_pending_by_booking = AsyncMock(return_value=existing_consent)

    svc = _make_service(tenant_id, mock_session, mock_consent_repo)
    result = await svc.request_consent(request=request_consent, base_url="https://vitalia.app")

    assert result.consent_id == consent_id, "Must return existing consent_id on idempotent call"
    assert result.is_new is False, "is_new must be False on idempotent hit"
    mock_consent_repo.save.assert_not_called()


# ── sign_consent ─────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_sign_consent_captures_ip_ua_name(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_consent_repo: MagicMock,
    consent_id: uuid.UUID,
) -> None:
    """sign_consent must capture signature_name, IP, User-Agent."""
    mock_consent_repo.mark_signed = AsyncMock(return_value=True)

    svc = _make_service(tenant_id, mock_session, mock_consent_repo)
    request = SignConsentRequest(
        consent_id=consent_id,
        signed_name="Juan Perez",
        signed_ip="192.168.1.100",
        signed_user_agent="Mozilla/5.0 (iPhone)",
        signature_method="typed_name",
        token="valid-token",
    )

    # We bypass HMAC check in this test by patching verify_consent_token
    with patch.object(svc, "verify_consent_token", return_value=True):
        result = await svc.sign_consent(request=request)

    assert result.success is True
    mock_consent_repo.mark_signed.assert_called_once()
    call_kwargs = mock_consent_repo.mark_signed.call_args.kwargs
    assert call_kwargs["signed_name"] == "Juan Perez"
    assert call_kwargs["signed_ip"] == "192.168.1.100"
    assert call_kwargs["signed_user_agent"] == "Mozilla/5.0 (iPhone)"
    assert call_kwargs["signature_method"] == "typed_name"


@pytest.mark.asyncio
async def test_sign_consent_invalid_token_rejected(
    tenant_id: uuid.UUID,
    mock_session: MagicMock,
    mock_consent_repo: MagicMock,
    consent_id: uuid.UUID,
) -> None:
    """sign_consent must reject tampered HMAC token."""
    svc = _make_service(tenant_id, mock_session, mock_consent_repo, hmac_secret="secret")

    request = SignConsentRequest(
        consent_id=consent_id,
        signed_name="Attacker",
        signed_ip="1.2.3.4",
        signed_user_agent="python-requests",
        signature_method="typed_name",
        token="tampered-invalid-token",
    )

    result = await svc.sign_consent(request=request)
    assert result.success is False
    assert "invalid_token" in result.error_code or "token" in (result.error_code or "")
    mock_consent_repo.mark_signed.assert_not_called()


# ── D1: DI constructor ───────────────────────────────────────────────────────


def test_consent_service_constructor_requires_di_params(tenant_id: uuid.UUID) -> None:
    """D1: ConsentService must accept session + consent_repo + tenant_id + hmac_secret via DI."""
    import inspect

    sig = inspect.signature(ConsentService.__init__)
    params = list(sig.parameters.keys())
    assert "session" in params
    assert "consent_repo" in params
    assert "tenant_id" in params
    assert "hmac_secret" in params


def test_consent_url_result_is_pydantic_model() -> None:
    """ConsentUrlResult must be Pydantic v2 model."""
    result = ConsentUrlResult(
        consent_id=uuid.uuid4(),
        consent_url="https://vitalia.app/consent?token=abc",
        expires_at=datetime.now(tz=timezone.utc) + timedelta(hours=24),
        is_new=True,
    )
    assert result.is_new is True
