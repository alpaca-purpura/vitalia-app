"""T-3 sub-bug #1 — GET /prohibited-phrases: X-User-ID opcional.

El browser real (fetchClient) NUNCA inyecta X-User-ID en este GET → 422 hoy
(B6 del re-repro 2026-06-02). El endpoint es un read tenant+país: NO audita,
NO usa user_id en el body. El header debe ser opcional.

X-Tenant-ID SIGUE required (tenant-isolation raíz rule). response_model=
se MANTIENE (arch test test_response_model_required.py + PII allowlist).

RED antes del fix: GET sin X-User-ID → 422 (header required).
GREEN tras fix: GET sin X-User-ID → 200; X-Tenant-ID inválido → 422.

Pure-app (httpx + AsyncMock _build_service) — NO requiere Postgres.

Story: estabilizar-harness-e2e-lisa-marca / T-3 (A1 + A2)
cap: brand_studio.lisa-marca
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import ProhibitedPhrasesListDTO

# Importa src.main (Settings env) → marca integration para auto-skip sin Postgres/env,
# consistente con los demás test_marca_router_*.py de este módulo.
pytestmark = pytest.mark.integration

_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_USER_A = "11111111-1111-1111-1111-111111111111"
_PROHIBITED_URL = "/api/v1/lisa/marca/prohibited-phrases"


def _empty_phrases_dto() -> ProhibitedPhrasesListDTO:
    """Minimal valid ProhibitedPhrasesListDTO (empty list)."""
    return ProhibitedPhrasesListDTO(items=[], total=0)


@pytest.fixture
def app():  # noqa: ANN201
    """Vitalia FastAPI app instance."""
    from src.main import app as vitalia_app

    return vitalia_app


@pytest.mark.asyncio
class TestProhibitedPhrasesOptionalHeader:
    """GET /prohibited-phrases — X-User-ID opcional, X-Tenant-ID required."""

    async def test_prohibited_phrases_no_user_id(self, app) -> None:
        """GET sin X-User-ID → 200 (RED contra 422 actual).

        Reproduce el contrato real del browser: fetchClient solo manda X-Tenant-ID.
        """
        from httpx import ASGITransport, AsyncClient

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.voice_blocklist.list_for_tenant.return_value = _empty_phrases_dto()
            mock_build.return_value = mock_bundle

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    _PROHIBITED_URL,
                    headers={"X-Tenant-ID": _TENANT_A},  # NO X-User-ID
                )

        assert response.status_code == 200, (
            f"GET sin X-User-ID debe responder 200 (header opcional). Got {response.status_code}: {response.text}"
        )

    async def test_prohibited_phrases_with_user_id_still_200(self, app) -> None:
        """GET con X-User-ID → 200 (no regresión back-compat)."""
        from httpx import ASGITransport, AsyncClient

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.voice_blocklist.list_for_tenant.return_value = _empty_phrases_dto()
            mock_build.return_value = mock_bundle

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get(
                    _PROHIBITED_URL,
                    headers={"X-Tenant-ID": _TENANT_A, "X-User-ID": _USER_A},
                )

        assert response.status_code == 200

    async def test_prohibited_phrases_bad_tenant(self, app) -> None:
        """GET con X-Tenant-ID inválido (no-UUID) → 422 (tenant-isolation intacta)."""
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                _PROHIBITED_URL,
                headers={"X-Tenant-ID": "not-a-uuid"},
            )

        assert response.status_code == 422, (
            f"X-Tenant-ID inválido debe responder 422 (tenant-isolation). Got {response.status_code}"
        )

    async def test_prohibited_phrases_no_tenant_header(self, app) -> None:
        """GET sin X-Tenant-ID → 422 (X-Tenant-ID sigue required)."""
        from httpx import ASGITransport, AsyncClient

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(_PROHIBITED_URL)  # ningún header

        assert response.status_code == 422, (
            f"GET sin X-Tenant-ID debe responder 422 (header required). Got {response.status_code}"
        )

    async def test_prohibited_phrases_passes_tenant_not_user(self, app) -> None:
        """El service recibe tenant_id; user_id NO se propaga al service (read tenant+país)."""
        from httpx import ASGITransport, AsyncClient

        with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
            mock_bundle = AsyncMock()
            mock_bundle.voice_blocklist.list_for_tenant.return_value = _empty_phrases_dto()
            mock_build.return_value = mock_bundle

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                await client.get(_PROHIBITED_URL, headers={"X-Tenant-ID": _TENANT_A})

            call_kwargs = mock_bundle.voice_blocklist.list_for_tenant.call_args.kwargs
            assert call_kwargs["tenant_id"] == UUID(_TENANT_A)
            assert "user_id" not in call_kwargs, "user_id no debe propagarse al service (read tenant+país)"
