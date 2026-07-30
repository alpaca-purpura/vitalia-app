# cap: lisa.servicios
"""Cross-tenant isolation tests for /api/v1/offer/servicios (T-2 § 8).

Tenant A asking for a resource that belongs to tenant B → the service returns
None (its queries filter tenant_id), and the API maps that to 404 — NEVER 403
(no existence leak) and NEVER the foreign row's body. Pins the HTTP mapping of
service-None → 404 for reads, detail, patch, activate and sub-resource reads.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

pytestmark = pytest.mark.integration

_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_OWNER = "11111111-1111-1111-1111-111111111111"
_BASE = "/api/v1/offer/servicios"
_FOREIGN_OFFER = uuid4()  # belongs to tenant B


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


def _patch():
    return patch("src.modules.vitalia.offer.api.servicios_router._build_service")


def _none_catalog() -> AsyncMock:
    """Bundle whose catalog returns None for every single-resource lookup."""
    bundle = AsyncMock()
    bundle.catalog.get_service.return_value = None
    bundle.catalog.patch_service.return_value = None
    bundle.catalog.set_active.return_value = None
    bundle.sales_brief.get.return_value = None
    bundle.specialists.list_for_offer.return_value = []
    bundle.proof.list_cases.return_value = []
    bundle.proof.list_testimonials.return_value = []
    return bundle


@pytest.mark.asyncio
async def test_get_detail_foreign_tenant_returns_404_no_leak(app) -> None:
    with _patch() as mock_build:
        mock_build.return_value = _none_catalog()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(f"{_BASE}/{_FOREIGN_OFFER}", headers={"X-Tenant-ID": _TENANT_A})
    assert resp.status_code == 404
    # No foreign row body leaked.
    assert "public_name" not in resp.json()


@pytest.mark.asyncio
async def test_patch_foreign_tenant_returns_404(app) -> None:
    with _patch() as mock_build:
        mock_build.return_value = _none_catalog()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.patch(
                f"{_BASE}/{_FOREIGN_OFFER}",
                headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _OWNER, "X-User-Role": "owner"},
                json={"public_name": "hack"},
            )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_activate_foreign_tenant_returns_404(app) -> None:
    with _patch() as mock_build:
        mock_build.return_value = _none_catalog()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"{_BASE}/{_FOREIGN_OFFER}/activate",
                headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _OWNER, "X-User-Role": "owner"},
                json={"is_active": True},
            )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_foreign_tenant_returns_404(app) -> None:
    with _patch() as mock_build:
        mock_build.return_value = _none_catalog()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.delete(
                f"{_BASE}/{_FOREIGN_OFFER}",
                headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _OWNER, "X-User-Role": "owner"},
            )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_specialist_link_foreign_roster_returns_404(app) -> None:
    """Linking a doctor outside tenant A's roster → DoctorNotInRosterError → 404 (no leak)."""
    from src.modules.vitalia.offer.application.services.specialist_link_service import DoctorNotInRosterError

    bundle = _none_catalog()
    bundle.specialists.link.side_effect = DoctorNotInRosterError("not in roster")
    with _patch() as mock_build:
        mock_build.return_value = bundle
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                f"{_BASE}/{_FOREIGN_OFFER}/specialists",
                headers={
                    "X-Tenant-ID": _TENANT_A,
                    "X-User-ID": _OWNER,
                    "X-User-Role": "owner",
                    "X-Clinic-ID": "22222222-2222-2222-2222-222222222222",
                },
                json={"doctor_id": str(uuid4())},
            )
    assert resp.status_code == 404
    assert "doctor_id" not in resp.json()
