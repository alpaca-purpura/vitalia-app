# cap: inbox.adrian-inbox
"""Tests for POST /inbox/conversations/{conv_id}/nudge — TDD RED-first (T-2).

SC-6 + architecture acceptance validators:
- fn-be-nudge: POST /nudge happy path → 201 + NudgeResponse
- av-be-arch-fitness: response_model= present; dual-tenant 403 for non-PHI roles
- av-no-sales-agent-import: NudgeService never imports from sales_agent/ (verified by import test)
- PHI gated: only doctor/nurse/admin_clinic roles can call nudge
- cross-tenant: conv_id from other tenant → 404 (dual filter)
- conv not live → 422 NudgeNotApplicableError
- conv not found → 404 ConvNotFoundError
- idempotency: same day repeat → 200 nudge_sent=False
"""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
CONV_ID = uuid4()
USER_ID = uuid4()
MSG_ID = uuid4()
ACTIVITY_ID = uuid4()

_AUTH = "Bearer test-token-doctor"
_TENANT_HEADER = str(TENANT_ID)
_CLINIC_HEADER = str(CLINIC_ID)


def _make_clinic_context(role: str = "doctor") -> MagicMock:
    ctx = MagicMock()
    ctx.tenant_id = TENANT_ID
    ctx.user_id = str(USER_ID)
    ctx.role = role
    ctx.clinic_id = CLINIC_ID
    return ctx


def _make_nudge_result(*, nudge_sent: bool = True) -> MagicMock:
    from src.modules.vitalia.inbox.application.services.nudge_service import NudgeResult

    return NudgeResult(
        conversation_id=CONV_ID,
        message_id=MSG_ID if nudge_sent else None,
        nudge_sent=nudge_sent,
        activity_event_id=ACTIVITY_ID,
        sent_at=datetime.now(UTC),
    )


def _make_app() -> FastAPI:
    """Minimal FastAPI app with only the inbox router mounted."""
    from src.modules.vitalia.inbox.api.router import router

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/inbox")
    return app


def _make_stub_nudge_service(nudge_result: object) -> object:
    """Create a stub NudgeService that returns a fixed result."""
    svc = MagicMock()
    svc.nudge = AsyncMock(return_value=nudge_result)
    return svc


# ---------------------------------------------------------------------------
# Test: happy path POST /nudge → 201 NudgeResponse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_endpoint_happy_path_returns_201() -> None:
    """SC-6: POST /inbox/conversations/{conv_id}/nudge → 201 + nudge_sent=True."""
    from src.modules.vitalia.inbox.api.router import _get_nudge_service
    from tests.modules.vitalia.inbox.api.conftest import apply_session_stub

    ctx = _make_clinic_context(role="doctor")
    nudge_result = _make_nudge_result(nudge_sent=True)
    stub_svc = _make_stub_nudge_service(nudge_result)

    app = _make_app()
    apply_session_stub(app)
    app.dependency_overrides[_get_nudge_service] = lambda: stub_svc

    with patch(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        new_callable=AsyncMock,
        return_value=ctx,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/inbox/conversations/{CONV_ID}/nudge",
                headers={
                    "Authorization": _AUTH,
                    "X-Tenant-ID": _TENANT_HEADER,
                    "X-Clinic-ID": _CLINIC_HEADER,
                },
                json={"reason": "paciente inactivo 2 días"},
            )

    assert resp.status_code == 201
    data = resp.json()
    assert data["nudge_sent"] is True
    assert data["conversation_id"] == str(CONV_ID)
    assert data["message_id"] == str(MSG_ID)


# ---------------------------------------------------------------------------
# Test: PHI gate — non-PHI role (marketing) → 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_endpoint_non_phi_role_returns_403() -> None:
    """PHI gated: role 'marketing' cannot call nudge → 403."""
    from tests.modules.vitalia.inbox.api.conftest import apply_session_stub

    ctx = _make_clinic_context(role="marketing")  # non-PHI role

    app = _make_app()
    apply_session_stub(app)

    with patch(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        new_callable=AsyncMock,
        return_value=ctx,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/inbox/conversations/{CONV_ID}/nudge",
                headers={
                    "Authorization": _AUTH,
                    "X-Tenant-ID": _TENANT_HEADER,
                    "X-Clinic-ID": _CLINIC_HEADER,
                },
                json={},
            )

    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Test: PHI gate — admin_clinic role → allowed (201)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_endpoint_admin_clinic_role_allowed() -> None:
    """PHI gated: admin_clinic role CAN call nudge → not 403."""
    from src.modules.vitalia.inbox.api.router import _get_nudge_service
    from tests.modules.vitalia.inbox.api.conftest import apply_session_stub

    ctx = _make_clinic_context(role="admin_clinic")
    nudge_result = _make_nudge_result(nudge_sent=True)
    stub_svc = _make_stub_nudge_service(nudge_result)

    app = _make_app()
    apply_session_stub(app)
    app.dependency_overrides[_get_nudge_service] = lambda: stub_svc

    with patch(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        new_callable=AsyncMock,
        return_value=ctx,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/inbox/conversations/{CONV_ID}/nudge",
                headers={
                    "Authorization": _AUTH,
                    "X-Tenant-ID": _TENANT_HEADER,
                    "X-Clinic-ID": _CLINIC_HEADER,
                },
                json={},
            )

    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Test: nurse role → allowed (201)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_endpoint_nurse_role_allowed() -> None:
    """PHI gated: nurse role CAN call nudge → not 403."""
    from src.modules.vitalia.inbox.api.router import _get_nudge_service
    from tests.modules.vitalia.inbox.api.conftest import apply_session_stub

    ctx = _make_clinic_context(role="nurse")
    nudge_result = _make_nudge_result(nudge_sent=True)
    stub_svc = _make_stub_nudge_service(nudge_result)

    app = _make_app()
    apply_session_stub(app)
    app.dependency_overrides[_get_nudge_service] = lambda: stub_svc

    with patch(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        new_callable=AsyncMock,
        return_value=ctx,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/inbox/conversations/{CONV_ID}/nudge",
                headers={
                    "Authorization": _AUTH,
                    "X-Tenant-ID": _TENANT_HEADER,
                    "X-Clinic-ID": _CLINIC_HEADER,
                },
                json={},
            )

    assert resp.status_code == 201


# ---------------------------------------------------------------------------
# Test: cross-tenant → 404 (NudgeService raises ConvNotFoundError)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_endpoint_cross_tenant_returns_404() -> None:
    """SC-10: conv_id from another tenant → NudgeService raises ConvNotFoundError → 404."""
    from src.modules.vitalia.inbox.api.router import _get_nudge_service
    from src.modules.vitalia.inbox.application.services.nudge_service import ConvNotFoundError
    from tests.modules.vitalia.inbox.api.conftest import apply_session_stub

    ctx = _make_clinic_context(role="doctor")

    svc = MagicMock()
    svc.nudge = AsyncMock(side_effect=ConvNotFoundError(conv_id=CONV_ID))

    app = _make_app()
    apply_session_stub(app)
    app.dependency_overrides[_get_nudge_service] = lambda: svc

    with patch(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        new_callable=AsyncMock,
        return_value=ctx,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/inbox/conversations/{CONV_ID}/nudge",
                headers={
                    "Authorization": _AUTH,
                    "X-Tenant-ID": _TENANT_HEADER,
                    "X-Clinic-ID": _CLINIC_HEADER,
                },
                json={},
            )

    assert resp.status_code == 404
    assert "Conversación" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# Test: conv not live → 422 (NudgeNotApplicableError)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_endpoint_conv_not_live_returns_422() -> None:
    """NudgeNotApplicableError (closed conv or not stalled) → 422."""
    from src.modules.vitalia.inbox.api.router import _get_nudge_service
    from src.modules.vitalia.inbox.application.services.nudge_service import NudgeNotApplicableError
    from tests.modules.vitalia.inbox.api.conftest import apply_session_stub

    ctx = _make_clinic_context(role="doctor")

    svc = MagicMock()
    svc.nudge = AsyncMock(
        side_effect=NudgeNotApplicableError(conv_id=CONV_ID, reason="La conversación no está activa.")
    )

    app = _make_app()
    apply_session_stub(app)
    app.dependency_overrides[_get_nudge_service] = lambda: svc

    with patch(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        new_callable=AsyncMock,
        return_value=ctx,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/inbox/conversations/{CONV_ID}/nudge",
                headers={
                    "Authorization": _AUTH,
                    "X-Tenant-ID": _TENANT_HEADER,
                    "X-Clinic-ID": _CLINIC_HEADER,
                },
                json={},
            )

    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Test: idempotent repeat → 200 nudge_sent=False (not 201)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nudge_endpoint_idempotent_repeat_returns_200_not_sent() -> None:
    """Same day repeat → nudge_sent=False → 200 (not 201)."""
    from src.modules.vitalia.inbox.api.router import _get_nudge_service
    from tests.modules.vitalia.inbox.api.conftest import apply_session_stub

    ctx = _make_clinic_context(role="doctor")
    nudge_result = _make_nudge_result(nudge_sent=False)
    stub_svc = _make_stub_nudge_service(nudge_result)

    app = _make_app()
    apply_session_stub(app)
    app.dependency_overrides[_get_nudge_service] = lambda: stub_svc

    with patch(
        "src.modules.vitalia.iam.application.services.clinic_resolver.ClinicResolver.async_resolve",
        new_callable=AsyncMock,
        return_value=ctx,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"/inbox/conversations/{CONV_ID}/nudge",
                headers={
                    "Authorization": _AUTH,
                    "X-Tenant-ID": _TENANT_HEADER,
                    "X-Clinic-ID": _CLINIC_HEADER,
                },
                json={},
            )

    assert resp.status_code == 200
    assert resp.json()["nudge_sent"] is False


# ---------------------------------------------------------------------------
# Test: av-no-sales-agent-import — NudgeService has no direct sales_agent import
# ---------------------------------------------------------------------------


def test_nudge_service_has_no_direct_sales_agent_import() -> None:
    """av-no-sales-agent-import: inbox/application/services/nudge_service.py
    MUST NOT import from src.modules.vitalia.sales_agent (uses resolver pattern instead).
    """
    import ast
    from pathlib import Path

    # Navigate from test file to nudge_service.py
    # tests/modules/vitalia/inbox/api/test_router_nudge.py
    # → vitalia/backend/src/modules/vitalia/inbox/application/services/nudge_service.py
    test_path = Path(__file__).resolve()
    # Up 8 levels: api → inbox → vitalia → modules → tests → backend → vitalia → WS
    backend_root = test_path.parent.parent.parent.parent.parent.parent  # vitalia/backend
    svc_path = backend_root / "src/modules/vitalia/inbox/application/services/nudge_service.py"

    if not svc_path.exists():
        pytest.skip("nudge_service.py not yet created (RED phase)")

    source = svc_path.read_text()
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "sales_agent" not in node.module, (
                f"nudge_service.py imports from sales_agent directly: {node.module}. "
                "Use proactive_resolver DI pattern instead."
            )


# ---------------------------------------------------------------------------
# Test: response_model matches NudgeResponse schema (structural validation)
# ---------------------------------------------------------------------------


def test_nudge_endpoint_has_response_model() -> None:
    """av-be-arch-fitness: nudge endpoint declares response_model=NudgeResponse."""
    from src.modules.vitalia.inbox.api.router import router
    from src.modules.vitalia.inbox.application.dto.nudge_dto import NudgeResponse

    # Find the nudge route
    nudge_routes = [r for r in router.routes if hasattr(r, "path") and "nudge" in r.path]
    assert len(nudge_routes) == 1, "Expected exactly one /nudge route"
    route = nudge_routes[0]
    assert route.response_model is NudgeResponse, (
        f"Nudge route response_model is {route.response_model!r}, expected NudgeResponse"
    )
