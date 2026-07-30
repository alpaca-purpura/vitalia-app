"""Router tests for GET/POST/DELETE /api/v1/lisa/marca/trust-signals.

T-3 F1 — vitalia-fase2-lisa-marca (F2-S7).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient

from src.modules.vitalia.brand_studio.api.dtos.marca_dtos import TrustSignalDTO

pytestmark = pytest.mark.integration


_TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
_USER_A = "11111111-1111-1111-1111-111111111111"
_TRUST_SIGNALS_URL = "/api/v1/lisa/marca/trust-signals"

_SIGNAL = TrustSignalDTO(
    id=UUID("eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
    tenant_id=UUID(_TENANT_A),
    label="DIGESA",
    catalog_code="DIGESA",
    logo_url=None,
    issued_year=2024,
    is_seed=True,
)

_LIST_RESPONSE = [_SIGNAL]


@pytest.fixture
def app():
    from src.main import app as vitalia_app

    return vitalia_app


@pytest.mark.asyncio
async def test_get_trust_signals_returns_200(app) -> None:
    """GET /trust-signals retorna 200 + TrustSignalsListDTO."""
    with patch("src.modules.vitalia.brand_studio.api.routers.marca_router._build_service") as mock_build:
        mock_bundle = AsyncMock()
        mock_bundle.marca.get_trust_signals.return_value = _LIST_RESPONSE
        mock_build.return_value = mock_bundle

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get(
                _TRUST_SIGNALS_URL,
                headers={
                    "X-Tenant-ID": _TENANT_A,
                    "X-User-ID": _USER_A,
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["label"] == "DIGESA"


@pytest.mark.asyncio
async def test_get_trust_signals_missing_tenant_returns_422(app) -> None:
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            _TRUST_SIGNALS_URL,
            headers={"X-User-ID": _USER_A},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_trust_signal_missing_tenant_returns_422(app) -> None:
    """POST /trust-signals sin X-Tenant-ID → 422."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            _TRUST_SIGNALS_URL,
            json={"label": "DIGESA", "catalog_code": "DIGESA"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_trust_signal_missing_tenant_returns_422(app) -> None:
    """DELETE /trust-signals/{id} sin X-Tenant-ID → 422."""
    signal_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            f"{_TRUST_SIGNALS_URL}/{signal_id}",
        )
    assert response.status_code == 422
