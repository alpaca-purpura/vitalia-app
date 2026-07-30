"""Tests for GET /inbox/conversations/{conv_id}/activity.

Covers:
  - Happy path: doctor gets activity stream → 200 + ActivityStreamResponse
  - Empty stream → 200 + empty items list
  - 403 marketing role cannot access PHI
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
CONV_ID = uuid4()
USER_ID = uuid4()
AGENT_ID = uuid4()
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
# Happy path — doctor gets activity stream → 200 with items
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_activity_stream_200(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Doctor gets activity stream → 200 with ActivityStreamResponse."""
    from src.modules.vitalia.inbox.application.services.activity_event_service import (
        ActivityStreamItem,
        ActivityStreamResult,
    )

    items = [
        ActivityStreamItem(
            id=uuid4(),
            event_kind="message_sent",
            description_es="Adrián envió un mensaje al paciente.",
            agent_id=str(AGENT_ID),
            occurred_at=NOW,
        ),
        ActivityStreamItem(
            id=uuid4(),
            event_kind="mode_changed",
            description_es="El médico cambió el modo a humano.",
            agent_id="",
            occurred_at=NOW,
        ),
    ]
    result = ActivityStreamResult(conversation_id=CONV_ID, events=items, limit=8, since_minutes=5)
    activity_svc = AsyncMock()
    activity_svc.get_stream.return_value = result

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_activity_service",
        lambda: activity_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/activity-stream",
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "events" in body
    assert len(body["events"]) == 2
    assert body["events"][0]["event_kind"] == "message_sent"


# ---------------------------------------------------------------------------
# Empty stream → 200 with empty items list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_activity_stream_empty_200(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No activity events → 200 with empty items list."""
    from src.modules.vitalia.inbox.application.services.activity_event_service import (
        ActivityStreamResult,
    )

    result = ActivityStreamResult(conversation_id=CONV_ID, events=[], limit=8, since_minutes=5)
    activity_svc = AsyncMock()
    activity_svc.get_stream.return_value = result

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_activity_service",
        lambda: activity_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/activity-stream",
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["events"] == []


# ---------------------------------------------------------------------------
# 403 — marketing role cannot access PHI
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_activity_stream_403_marketing(
    mock_clinic_ctx_marketing: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Marketing role cannot get activity stream (PHI endpoint) → 403."""
    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_marketing),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/activity-stream",
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
async def test_get_activity_stream_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid token → 401."""
    from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import JwtDecodeError

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(side_effect=JwtDecodeError("bad token")),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/activity-stream",
            headers={
                "Authorization": "Bearer invalid",
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 401
