"""Router tests for GET /api/v1/lisa/marca/voice-preview.

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import VoicePreviewDTO

pytestmark = pytest.mark.integration


_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_VOICE_PREVIEW_URL = "/api/v1/lisa/marca/voice-preview"
_PROFILE_ID = UUID("11111111-1111-1111-1111-111111111111")

_VOICE_PREVIEW_RESPONSE = VoicePreviewDTO(
    personality_profile_id=_PROFILE_ID,
    sample_whatsapp="Hola, soy Lisa de Clínica Bienestar.",
    sample_email_reactivation="Estimado paciente, queremos invitarte a tu próximo control.",
    compiler_version="v2",
    cache_hit=False,
    compiled_at=datetime.now(timezone.utc),
)


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


@pytest.mark.asyncio
async def test_get_voice_preview_returns_200(app) -> None:
    """GET /voice-preview retorna 200 + VoicePreviewDTO."""
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_voice_preview.return_value = _VOICE_PREVIEW_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _VOICE_PREVIEW_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    assert response.status_code == 200
    data = response.json()
    assert data["compiler_version"] == "v2"
    assert data["cache_hit"] is False


@pytest.mark.asyncio
async def test_get_voice_preview_no_user_id_required(app) -> None:
    """GET /voice-preview no requiere X-User-ID (F2 fix)."""
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_voice_preview.return_value = _VOICE_PREVIEW_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _VOICE_PREVIEW_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_voice_preview_missing_tenant_returns_422(app) -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(_VOICE_PREVIEW_URL)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_voice_preview_cache_hit_field_present(app) -> None:
    """Response debe incluir campo cache_hit (LRU anti-creep observable)."""
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        cached_response = VoicePreviewDTO(
            personality_profile_id=_PROFILE_ID,
            sample_whatsapp="Hola.",
            sample_email_reactivation="Est.",
            compiler_version="v2",
            cache_hit=True,
            compiled_at=datetime.now(timezone.utc),
        )
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_voice_preview.return_value = cached_response
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _VOICE_PREVIEW_URL,
                headers={"X-Tenant-ID": _TENANT_A},
            )

    data = response.json()
    assert "cache_hit" in data
    assert data["cache_hit"] is True
