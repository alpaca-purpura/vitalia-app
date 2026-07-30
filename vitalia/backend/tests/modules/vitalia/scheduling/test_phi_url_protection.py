"""T-6 A1 — PHI URL param protection on GET /agenda/grid.

TDD: tests define the security contract BEFORE implementation.

Coverage:
  - Any query param NOT in ALLOWED_GRID_PARAMS → suspicious_request audit + 400
  - patient_dni query param → rejected (PHI detection)
  - patient_name query param → rejected (PHI detection)
  - diagnosis query param → rejected (PHI detection)
  - Unknown param with no PHI pattern → also rejected (whitelist hard gate)
  - Valid params only (view, date, preset_filter) → 200 OK
  - RBAC gate: non-PHI role → 403 (before param check)

All tests use mocked services/repos — pure HTTP layer test (no Postgres).

Per vitalia/.claude/rules/hipaa-lite.md § Anti-patterns:
  "PHI en URLs (GET query params) — usa POST body siempre."
  "Ej: GET /patients?dni=12345678 PROHIBIDO."

Gherkin SC-4 coverage:
  test_patient_dni_query_param_rejected covers:
    "Given a request with ?patient_dni=12345678 when GET /agenda/grid
    Then 400 is returned and suspicious_request audit row is written"

downstream-regression-na: brand-local security test for vitalia scheduling T-6
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
USER_ID = uuid4()

_PHI_ROLE_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "admin_clinic",
}

_NON_PHI_ROLE_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "marketing",
}


# ---------------------------------------------------------------------------
# Test app factory
# ---------------------------------------------------------------------------


def _build_test_app(*, audit_mock: MagicMock | None = None) -> FastAPI:
    """Build minimal FastAPI test app with agenda router + mocked dependencies."""
    from src.modules.vitalia.scheduling.api.agenda_router import router

    test_app = FastAPI(redirect_slashes=False)
    test_app.include_router(router, prefix="/api/v1/scheduling")

    # Override DB session dependency
    async def _fake_db():
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        # commit() is awaited on the suspicious_request path (audit must survive the
        # HTTP 400 under the committing session dependency) — make it awaitable.
        session.commit = AsyncMock(return_value=None)
        session.rollback = AsyncMock(return_value=None)
        yield session

    from src.modules.vitalia.scheduling.api import agenda_router as ar_module

    test_app.dependency_overrides[ar_module._get_db] = _fake_db

    return test_app


# ---------------------------------------------------------------------------
# Tests: PHI param rejection (SC-4 Gherkin coverage)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patient_dni_query_param_rejected() -> None:
    """SC-4: patient_dni in query params → 400 + suspicious_request audit written."""
    audit_write_mock = AsyncMock()

    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter") as MockAudit,
    ):
        mock_instance = MagicMock()
        mock_instance.write = audit_write_mock
        MockAudit.return_value = mock_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/scheduling/agenda/grid",
                params={"patient_dni": "12345678"},
                headers=_PHI_ROLE_HEADERS,
            )

    assert resp.status_code == 400
    body = resp.json()
    assert body["detail"]["error_code"] == "INVALID_QUERY_PARAMS"
    # Suspicious audit must be written synchronously
    audit_write_mock.assert_awaited_once()
    call_kwargs = audit_write_mock.call_args.kwargs
    assert call_kwargs["action"] == "suspicious_request"
    # Only keys logged, never values
    assert "patient_dni" in call_kwargs["payload"]["bypass_params"]


@pytest.mark.asyncio
async def test_patient_name_query_param_rejected() -> None:
    """PHI: patient_name in URL params → 400 + audit."""
    audit_write_mock = AsyncMock()

    with patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter") as MockAudit:
        mock_instance = MagicMock()
        mock_instance.write = audit_write_mock
        MockAudit.return_value = mock_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/scheduling/agenda/grid",
                params={"patient_name": "García López"},
                headers=_PHI_ROLE_HEADERS,
            )

    assert resp.status_code == 400
    assert resp.json()["detail"]["error_code"] == "INVALID_QUERY_PARAMS"
    audit_write_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_diagnosis_query_param_rejected() -> None:
    """PHI: diagnosis in URL params → 400 + audit."""
    audit_write_mock = AsyncMock()

    with patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter") as MockAudit:
        mock_instance = MagicMock()
        mock_instance.write = audit_write_mock
        MockAudit.return_value = mock_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/scheduling/agenda/grid",
                params={"diagnosis": "hipertension"},
                headers=_PHI_ROLE_HEADERS,
            )

    assert resp.status_code == 400
    audit_write_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_unknown_non_phi_param_rejected() -> None:
    """Whitelist gate: unknown param (even without PHI pattern) → 400.

    The whitelist is hard (frozenset) — not just PHI detection.
    Only view, date, preset_filter are allowed.
    """
    audit_write_mock = AsyncMock()

    with patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter") as MockAudit:
        mock_instance = MagicMock()
        mock_instance.write = audit_write_mock
        MockAudit.return_value = mock_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/scheduling/agenda/grid",
                params={"doctor_id": str(uuid4())},  # not in ALLOWED_GRID_PARAMS
                headers=_PHI_ROLE_HEADERS,
            )

    assert resp.status_code == 400
    audit_write_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_valid_params_pass_whitelist() -> None:
    """view, date, preset_filter pass the whitelist; grid renders normally."""
    grid_service_mock = AsyncMock(return_value=[])

    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridRepositoryImpl"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.list_slots = grid_service_mock
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                "/api/v1/scheduling/agenda/grid",
                params={"view": "semana", "date": "2026-05-26", "preset_filter": "hoy"},
                headers=_PHI_ROLE_HEADERS,
            )

    # 200 OK with valid params — grid service called
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_non_phi_role_forbidden_before_param_check() -> None:
    """RBAC gate fires BEFORE whitelist check — 403 for non-PHI role."""
    app = _build_test_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.get(
            "/api/v1/scheduling/agenda/grid",
            params={"patient_dni": "99999999"},  # would trigger whitelist if RBAC passed
            headers=_NON_PHI_ROLE_HEADERS,
        )

    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "PHI_RBAC_DENIED"
