"""Tests for POST /inbox/conversations/{conv_id}/pause.

Covers:
  - Happy path: doctor pauses Adrián → 200 + ConversationResponse with pause_until
  - 404 conversation not found
  - 403 marketing role cannot pause (PHI endpoint)
  - 401 invalid token

downstream-regression-na: brand-local vitalia inbox router test
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
CONV_ID = uuid4()
USER_ID = uuid4()
NOW = datetime.now(UTC)
VALID_TOKEN = "Bearer valid-test-token"


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
# Happy path — doctor pauses Adrián → 200 + pause_until set
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pause_adrian_200(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Doctor pauses Adrián → 200 with pause_until populated."""
    from src.modules.vitalia.inbox.application.services.pause_adrian_service import (
        PauseResult,
    )

    pause_until = NOW + timedelta(hours=1)
    result = PauseResult(
        conversation_id=CONV_ID,
        pause_until=pause_until,
        handler_mode="ai",
        status="open",
    )
    pause_svc = AsyncMock()
    pause_svc.pause.return_value = result

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_pause_service",
        lambda: pause_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/pause",
            json={"reason": "attending to another patient"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(CONV_ID)
    assert body["pause_until"] is not None
    assert body["handler_mode"] == "ai"


# ---------------------------------------------------------------------------
# 404 — conversation not found
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pause_404_conv_not_found(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Conversation not found → 404."""
    from src.modules.vitalia.inbox.application.services.pause_adrian_service import (
        ConversationNotFoundError,
    )

    pause_svc = AsyncMock()
    pause_svc.pause.side_effect = ConversationNotFoundError(CONV_ID)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_pause_service",
        lambda: pause_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/pause",
            json={"reason": "test"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 403 — marketing role cannot access PHI endpoints
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pause_403_marketing_role(
    mock_clinic_ctx_marketing: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Marketing role cannot pause Adrián (PHI endpoint) → 403."""
    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_marketing),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/pause",
            json={"reason": "test"},
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
async def test_pause_401_invalid_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid token → 401."""
    from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import JwtDecodeError

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(side_effect=JwtDecodeError("bad token")),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/pause",
            json={"reason": "test"},
            headers={
                "Authorization": "Bearer invalid",
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 401
