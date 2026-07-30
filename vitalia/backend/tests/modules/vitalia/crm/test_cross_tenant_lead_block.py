# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Tests for cross-tenant isolation on funnel endpoints (SC-4).

Verifies that leads from another tenant return 404 (not 403),
preventing information leakage about whether a lead exists.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

TENANT_A = uuid4()
TENANT_B = uuid4()
LEAD_ID_B = uuid4()  # Lead belonging to TENANT_B
USER_ID = uuid4()


def _mock_context_tenant_a() -> MagicMock:
    """User authenticated as TENANT_A."""
    ctx = MagicMock()
    ctx.user_id = str(USER_ID)
    ctx.tenant_id = TENANT_A
    ctx.clinic_id = uuid4()
    ctx.role = "admin_clinic"
    ctx.email = "admin@tenant-a.test"
    ctx.name = "Admin A"
    return ctx


def _make_app() -> "FastAPI":
    from src.modules.vitalia.crm.api.router import router as crm_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(crm_router, prefix="/api/v1/crm")
    return app


@pytest.fixture(autouse=True)
def _patch_kek(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.modules.vitalia._shared.encryption.kek_client import KEKClient

    mock_kek = MagicMock(spec=KEKClient)
    mock_kek.get_key.return_value = "a" * 64
    monkeypatch.setattr(KEKClient, "from_env", classmethod(lambda cls, *a, **kw: mock_kek))

    # Auth resolves as TENANT_A
    ctx = _mock_context_tenant_a()
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_sync",
        lambda *a, **kw: ctx,
    )


@pytest.mark.asyncio
async def test_get_lead_detail_cross_tenant_returns_404() -> None:
    """SC-4: accessing a lead from another tenant returns 404 (no leak)."""
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    mock_service = AsyncMock(spec=FunnelService)
    # Lead repo returns None because TENANT_A cannot see TENANT_B's leads
    mock_service.get_lead_detail = AsyncMock(return_value=None)

    app = _make_app()

    with patch(
        "src.modules.vitalia.crm.api.router._build_funnel_service",
        return_value=mock_service,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(
                f"/api/v1/crm/leads/{LEAD_ID_B}/detail",
                headers={
                    "Authorization": "Bearer valid-test-token",
                    "X-Tenant-ID": str(TENANT_A),
                },
            )

    # Should be 404, not 403 — no information leakage
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_patch_stage_cross_tenant_returns_404() -> None:
    """SC-4: patching stage of another tenant's lead returns 404."""
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.transition_stage = AsyncMock(return_value=None)

    app = _make_app()

    with patch(
        "src.modules.vitalia.crm.api.router._build_funnel_service",
        return_value=mock_service,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.patch(
                f"/api/v1/crm/leads/{LEAD_ID_B}/stage",
                json={"to_stage": "calificando", "version": 1},
                headers={
                    "Authorization": "Bearer valid-test-token",
                    "X-Tenant-ID": str(TENANT_A),
                },
            )

    assert response.status_code == 404
