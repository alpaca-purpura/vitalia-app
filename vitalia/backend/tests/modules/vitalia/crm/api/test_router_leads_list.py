"""Tests for GET /crm/leads and POST /crm/leads.

Covers:
  - GET /leads: happy path all roles → 200 + LeadListResponse (non-PHI)
  - GET /leads: 401 invalid token
  - POST /leads: happy path → 201 + LeadResponse
  - PATCH /leads/{id}: lead not found → 404

downstream-regression-na: brand-local vitalia crm router test
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient


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
LEAD_ID = uuid4()
USER_ID = uuid4()
VALID_TOKEN = "Bearer valid-test-token"

CREATE_LEAD_PAYLOAD = {
    "name": "María García",
    "email": "maria@example.com",
    "phone": "+525512345678",
    "source": "instagram",
    "status": "new",
    "notes": None,
    "marketing_opt_in": True,
}


@pytest.fixture()
def mock_clinic_ctx_doctor() -> MagicMock:
    """Doctor context (any authenticated role can access leads)."""
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
    """Marketing context — also allowed for non-PHI leads."""
    ctx = MagicMock()
    ctx.user_id = str(uuid4())
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.role = "marketing"
    ctx.email = "mkt@vitalia.test"
    ctx.name = "Marketing User"
    return ctx


# ---------------------------------------------------------------------------
# GET /leads — happy path → 200 + paginated list (empty in Slice 1)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_200_doctor(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Doctor lists leads → 200 + LeadListResponse (empty Slice 1)."""
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._get_resolver",
        lambda: MagicMock(**{"resolve.return_value": mock_clinic_ctx_doctor}),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/vitalia/crm/leads",
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
async def test_list_leads_200_marketing(
    mock_clinic_ctx_marketing: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Marketing role can also list leads (non-PHI) → 200."""
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._get_resolver",
        lambda: MagicMock(**{"resolve.return_value": mock_clinic_ctx_marketing}),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/vitalia/crm/leads",
            headers={
                "Authorization": "Bearer marketing-token",
                "X-Tenant-ID": str(TENANT_ID),
            },
        )

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# GET /leads — 401 invalid token
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_leads_401(monkeypatch: pytest.MonkeyPatch) -> None:
    """Invalid token → 401."""
    from src.modules.vitalia.iam.infrastructure.clerk_jwt_decoder import JwtDecodeError

    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._get_resolver",
        lambda: MagicMock(**{"resolve.side_effect": JwtDecodeError("bad token")}),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/vitalia/crm/leads",
            headers={
                "Authorization": "Bearer invalid",
                "X-Tenant-ID": str(TENANT_ID),
            },
        )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# POST /leads — happy path → 201 + LeadResponse
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_lead_201(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Doctor creates a new lead → 201 + LeadResponse."""
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._get_resolver",
        lambda: MagicMock(**{"resolve.return_value": mock_clinic_ctx_doctor}),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/api/v1/vitalia/crm/leads",
            json=CREATE_LEAD_PAYLOAD,
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    assert resp.status_code == 201
    body = resp.json()
    assert "id" in body
    assert body["name"] == "María García"
    assert body["status"] == "new"
    assert body["tenant_id"] == str(TENANT_ID)


# ---------------------------------------------------------------------------
# PATCH /leads/{lead_id} — 404 (Slice 1 — no live DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_lead_404_slice1(
    mock_clinic_ctx_doctor: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PATCH lead returns 404 in Slice 1 (no live DB). Slice 2 will fix."""
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._get_resolver",
        lambda: MagicMock(**{"resolve.return_value": mock_clinic_ctx_doctor}),
    )

    app = _make_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            f"/api/v1/vitalia/crm/leads/{LEAD_ID}",
            json={"status": "contacted"},
            headers={
                "Authorization": VALID_TOKEN,
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
            },
        )

    # Slice 1: always 404 since lead_repo.get_by_id returns None
    assert resp.status_code == 404
