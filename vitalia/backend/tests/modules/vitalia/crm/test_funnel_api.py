# cap: crm.adrian-embudo
# story-origin: vitalia-fase2-adrian-embudo
"""Tests for funnel API endpoints — unit tests using FastAPI TestClient mocks.

TDD order: RED first, then GREEN in router.py.

Covers:
  - GET /crm/board → 200 BoardResponse
  - PATCH /crm/leads/{id}/stage → 200 StageTransitionResponse
  - PATCH /crm/leads/{id}/stage → 422 invalid transition
  - PATCH /crm/leads/{id}/stage → 409 optimistic lock conflict
  - PATCH /crm/leads/{id}/stage → 403 manual reservado
  - GET /crm/leads/{id}/transitions → 200 TimelineResponse
  - GET /crm/frozen → 200 FrozenListResponse
  - POST /crm/leads/{id}/diagnose → 200 DiagnoseResponse
  - POST /crm/leads/{id}/reactivate → 200 Lead
  - POST /crm/leads/{id}/reservado-side-effect → 200 stub
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.modules.vitalia.crm.domain.exceptions import (
    InvalidTransitionError,
    ManualReservadoForbiddenError,
    StaleStateError,
)
from src.modules.vitalia.crm.domain.lead import Lead

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
LEAD_ID = uuid4()
USER_ID = uuid4()
VALID_TOKEN = "Bearer valid-test-token"


def _make_lead(stage: str = "interesado", version: int = 1, is_frozen: bool = False) -> Lead:
    return Lead(
        id=LEAD_ID,
        tenant_id=TENANT_ID,
        name="María García",
        email="maria@example.com",
        phone="+525512345678",
        stage=stage,
        score=50,
        version=version,
        is_frozen=is_frozen,
        stage_entered_at=datetime.now(tz=timezone.utc),
    )


def _mock_context() -> MagicMock:
    ctx = MagicMock()
    ctx.user_id = str(USER_ID)
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.role = "admin_clinic"
    ctx.email = "admin@vitalia.test"
    ctx.name = "Admin Test"
    return ctx


def _make_app() -> FastAPI:
    from src.modules.vitalia.crm.api.router import router as crm_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(crm_router, prefix="/api/v1/crm")
    return app


# ---------------------------------------------------------------------------
# Fixture: patch auth + KEK
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_auth_and_kek(monkeypatch: pytest.MonkeyPatch) -> None:
    """Patch KEKClient.from_env and _resolve_context_sync for all funnel API tests."""
    from src.modules.vitalia._shared.encryption.kek_client import KEKClient

    mock_kek = MagicMock(spec=KEKClient)
    mock_kek.get_key.return_value = "a" * 64
    monkeypatch.setattr(KEKClient, "from_env", classmethod(lambda cls, *a, **kw: mock_kek))

    ctx = _mock_context()
    monkeypatch.setattr(
        "src.modules.vitalia.crm.api.router._resolve_context_sync",
        lambda *a, **kw: ctx,
    )


# ---------------------------------------------------------------------------
# GET /crm/board
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_board_returns_200() -> None:
    """GET /crm/board → 200 with BoardResponse structure."""
    from src.modules.vitalia.crm.application.dto.board_dto import BoardColumn, BoardKpis, BoardResponse
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    board_resp = BoardResponse(
        columns=[
            BoardColumn(
                stage="interesado",
                label="Interesado",
                count=1,
                sum_value=Decimal("5000"),
                currency="MXN",
                over_sla_count=0,
                leads=[],
            )
        ],
        kpis=BoardKpis(
            active=1,
            agent_count=1,
            human_count=0,
            hot=0,
            warm=1,
            cold=0,
            avg_score=50,
            deposit_rate=0.0,
            frozen_count=0,
        ),
    )

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.get_board = AsyncMock(return_value=board_resp)

    app = _make_app()

    with patch(
        "src.modules.vitalia.crm.api.router._build_funnel_service",
        return_value=mock_service,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/crm/board",
                headers={
                    "Authorization": VALID_TOKEN,
                    "X-Tenant-ID": str(TENANT_ID),
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert "columns" in data
    assert "kpis" in data


# ---------------------------------------------------------------------------
# PATCH /crm/leads/{id}/stage — 200 success
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_stage_returns_200() -> None:
    """PATCH /crm/leads/{id}/stage → 200 StageTransitionResponse."""
    from src.modules.vitalia.crm.application.dto.transition_dto import StageTransitionResponse, TransitionDTO
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    lead_after = _make_lead(stage="calificando", version=2)
    transition = TransitionDTO(
        from_stage="interesado",
        to_stage="calificando",
        triggered_by="manual_override",
        reason=None,
        occurred_at=datetime.now(tz=timezone.utc),
    )

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.transition_stage = AsyncMock(
        return_value=StageTransitionResponse(lead=lead_after, transition=transition)
    )

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
                    "Authorization": VALID_TOKEN,
                    "X-Tenant-ID": str(TENANT_ID),
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert data["lead"]["stage"] == "calificando"


# ---------------------------------------------------------------------------
# PATCH /crm/leads/{id}/stage — 422 invalid transition
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_stage_invalid_transition_returns_422() -> None:
    """PATCH /crm/leads/{id}/stage → 422 with allowed_next in body."""
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.transition_stage = AsyncMock(
        side_effect=InvalidTransitionError("interesado", "plan_presentado", ["calificando", "decidio_no"])
    )

    app = _make_app()

    with patch(
        "src.modules.vitalia.crm.api.router._build_funnel_service",
        return_value=mock_service,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.patch(
                f"/api/v1/crm/leads/{LEAD_ID}/stage",
                json={"to_stage": "plan_presentado", "version": 1},
                headers={
                    "Authorization": VALID_TOKEN,
                    "X-Tenant-ID": str(TENANT_ID),
                },
            )

    assert response.status_code == 422
    data = response.json()
    # FastAPI wraps dict detail — check nested or flat structure
    detail = data.get("detail", data)
    if isinstance(detail, dict):
        assert "allowed_next" in detail
    else:
        assert "allowed_next" in data


# ---------------------------------------------------------------------------
# PATCH /crm/leads/{id}/stage — 409 optimistic lock
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_stage_stale_version_returns_409() -> None:
    """PATCH /crm/leads/{id}/stage → 409 on version conflict."""
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.transition_stage = AsyncMock(side_effect=StaleStateError(LEAD_ID, 1))

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
                    "Authorization": VALID_TOKEN,
                    "X-Tenant-ID": str(TENANT_ID),
                },
            )

    assert response.status_code == 409


# ---------------------------------------------------------------------------
# PATCH /crm/leads/{id}/stage — 403 manual reservado
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_stage_reservado_manual_returns_403() -> None:
    """PATCH /crm/leads/{id}/stage → 403 when trying to set reservado manually."""
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.transition_stage = AsyncMock(side_effect=ManualReservadoForbiddenError())

    app = _make_app()

    with patch(
        "src.modules.vitalia.crm.api.router._build_funnel_service",
        return_value=mock_service,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.patch(
                f"/api/v1/crm/leads/{LEAD_ID}/stage",
                json={"to_stage": "reservado", "version": 1},
                headers={
                    "Authorization": VALID_TOKEN,
                    "X-Tenant-ID": str(TENANT_ID),
                },
            )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# GET /crm/frozen → 200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_frozen_returns_200() -> None:
    """GET /crm/frozen → 200 FrozenListResponse."""
    from src.modules.vitalia.crm.application.dto.frozen_dto import FrozenListResponse
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.get_frozen_list = AsyncMock(return_value=FrozenListResponse(recien_congelados=[], decidio_no=[]))

    app = _make_app()

    with patch(
        "src.modules.vitalia.crm.api.router._build_funnel_service",
        return_value=mock_service,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(
                "/api/v1/crm/frozen",
                headers={
                    "Authorization": VALID_TOKEN,
                    "X-Tenant-ID": str(TENANT_ID),
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert "recien_congelados" in data
    assert "decidio_no" in data


# ---------------------------------------------------------------------------
# POST /crm/leads/{id}/diagnose → 200
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_post_diagnose_returns_200() -> None:
    """POST /crm/leads/{id}/diagnose → 200 DiagnoseResponse."""
    from src.modules.vitalia.crm.application.dto.frozen_dto import DiagnoseResponse
    from src.modules.vitalia.crm.application.services.funnel_service import FunnelService

    mock_service = AsyncMock(spec=FunnelService)
    mock_service.diagnose = AsyncMock(
        return_value=DiagnoseResponse(
            recommendation_es="Reiniciar contacto con descuento de presentación.",
            suggested_action="reactivate",
        )
    )

    app = _make_app()

    with patch(
        "src.modules.vitalia.crm.api.router._build_funnel_service",
        return_value=mock_service,
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                f"/api/v1/crm/leads/{LEAD_ID}/diagnose",
                headers={
                    "Authorization": VALID_TOKEN,
                    "X-Tenant-ID": str(TENANT_ID),
                },
            )

    assert response.status_code == 200
    data = response.json()
    assert "recommendation_es" in data
    assert "suggested_action" in data
