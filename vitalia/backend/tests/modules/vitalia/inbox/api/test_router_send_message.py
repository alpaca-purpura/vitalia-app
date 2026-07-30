"""RED tests for POST /inbox/conversations/{conv_id}/messages.

TDD: these tests fail until inbox/api/router.py is created (T-inbox-be-5).
Covers:
  - SC-01: happy path doctor sends AI message → 201 + MessageResponse
  - SC-04 adversarial: marketing role → 403 Forbidden
  - 401 invalid token
  - 404 conversation not found

downstream-regression-na: brand-local vitalia inbox router test
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Lazy router import — RED phase: router.py does not exist yet
# We import inside fixtures so test collection does not fail before impl.
# ---------------------------------------------------------------------------


def _make_app() -> FastAPI:
    """Build a minimal FastAPI test app with the inbox router."""
    from src.modules.vitalia.inbox.api.router import router as inbox_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(inbox_router, prefix="/api/v1/vitalia/inbox")
    return app


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()
USER_ID = uuid4()
MSG_ID = uuid4()
NOW = datetime.now(UTC)
EXPIRES_AT = datetime(2099, 1, 1, tzinfo=UTC)

VALID_TOKEN = "Bearer valid-test-token"
MARKETING_TOKEN = "Bearer marketing-test-token"


# ---------------------------------------------------------------------------
# Fixture: mock clinic context — doctor (PHI access allowed)
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_clinic_ctx_doctor() -> MagicMock:
    """Clinic context for a doctor (PHI access allowed)."""
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
    """Clinic context for a marketing role (PHI access denied)."""
    ctx = MagicMock()
    ctx.user_id = str(uuid4())
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.role = "marketing"
    ctx.email = "mkt@vitalia.test"
    ctx.name = "Marketing User"
    return ctx


# ---------------------------------------------------------------------------
# Fixture: mock SendMessageService with success result
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_send_service_ok() -> AsyncMock:
    """SendMessageService that returns a successful SendMessageResult."""
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        SendMessageResult,
    )

    result = SendMessageResult(
        message_id=MSG_ID,
        conversation_id=CONV_ID,
        sender_type="agent_ai",
        sender_user_id=USER_ID,
        body_text="Hola, ¿en qué puedo ayudarte?",
        media_kind=None,
        media_url=None,
        media_duration_s=None,
        transcription_text=None,
        transcription_confidence=None,
        retracted_at=None,
        retract_succeeded=None,
        handler_mode="ai",
        sent_at=NOW,
        action_receipt_expires_at=EXPIRES_AT,
    )
    svc = AsyncMock()
    svc.send.return_value = result
    return svc


# ---------------------------------------------------------------------------
# SC-01 — doctor sends AI message → 201 + MessageResponse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_ai_message_201(
    mock_clinic_ctx_doctor: MagicMock,
    mock_send_service_ok: AsyncMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SC-01: Doctor sends a text message to conversation → 201 + MessageResponse body."""
    # Patch ClinicResolver and SendMessageService at the router level
    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_send_service",
        lambda: mock_send_service_ok,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages",
            json={
                "body_text": "Hola, ¿en qué puedo ayudarte?",
                "media_url": None,
                "media_kind": None,
            },
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] == str(MSG_ID)
    assert body["conversation_id"] == str(CONV_ID)
    assert body["sender_type"] == "agent_ai"
    assert body["handler_mode"] == "ai"
    assert "action_receipt_expires_at" in body


# ---------------------------------------------------------------------------
# SC-04 adversarial — marketing role → 403 Forbidden
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_marketing_role_403(
    mock_clinic_ctx_marketing: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SC-04: Marketing role cannot send messages to PHI conversations → 403."""
    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_marketing),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages",
            json={"body_text": "test"},
            headers={
                "Authorization": MARKETING_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 403
    body = resp.json()
    assert "denegado" in body["detail"].lower() or "403" in str(resp.status_code)


# ---------------------------------------------------------------------------
# 401 — invalid / missing token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_401_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid token → 401 Unauthorized."""
    from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import JwtDecodeError

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(side_effect=JwtDecodeError("bad token")),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages",
            json={"body_text": "test"},
            headers={
                "Authorization": "Bearer invalid-token",
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 404 — conversation not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_404_conv_not_found(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Conversation not found → 404."""
    from src.modules.vitalia.inbox.application.services.send_message_service import (
        ConversationNotFoundError,
    )

    send_svc = AsyncMock()
    send_svc.send.side_effect = ConversationNotFoundError(CONV_ID)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_send_service",
        lambda: send_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages",
            json={"body_text": "test"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 404
