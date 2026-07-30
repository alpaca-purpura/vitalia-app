"""Tests for GET /crm/conversations.

Covers:
  - Happy path: doctor lists conversations → 200 + ConversationListResponse (empty Slice 1)
  - 403 marketing role (PHI gated)
  - 401 invalid token

downstream-regression-na: brand-local vitalia crm router test
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient


async def _async_return(value: object) -> object:
    """Awaitable helper that returns a fixed value — used to stub async resolvers."""
    return value


def _make_app() -> FastAPI:
    """Build minimal FastAPI test app with CRM router."""
    from src.modules.vitalia.crm.api.router import router as crm_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(crm_router, prefix="/api/v1/vitalia/crm")
    return app


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TENANT_ID = uuid4()
CLINIC_ID = uuid4()
USER_ID = uuid4()
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
# Happy path — doctor lists conversations → 200 + empty list (Slice 1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_conversations_200_doctor(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Doctor lists conversations → 200 + ConversationListResponse (empty in Slice 1)."""
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_async",
        lambda *a, **kw: _async_return(mock_clinic_ctx_doctor),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/vitalia/crm/conversations",
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)


@pytest.mark.asyncio
async def test_list_conversations_with_filters_200(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Doctor lists conversations with optional query filters → 200."""
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_async",
        lambda *a, **kw: _async_return(mock_clinic_ctx_doctor),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/vitalia/crm/conversations?status=open&handler_mode=ai&limit=10",
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 403 — marketing role cannot list PHI conversations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_conversations_403_marketing(
    mock_clinic_ctx_marketing: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Marketing role cannot list PHI conversations → 403."""
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_async",
        lambda *a, **kw: _async_return(mock_clinic_ctx_marketing),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/vitalia/crm/conversations",
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
async def test_list_conversations_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid token → 401."""

    async def _raise_401(*a: object, **kw: object) -> None:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")

    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_async",
        _raise_401,
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/vitalia/crm/conversations",
            headers={
                "Authorization": "Bearer invalid",
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 401
