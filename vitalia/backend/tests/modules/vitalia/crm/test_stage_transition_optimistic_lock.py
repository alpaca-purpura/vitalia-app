# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Tests for optimistic lock behavior via API (SC-5).

Tests that the PATCH /stage endpoint correctly:
  1. Returns 409 when StaleStateError raised by service
  2. Returns correct version in success response for retry
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.modules.vitalia.crm.domain.exceptions import StaleStateError
from src.modules.vitalia.crm.domain.lead import Lead

TENANT_ID = uuid4()
LEAD_ID = uuid4()
USER_ID = uuid4()


def _make_app() -> "FastAPI":
    from src.modules.vitalia.crm.api.router import router as crm_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(crm_router, prefix="/api/v1/crm")
    return app


@pytest.fixture(autouse=True)
def _patch_auth_kek(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.modules.vitalia._shared.encryption.kek_client import KEKClient

    mock_kek = MagicMock(spec=KEKClient)
    mock_kek.get_key.return_value = "a" * 64
    monkeypatch.setattr(KEKClient, "from_env", classmethod(lambda cls, *a, **kw: mock_kek))

    ctx = MagicMock()
    ctx.user_id = str(USER_ID)
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = uuid4()
    ctx.role = "admin_clinic"
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_sync",
        lambda *a, **kw: ctx,
    )


@pytest.mark.asyncio
async def test_patch_stage_version_1_conflict_returns_409() -> None:
    """SC-5: PATCH /leads/{id}/stage with stale version → 409 Conflict."""
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.transition_stage = AsyncMock(side_effect=StaleStateError(LEAD_ID, expected_version=1))

    app = _make_app()

    with patch(
        "src.modules.vitalia.crm.api.router._build_funnel_service",
        return_value=mock_service,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.patch(
                f"/api/v1/crm/leads/{LEAD_ID}/stage",
                json={"to_stage": "calificando", "version": 1},
                headers={
                    "Authorization": "Bearer valid-test-token",
                    "X-Tenant-ID": str(TENANT_ID),
                },
            )

    assert response.status_code == 409
    data = response.json()
    assert (
        "conflict" in data["detail"].lower()
        or "concurrente" in data["detail"].lower()
        or "409" in str(response.status_code)
    )


@pytest.mark.asyncio
async def test_patch_stage_success_returns_new_version() -> None:
    """SC-5: successful transition returns lead with incremented version."""
    from src.modules.vitalia.crm.application.dto.transition_dto import StageTransitionResponse, TransitionDTO
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    lead_v2 = Lead(
        id=LEAD_ID,
        tenant_id=TENANT_ID,
        name="María García",
        stage="calificando",
        score=50,
        version=2,  # incremented
        stage_entered_at=datetime.now(tz=timezone.utc),
    )

    resp = StageTransitionResponse(
        lead=lead_v2,
        transition=TransitionDTO(
            from_stage="interesado",
            to_stage="calificando",
            triggered_by="manual_override",
            reason=None,
            occurred_at=datetime.now(tz=timezone.utc),
        ),
    )

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.transition_stage = AsyncMock(return_value=resp)

    app = _make_app()

    with patch(
        "src.modules.vitalia.crm.api.router._build_funnel_service",
        return_value=mock_service,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.patch(
                f"/api/v1/crm/leads/{LEAD_ID}/stage",
                json={"to_stage": "calificando", "version": 1},
                headers={
                    "Authorization": "Bearer valid-test-token",
                    "X-Tenant-ID": str(TENANT_ID),
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["lead"]["version"] == 2
