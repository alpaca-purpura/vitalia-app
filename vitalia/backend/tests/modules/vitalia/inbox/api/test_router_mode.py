"""RED tests for PATCH /inbox/conversations/{conv_id}/mode.

TDD: these tests fail until inbox/api/router.py is created (T-inbox-be-5).
Covers:
  - SC-03 OCC: stale expected_updated_at → 409 Conflict
  - Happy path: mode change within valid OCC → 200 + ConversationResponse
  - Pause Adrián → 200 + ConversationResponse
  - Conversation not found → 404

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
NOW = datetime.now(UTC)
STALE_TS = datetime(2020, 1, 1, tzinfo=UTC)
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


# ---------------------------------------------------------------------------
# SC-03 OCC — stale expected_updated_at → 409 Conflict
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_occ_409(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SC-03: OCC check fails (stale expected_updated_at) → 409 Conflict."""
    from src.modules.vitalia.inbox.application.services.set_mode_service import (
        OCCConflictError,
    )

    mode_svc = AsyncMock()
    mode_svc.set_mode.side_effect = OCCConflictError(CONV_ID)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_set_mode_service",
        lambda: mode_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/mode",
            json={
                "mode": "human",
                "proposal_required": False,
                "expected_updated_at": STALE_TS.isoformat(),
            },
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 409
    body = resp.json()
    assert "conflict" in body["detail"].lower() or "409" in str(resp.status_code)


# ---------------------------------------------------------------------------
# Happy path — mode change with valid OCC → 200 + ConversationResponse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_mode_200_human(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Happy path: doctor sets conversation to human mode → 200."""
    from src.modules.vitalia.inbox.application.services.set_mode_service import (
        SetModeResult,
    )

    result = SetModeResult(
        conversation_id=CONV_ID,
        handler_mode="human",
        proposal_required=False,
        status="open",
        pause_until=None,
        help_needed=False,
        updated_at=NOW,
    )
    mode_svc = AsyncMock()
    mode_svc.set_mode.return_value = result

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_set_mode_service",
        lambda: mode_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/mode",
            json={
                "mode": "human",
                "proposal_required": False,
                "expected_updated_at": NOW.isoformat(),
            },
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(CONV_ID)
    assert body["handler_mode"] == "human"


# ---------------------------------------------------------------------------
# Pause Adrián → 200 + ConversationResponse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pause_adrian_200(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /conversations/{id}/pause → 200 + ConversationResponse."""
    from datetime import timedelta

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
            json={"reason": "taking a call"},
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


# ---------------------------------------------------------------------------
# RBAC regression — owner (front-desk operator) may change mode (Chris UI #8)
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_clinic_ctx_owner() -> MagicMock:
    """Owner context — front-desk operator, NOT a strict clinical PHI role."""
    ctx = MagicMock()
    ctx.user_id = str(USER_ID)
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.role = "owner"
    ctx.email = "owner@vitalia.test"
    ctx.name = "Clinic Owner"
    return ctx


@pytest.mark.asyncio
async def test_set_mode_200_owner_operator(
    mock_clinic_ctx_owner: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression: owner is an inbox operator → set_mode allowed (was 403)."""
    from src.modules.vitalia.inbox.application.services.set_mode_service import (
        SetModeResult,
    )

    result = SetModeResult(
        conversation_id=CONV_ID,
        handler_mode="ai",
        proposal_required=True,
        status="open",
        pause_until=None,
        help_needed=False,
        updated_at=NOW,
    )
    mode_svc = AsyncMock()
    mode_svc.set_mode.return_value = result

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_owner),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_set_mode_service",
        lambda: mode_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/mode",
            json={
                "mode": "ai",
                "proposal_required": True,
                "expected_updated_at": NOW.isoformat(),
            },
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200, resp.text
    assert resp.json()["proposal_required"] is True


# ---------------------------------------------------------------------------
# 404 — conversation not found in set_mode
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_set_mode_404_conv_not_found(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Conversation not found → 404."""
    from src.modules.vitalia.inbox.application.services.set_mode_service import (
        ConversationNotFoundError,
    )

    mode_svc = AsyncMock()
    mode_svc.set_mode.side_effect = ConversationNotFoundError(CONV_ID)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_set_mode_service",
        lambda: mode_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/mode",
            json={
                "mode": "human",
                "proposal_required": False,
                "expected_updated_at": NOW.isoformat(),
            },
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 404
