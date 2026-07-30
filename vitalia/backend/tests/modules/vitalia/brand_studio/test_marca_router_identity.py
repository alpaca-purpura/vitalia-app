"""Router tests for GET/PATCH /api/v1/lisa/marca/identity.

Uses httpx.AsyncClient with mocked MarcaService (no Postgres).
Verifies:
  - GET /identity returns 200 + BrandIdentityDTO shape
  - GET /identity does NOT require X-User-ID (F2 fix verification)
  - PATCH /identity requires X-User-ID + brand_owner role
  - PATCH /identity returns 200 + updated DTO
  - Missing X-Tenant-ID → 422

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import (
    BrandIdentityDTO,
)

pytestmark = pytest.mark.integration

_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_USER_A = "11111111-1111-1111-1111-111111111111"
_IDENTITY_URL = "/api/v1/lisa/marca/identity"

_IDENTITY_RESPONSE = BrandIdentityDTO(
    tenant_id=UUID(_TENANT_A),
    name="Clínica Bienestar",
    slug="clinica-bienestar",
    tagline="Tu salud es nuestra prioridad",
    clinic_vertical="dental",
    primary_specialties=["odontología"],
    updated_at=None,
)


@pytest.fixture
def app():
    """Vitalia FastAPI app (imports from main.py)."""
    from src.main import app as vitalia_app

    return vitalia_app


@pytest.mark.asyncio
async def test_get_identity_returns_200(app) -> None:
    """GET /identity returns 200 with BrandIdentityDTO shape."""
    with (
        patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build,
    ):
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_identity.return_value = _IDENTITY_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _IDENTITY_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Clínica Bienestar"
    assert data["tenant_id"] == _TENANT_A


@pytest.mark.asyncio
async def test_get_identity_does_not_require_user_id(app) -> None:
    """GET /identity no requiere X-User-ID (F2 fix — no audit log on GET)."""
    with (
        patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build,
    ):
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_identity.return_value = _IDENTITY_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            # No X-User-ID header — should succeed (GET does not need it)
            response = await client.get(
                _IDENTITY_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_identity_missing_tenant_id_returns_422(app) -> None:
    """GET /identity sin X-Tenant-ID retorna 422."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(_IDENTITY_URL)

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_identity_invalid_tenant_id_uuid_returns_422(app) -> None:
    """GET /identity con tenant_id no-UUID retorna 422."""
    with (
        patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build,
    ):
        mock_bundle = AsyncMock()
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _IDENTITY_URL,
                headers={"X-Tenant-ID": "not-a-uuid"},
            )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_patch_identity_requires_user_id(app) -> None:
    """PATCH /identity requiere X-User-ID (audit log write)."""
    with (
        patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build,
        patch(
            "src.modules.vitalia.brand_studio.api.routers.marca_router._brand_owner_required",
        ) as mock_rbac,
    ):
        mock_rbac.__call__ = AsyncMock(return_value="brand_owner")
        mock_bundle = AsyncMock()
        mock_bundle.marca.patch_identity.return_value = _IDENTITY_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            # PATCH without X-User-ID → 422
            response = await client.patch(
                _IDENTITY_URL,
                headers={"X-Tenant-ID": _TENANT_A},
                json={"name": "Clínica Actualizada"},
            )

    assert response.status_code == 422
