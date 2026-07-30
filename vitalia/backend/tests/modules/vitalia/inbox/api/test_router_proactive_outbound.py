"""Tests for POST /inbox/proactive-outbound.

Covers:
  - Happy path: doctor sends proactive HSM → 201 + ProactiveOutboundResponse
  - Template not found → 422
  - Lead not found → 404
  - Marketing opt-in missing → 403
  - Rate limit exceeded → 429
  - 403 marketing role (PHI gated)
  - 401 invalid token

downstream-regression-na: brand-local vitalia inbox router test
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


def _make_app() -> FastAPI:
    """Build minimal FastAPI test app with inbox router.

    Includes get_async_session stub override (Slice 2: endpoints have
    session: Annotated[AsyncSession, Depends(get_async_session)]).
    """
    from src.modules.vitalia.inbox.api.router import router as inbox_router
    from tests.modules.vitalia.inbox.api.conftest import apply_session_stub

    app = FastAPI(redirect_slashes=False)
    app.include_router(inbox_router, prefix="/api/v1/vitalia/inbox")
    return apply_session_stub(app)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TENANT_ID = uuid4()
CLINIC_ID = uuid4()
LEAD_ID = uuid4()
CONV_ID = uuid4()
MSG_ID = uuid4()
USER_ID = uuid4()
NOW = datetime.now(UTC)
VALID_TOKEN = "Bearer valid-test-token"

PROACTIVE_PAYLOAD = {
    "lead_id": str(LEAD_ID),
    "template_id": "appointment_reminder_v1",
    "variables": {"patient_name": "Juan", "date": "2026-06-01"},
    "channel": "whatsapp",
}


@pytest.fixture()
def mock_clinic_ctx_doctor() -> MagicMock:
    """Doctor context (PHI access allowed)."""
    ctx = MagicMock()
    ctx.user_id = str(USER_ID)
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.role = "doctor"
    ctx.email = "doc@vitalia.test"
    ctx.name = "Dr. Test"
    return ctx


@pytest.fixture()
def mock_clinic_ctx_marketing() -> MagicMock:
    """Marketing context (PHI access denied)."""
    ctx = MagicMock()
    ctx.user_id = str(uuid4())
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.role = "marketing"
    ctx.email = "mkt@vitalia.test"
    ctx.name = "Marketing User"
    return ctx


# ---------------------------------------------------------------------------
# Happy path — doctor sends proactive HSM → 201
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proactive_outbound_201(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Doctor sends proactive message → 201 + ProactiveOutboundResponse."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        ProactiveOutboundResult,
    )

    result = ProactiveOutboundResult(
        conversation_id=CONV_ID,
        message_id=MSG_ID,
        template_id="appointment_reminder_v1",
        channel="whatsapp",
        sent_at=NOW,
        compliance_checked=True,
    )
    proactive_svc = AsyncMock()
    proactive_svc.send_proactive.return_value = result

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_proactive_service",
        lambda: proactive_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/proactive-outbound",
            json=PROACTIVE_PAYLOAD,
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["conversation_id"] == str(CONV_ID)
    assert body["message_id"] == str(MSG_ID)
    assert body["template_id"] == "appointment_reminder_v1"
    assert body["compliance_checked"] is True


# ---------------------------------------------------------------------------
# 422 — template not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proactive_outbound_422_template_not_found(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Unknown template_id → 422 Unprocessable Entity."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        TemplateNotFoundError,
    )

    proactive_svc = AsyncMock()
    proactive_svc.send_proactive.side_effect = TemplateNotFoundError("nonexistent_template")

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_proactive_service",
        lambda: proactive_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/proactive-outbound",
            json={**PROACTIVE_PAYLOAD, "template_id": "nonexistent_template"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 404 — lead not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proactive_outbound_404_lead_not_found(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lead does not exist → 404."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        LeadNotFoundError,
    )

    proactive_svc = AsyncMock()
    proactive_svc.send_proactive.side_effect = LeadNotFoundError(LEAD_ID)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_proactive_service",
        lambda: proactive_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/proactive-outbound",
            json=PROACTIVE_PAYLOAD,
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 403 — marketing opt-in missing
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proactive_outbound_403_marketing_optin_missing(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Marketing template but lead has no opt-in → 403."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        MarketingOptInRequiredError,
    )

    proactive_svc = AsyncMock()
    proactive_svc.send_proactive.side_effect = MarketingOptInRequiredError("marketing_campaign_v1", LEAD_ID)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_proactive_service",
        lambda: proactive_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/proactive-outbound",
            json=PROACTIVE_PAYLOAD,
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 429 — rate limit exceeded
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proactive_outbound_429_rate_limit(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Rate limit exceeded → 429."""
    from src.modules.vitalia.inbox.application.services.proactive_outbound_service import (
        RateLimitExceededError,
    )

    proactive_svc = AsyncMock()
    proactive_svc.send_proactive.side_effect = RateLimitExceededError(TENANT_ID)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_proactive_service",
        lambda: proactive_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/proactive-outbound",
            json=PROACTIVE_PAYLOAD,
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 429


# ---------------------------------------------------------------------------
# 403 — marketing role cannot use PHI endpoint
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proactive_outbound_403_marketing_role(
    mock_clinic_ctx_marketing: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Marketing role cannot send proactive outbound (PHI endpoint) → 403."""
    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_marketing),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/proactive-outbound",
            json=PROACTIVE_PAYLOAD,
            headers={
                "Authorization": "Bearer marketing-token",
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# 401 — invalid token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proactive_outbound_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid token → 401."""
    from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import JwtDecodeError

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(side_effect=JwtDecodeError("bad token")),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/inbox/proactive-outbound",
            json=PROACTIVE_PAYLOAD,
            headers={
                "Authorization": "Bearer invalid",
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 401
