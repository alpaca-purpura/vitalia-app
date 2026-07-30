"""RED tests for POST /inbox/conversations/{conv_id}/messages/{msg_id}/revert.

TDD: these tests fail until inbox/api/router.py is created (T-inbox-be-5).
Covers:
  - SC-03 edge: 5-minute window expired → 410 Gone
  - Happy path: retract within window → 200 + RetractMessageResponse
  - Patient replied conflict → 409
  - 404 no active action receipt

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
MSG_ID = uuid4()
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


# ---------------------------------------------------------------------------
# SC-03 edge — 5-minute window expired → 410 Gone
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_410_gone_after_5min(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """SC-03: ActionReceipt expired (>5 min since send) → 410 Gone."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        ActionReceiptExpiredError,
    )

    expired_at = datetime(2000, 1, 1, tzinfo=UTC)
    retract_svc = AsyncMock()
    retract_svc.retract.side_effect = ActionReceiptExpiredError(MSG_ID, expired_at)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_retract_service",
        lambda: retract_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages/{MSG_ID}/revert",
            json={"reason": "user_undo"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 410
    body = resp.json()
    assert "ventana" in body["detail"].lower() or "expiró" in body["detail"].lower() or "410" in str(resp.status_code)


# ---------------------------------------------------------------------------
# Happy path — retract within window → 200 + RetractMessageResponse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revert_within_window_200(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Happy path: retract within 5-min window → 200 with retract_succeeded=True."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        RetractResult,
    )

    result = RetractResult(
        message_id=MSG_ID,
        retracted_at=NOW,
        retract_succeeded=True,
        fallback_applied=False,
        retract_reason="user_undo",
    )
    retract_svc = AsyncMock()
    retract_svc.retract.return_value = result

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_retract_service",
        lambda: retract_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages/{MSG_ID}/revert",
            json={"reason": "user_undo"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["message_id"] == str(MSG_ID)
    assert body["retract_succeeded"] is True
    assert body["fallback_applied"] is False


# ---------------------------------------------------------------------------
# 409 — patient replied after AI message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revert_409_patient_replied(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Patient replied after the AI message → 409 Conflict."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        PatientRepliedConflictError,
    )

    retract_svc = AsyncMock()
    retract_svc.retract.side_effect = PatientRepliedConflictError(MSG_ID)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_retract_service",
        lambda: retract_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages/{MSG_ID}/revert",
            json={"reason": "user_undo"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 409


# ---------------------------------------------------------------------------
# 404 — no active action receipt
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revert_404_no_receipt(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No active action receipt for message → 404."""
    from src.modules.vitalia.inbox.application.services.retract_message_service import (
        MessageNotRetractableError,
    )

    retract_svc = AsyncMock()
    retract_svc.retract.side_effect = MessageNotRetractableError(MSG_ID)

    monkeypatch.setattr(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        AsyncMock(return_value=mock_clinic_ctx_doctor),
    )
    monkeypatch.setattr(
        "src.modules.vitalia.inbox.api.router._get_retract_service",
        lambda: retract_svc,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            f"/api/v1/vitalia/inbox/conversations/{CONV_ID}/messages/{MSG_ID}/revert",
            json={"reason": "user_undo"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 404
