"""Router tests for GET/PATCH /api/v1/lisa/marca/visuals.

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
T-2 acceptance A6 verifier references this file.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import BrandVisualsDTO

pytestmark = pytest.mark.integration


_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_USER_A = "11111111-1111-1111-1111-111111111111"
_VISUALS_URL = "/api/v1/lisa/marca/visuals"

_VISUALS_RESPONSE = BrandVisualsDTO(
    tenant_id=UUID(_TENANT_A),
    primary_color="#01B2F8",
    accent_color="#7B2D91",
    background_color=None,
    text_primary_color=None,
    font_heading="Inter",
    font_body="Inter",
    logo_url=None,
    updated_at=None,
)


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


@pytest.mark.asyncio
async def test_get_visuals_returns_200(app) -> None:
    """GET /visuals retorna 200 + BrandVisualsDTO."""
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_visuals.return_value = _VISUALS_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _VISUALS_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["primary_color"] == "#01B2F8"
    assert data["tenant_id"] == _TENANT_A


@pytest.mark.asyncio
async def test_get_visuals_no_user_id_required(app) -> None:
    """GET /visuals no requiere X-User-ID (F2 fix)."""
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_visuals.return_value = _VISUALS_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _VISUALS_URL,
                headers={"X-Tenant-ID": _TENANT_A},
                # No X-User-ID — should succeed
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_visuals_missing_tenant_id_returns_422(app) -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(_VISUALS_URL)
    assert response.status_code == 422
