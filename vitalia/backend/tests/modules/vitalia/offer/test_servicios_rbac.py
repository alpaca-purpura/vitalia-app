# cap: lisa.servicios
"""RBAC tests for /api/v1/offer/servicios writes (T-2 § 8, RN-7).

Mutating endpoints (create/patch/activate/delete/specialists/cases/testimonials/
sales-brief/knowledge) require owner OR admin_clinic via require_brand_owner_access().
Every other role (doctor, nurse, staff, sales, marketing, patient, empty) → 403
with error_code BRAND_OWNER_RBAC_DENIED. The RBAC dependency reads X-User-Role
directly so these tests exercise the REAL dependency (no mock of the guard).

Reads (GET) stay open to any authenticated tenant caller — not covered here.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.integration

_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_USER_ID = "11111111-1111-1111-1111-111111111111"
_CLINIC_ID = "22222222-2222-2222-2222-222222222222"
_BASE = "/api/v1/offer/servicios"
_OFFER = uuid4()

_DENIED_ROLES = ["doctor", "nurse", "staff", "sales", "marketing", "patient", ""]


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


def _patch():
    return patch("src.modules.vitalia.offer.api.servicios_router._build_service")


@pytest.mark.asyncio
@pytest.mark.parametrize("role", _DENIED_ROLES)
async def test_create_custom_denied_for_non_owner_roles(app, role: str) -> None:
    with _patch() as mock_build:
        mock_build.return_value = AsyncMock()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"{_BASE}/custom",
                headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _USER_ID, "X-User-Role": role},
                json={"public_name": "X", "price": "10", "currency": "PEN", "modality": "unica", "category": None},
            )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "BRAND_OWNER_RBAC_DENIED"


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["doctor", "staff", "patient"])
async def test_patch_denied_for_non_owner_roles(app, role: str) -> None:
    with _patch() as mock_build:
        mock_build.return_value = AsyncMock()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                f"{_BASE}/{_OFFER}",
                headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _USER_ID, "X-User-Role": role},
                json={"public_name": "Y"},
            )
    assert resp.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["nurse", "marketing"])
async def test_activate_denied_for_non_owner_roles(app, role: str) -> None:
    with _patch() as mock_build:
        mock_build.return_value = AsyncMock()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"{_BASE}/{_OFFER}/activate",
                headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _USER_ID, "X-User-Role": role},
                json={"is_active": True},
            )
    assert resp.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["doctor", "sales"])
async def test_delete_denied_for_non_owner_roles(app, role: str) -> None:
    with _patch() as mock_build:
        mock_build.return_value = AsyncMock()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(
                f"{_BASE}/{_OFFER}",
                headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _USER_ID, "X-User-Role": role},
            )
    assert resp.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["staff", "patient"])
async def test_specialist_link_denied_for_non_owner_roles(app, role: str) -> None:
    with _patch() as mock_build:
        mock_build.return_value = AsyncMock()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"{_BASE}/{_OFFER}/specialists",
                headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _USER_ID, "X-User-Role": role},
                json={"doctor_id": str(uuid4())},
            )
    assert resp.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["doctor", "nurse"])
async def test_case_create_denied_for_non_owner_roles(app, role: str) -> None:
    with _patch() as mock_build:
        mock_build.return_value = AsyncMock()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"{_BASE}/{_OFFER}/cases",
                headers={
                    "X-Tenant-ID": _TENANT_A,
                    "X-User-ID": _USER_ID,
                    "X-User-Role": role,
                    "X-Clinic-ID": _CLINIC_ID,
                },
                json={
                    "before_asset_url": "https://x/b.jpg",
                    "after_asset_url": "https://x/a.jpg",
                    "consent_signed": True,
                },
            )
    assert resp.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize("role", ["staff", "marketing"])
async def test_sales_brief_patch_denied_for_non_owner_roles(app, role: str) -> None:
    with _patch() as mock_build:
        mock_build.return_value = AsyncMock()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                f"{_BASE}/{_OFFER}/sales-brief",
                headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _USER_ID, "X-User-Role": role},
                json={"keywords": ["sonrisa"]},
            )
    assert resp.status_code == 403
