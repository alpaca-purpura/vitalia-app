# cap: observability.api-health-endpoint
"""Integration (ASGI) contract test — GET /api/health endpoint.

Verifica que el endpoint /api/health:
  1. Responde 200 con JSON {"status": "ok", "brand": "vitalia"}
  2. Es accesible sin autenticación (ruta pública en el middleware Clerk)
  3. /health (alias sin prefijo /api) también responde 200

No requiere Postgres ni Clerk — ASGITransport aísla el test.
Ref: capabilities/observability/api-health-endpoint.yaml

downstream-regression-na: brand-local contract test; no cross-brand consumers
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.mark.asyncio
async def test_api_health_returns_200_ok() -> None:
    """GET /api/health → 200 + body {status: ok, brand: vitalia}."""
    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/health")

    assert response.status_code == 200, f"Expected 200 from /api/health, got {response.status_code}: {response.text}"
    body = response.json()
    assert body.get("status") == "ok", f"Expected status=ok, got: {body}"
    assert body.get("brand") == "vitalia", f"Expected brand=vitalia, got: {body}"


@pytest.mark.asyncio
async def test_health_alias_returns_200_ok() -> None:
    """GET /health (alias sin prefijo) → 200 + body {status: ok}."""
    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200, f"Expected 200 from /health, got {response.status_code}: {response.text}"
    body = response.json()
    assert body.get("status") == "ok", f"Expected status=ok in /health, got: {body}"


@pytest.mark.asyncio
async def test_api_health_no_auth_required() -> None:
    """GET /api/health sin header Authorization → sigue respondiendo 200.

    Verifica que la ruta es pública (no pasa por Clerk guard).
    """
    from src.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/health", headers={})

    assert response.status_code == 200, f"/api/health debe ser público (sin auth), got {response.status_code}"
