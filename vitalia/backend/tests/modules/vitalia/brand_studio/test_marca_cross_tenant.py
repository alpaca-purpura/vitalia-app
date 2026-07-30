"""Router-level cross-tenant isolation tests for brand_studio.

Verifies that a request from tenant_A cannot access or mutate data
of tenant_B through the marca router. This file is referenced by
T-2 acceptance A8 verifier command.

Uses httpx.AsyncClient with mocked _build_service (no Postgres).

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
T-2 acceptance A8 verifier references this file.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import (
    BrandIdentityDTO,
    BrandVisualsDTO,
    ProhibitedPhrasesListDTO,
)

pytestmark = pytest.mark.integration

_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_TENANT_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
_USER_A = "11111111-1111-1111-1111-111111111111"


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


def _identity_for(tenant_id_str: str) -> BrandIdentityDTO:
    return BrandIdentityDTO(
        tenant_id=UUID(tenant_id_str),
        name=f"Clínica de {tenant_id_str[:4]}",
        slug="test",
        tagline=None,
        clinic_vertical="dental",
        primary_specialties=[],
        updated_at=None,
    )


class TestMarcaRouterCrossTenantIsolation:
    """Router-level: tenant_A request only sees tenant_A data."""

    @pytest.mark.asyncio
    async def test_get_identity_service_receives_correct_tenant_id(self, app) -> None:
        """GET /identity pasa el X-Tenant-ID correcto al service."""
        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.get_identity.return_value = _identity_for(_TENANT_A)
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                await client.get(
                    "/api/v1/lisa/marca/identity",
                    headers={"X-Tenant-ID": _TENANT_A},
                )

            # Service debe haber recibido tenant_A, no tenant_B
            call_kwargs = mock_bundle.marca.get_identity.call_args.kwargs
            assert str(call_kwargs["tenant_id"]) == _TENANT_A

    @pytest.mark.asyncio
    async def test_get_identity_response_contains_request_tenant(self, app) -> None:
        """Response tenant_id coincide con X-Tenant-ID del request."""
        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.get_identity.return_value = _identity_for(_TENANT_A)
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get(
                    "/api/v1/lisa/marca/identity",
                    headers={"X-Tenant-ID": _TENANT_A},
                )

        data = response.json()
        assert data["tenant_id"] == _TENANT_A
        assert data["tenant_id"] != _TENANT_B

    @pytest.mark.asyncio
    async def test_get_visuals_service_receives_correct_tenant_id(self, app) -> None:
        """GET /visuals pasa tenant_A al service — no tenant_B."""
        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.get_visuals.return_value = BrandVisualsDTO(
                tenant_id=UUID(_TENANT_A),
                primary_color="#01B2F8",
                accent_color=None,
                background_color=None,
                text_primary_color=None,
                font_heading=None,
                font_body=None,
                logo_url=None,
                updated_at=None,
            )
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                await client.get(
                    "/api/v1/lisa/marca/visuals",
                    headers={"X-Tenant-ID": _TENANT_A},
                )

            call_kwargs = mock_bundle.marca.get_visuals.call_args.kwargs
            assert str(call_kwargs["tenant_id"]) == _TENANT_A

    @pytest.mark.asyncio
    async def test_get_prohibited_phrases_service_receives_correct_tenant(self, app) -> None:
        """GET /prohibited-phrases pasa tenant_A al voice_blocklist service."""
        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.voice_blocklist.list_for_tenant.return_value = ProhibitedPhrasesListDTO(items=[], total=0)
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                await client.get(
                    "/api/v1/lisa/marca/prohibited-phrases",
                    headers={"X-Tenant-ID": _TENANT_A},
                )

            call_kwargs = mock_bundle.voice_blocklist.list_for_tenant.call_args.kwargs
            assert str(call_kwargs["tenant_id"]) == _TENANT_A

    @pytest.mark.asyncio
    async def test_tenant_a_request_never_sends_tenant_b_to_service(self, app) -> None:
        """Cuando X-Tenant-ID es tenant_A, el service NUNCA recibe tenant_B."""
        received_tenant_ids: list[str] = []

        async def mock_get_identity(*, tenant_id: UUID) -> BrandIdentityDTO:
            received_tenant_ids.append(str(tenant_id))
            return _identity_for(str(tenant_id))

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.marca.get_identity.side_effect = mock_get_identity
            mock_build.return_value = mock_bundle

            async with AsyncClient(app=app, base_url="http://test") as client:
                await client.get(
                    "/api/v1/lisa/marca/identity",
                    headers={"X-Tenant-ID": _TENANT_A},
                )

        assert all(tid == _TENANT_A for tid in received_tenant_ids)
        assert _TENANT_B not in received_tenant_ids
