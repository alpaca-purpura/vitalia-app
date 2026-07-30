"""Router tests for GET/PATCH /api/v1/lisa/marca/personality.

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import BrandPersonalityDTO

pytestmark = pytest.mark.integration


_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_PERSONALITY_URL = "/api/v1/lisa/marca/personality"

_PERSONALITY_RESPONSE = BrandPersonalityDTO(
    tenant_id=UUID(_TENANT_A),
    personality_profile_id=UUID("11111111-1111-1111-1111-111111111111"),
    archetype="caregiver",
    so_i_speak="Hablo con claridad y empatía.",
    so_i_dont_speak="No uso tecnicismos sin contexto.",
    technical_context="Contexto médico-dental.",
    format_instructions="Frases cortas, lenguaje neutro.",
    identity_anchor="Clínica Bienestar — tu salud primero.",
    domain_context="Salud preventiva LatAm.",
    compiled_at=datetime.now(timezone.utc),
    compiler_version="v2",
)


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


@pytest.mark.asyncio
async def test_get_personality_returns_200(app) -> None:
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_personality.return_value = _PERSONALITY_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _PERSONALITY_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["archetype"] == "caregiver"
    assert data["compiler_version"] == "v2"


@pytest.mark.asyncio
async def test_get_personality_no_user_id_required(app) -> None:
    """GET /personality no requiere X-User-ID (F2 fix)."""
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_personality.return_value = _PERSONALITY_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _PERSONALITY_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_personality_missing_tenant_returns_422(app) -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(_PERSONALITY_URL)
    assert response.status_code == 422
