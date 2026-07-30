# cap: scheduling.valeria-agenda
"""Regression tests — clinic `owner` role allowed on scheduling PHI endpoints.

Bug origin (vitalia-bugfix-agenda-actor-headers-422, T-2, Bug 1):
  The clinic OWNER (``user_tenants.role = owner``) received HTTP 403 on their own
  agenda. ``ALLOWED_PHI_ROLES`` listed only
  {valeria_assistant, doctor, nurse, admin_clinic} — ``owner`` was missing.

Chris ratified adding ``owner`` (legitimate clinic role; the agenda is PHI-masked
server-side and the dual-filter tenant+clinic + audit log stay mandatory).

SSoT: the role frozenset was duplicated across ``agenda_router.py``
(``ALLOWED_PHI_ROLES``) and ``notify_router.py`` (``_PHI_ROLES``). The fix
consolidates them into ``scheduling/api/rbac.py::SCHEDULING_PHI_ROLES`` so adding a
role happens in ONE place. These tests pin: owner allowed, disallowed role still 403,
both routers consistent.

Per .claude/rules/tdd-mandatory.md (regression test reproduces bug FIRST).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
USER_ID = uuid4()


def _headers(role: str) -> dict[str, str]:
    return {
        "X-Tenant-ID": str(TENANT_ID),
        "X-Clinic-ID": str(CLINIC_ID),
        "X-User-ID": str(USER_ID),
        "X-User-Role": role,
    }


def _build_agenda_app() -> FastAPI:
    from src.modules.vitalia.scheduling.api import agenda_router as ar_module
    from src.modules.vitalia.scheduling.api.agenda_router import router

    test_app = FastAPI(redirect_slashes=False)
    test_app.include_router(router, prefix="/api/v1/scheduling")

    async def _fake_db():  # noqa: ANN202
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        yield session

    test_app.dependency_overrides[ar_module._get_db] = _fake_db
    return test_app


# ---------------------------------------------------------------------------
# Bug 1 — owner allowed on the agenda grid (was 403)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_owner_role_allowed_on_agenda_grid() -> None:
    """owner + valid params → NOT 403 (200, grid renders empty)."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridRepositoryImpl"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc = MagicMock()
        svc.list_slots = AsyncMock(return_value=[])
        MockSvc.return_value = svc

        app = _build_agenda_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/scheduling/agenda/grid",
                params={"view": "semana", "date": "2026-06-15"},
                headers=_headers("owner"),
            )

    assert resp.status_code != 403, "owner must NOT be denied on their own agenda"
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_disallowed_role_still_forbidden_on_agenda_grid() -> None:
    """Non-clinical role (marketing) still gets 403 — fix does not weaken RBAC."""
    app = _build_agenda_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get(
            "/api/v1/scheduling/agenda/grid",
            params={"view": "semana", "date": "2026-06-15"},
            headers=_headers("marketing"),
        )
    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "PHI_RBAC_DENIED"


@pytest.mark.asyncio
async def test_existing_clinical_roles_still_allowed() -> None:
    """doctor/nurse/admin_clinic/valeria_assistant remain allowed (no regression)."""
    for role in ("doctor", "nurse", "admin_clinic", "valeria_assistant"):
        with (
            patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridService") as MockSvc,
            patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridRepositoryImpl"),
            patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
        ):
            svc = MagicMock()
            svc.list_slots = AsyncMock(return_value=[])
            MockSvc.return_value = svc

            app = _build_agenda_app()
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.get(
                    "/api/v1/scheduling/agenda/grid",
                    params={"view": "semana", "date": "2026-06-15"},
                    headers=_headers(role),
                )
        assert resp.status_code != 403, f"clinical role {role} must stay allowed"


# ---------------------------------------------------------------------------
# SSoT — both scheduling routers share ONE role frozenset
# ---------------------------------------------------------------------------


def test_scheduling_phi_roles_is_single_ssot() -> None:
    """agenda_router + notify_router consume the same SCHEDULING_PHI_ROLES constant."""
    from src.modules.vitalia.scheduling.api import agenda_router, notify_router
    from src.modules.vitalia.scheduling.api.rbac import SCHEDULING_PHI_ROLES

    assert "owner" in SCHEDULING_PHI_ROLES, "owner must be in the scheduling PHI roles SSoT"
    # Both routers reference the same frozenset object (no divergent duplicate).
    assert agenda_router.ALLOWED_PHI_ROLES is SCHEDULING_PHI_ROLES
    assert notify_router._PHI_ROLES is SCHEDULING_PHI_ROLES


@pytest.mark.asyncio
async def test_owner_allowed_on_notify_router() -> None:
    """owner also allowed on POST /appointments/{id}/notify (consistency)."""
    from src.modules.vitalia.scheduling.api import notify_router as nr_module
    from src.modules.vitalia.scheduling.api.notify_router import router

    test_app = FastAPI(redirect_slashes=False)
    test_app.include_router(router, prefix="/api/v1/scheduling")

    async def _fake_session():  # noqa: ANN202
        yield MagicMock()

    test_app.dependency_overrides[nr_module.get_async_session_committing] = _fake_session

    notify_svc = MagicMock()
    notify_svc.send_notification = AsyncMock(return_value=None)

    with (
        patch.object(nr_module, "_make_notify_service", return_value=notify_svc),
        patch.object(nr_module, "GrowthStudioEmitter") as MockEmitter,
    ):
        emitter = MagicMock()
        emitter.emit_event = AsyncMock(return_value=None)
        MockEmitter.return_value = emitter

        async with AsyncClient(transport=ASGITransport(app=test_app), base_url="http://test") as client:
            resp = await client.post(
                f"/api/v1/scheduling/appointments/{uuid4()}/notify",
                json={"template_id": "recordatorio_24h", "channel": "whatsapp", "locale": "es"},
                headers=_headers("owner"),
            )

    assert resp.status_code != 403, "owner must NOT be denied on notify"
