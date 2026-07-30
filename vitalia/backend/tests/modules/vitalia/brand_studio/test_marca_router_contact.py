"""Router tests for GET/PATCH /api/v1/lisa/marca/contact.

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import BrandContactDTO

pytestmark = pytest.mark.integration


_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_CONTACT_URL = "/api/v1/lisa/marca/contact"

_CONTACT_RESPONSE = BrandContactDTO(
    tenant_id=UUID(_TENANT_A),
    public_landing_url="https://clinicabienestar.luana.app",
    website_url="https://clinicabienestar.pe",
    instagram_handle=None,
    tiktok_handle=None,
    facebook_page=None,
    google_business_url=None,
    updated_at=None,
)


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


@pytest.mark.asyncio
async def test_get_contact_returns_200(app) -> None:
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_contact.return_value = _CONTACT_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _CONTACT_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["website_url"] == "https://clinicabienestar.pe"
    assert data["tenant_id"] == _TENANT_A


@pytest.mark.asyncio
async def test_get_contact_no_user_id_required(app) -> None:
    """GET /contact no requiere X-User-ID (F2 fix)."""
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_contact.return_value = _CONTACT_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _CONTACT_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_contact_missing_tenant_returns_422(app) -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(_CONTACT_URL)
    assert response.status_code == 422
