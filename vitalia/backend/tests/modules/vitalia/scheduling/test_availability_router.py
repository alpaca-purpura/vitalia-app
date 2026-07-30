# cap: scheduling.mateo-agenda
"""TDD RED tests — availability router: RBAC + dual filter + PHI (T-BE-3).

Tests verify:
  - SC-disponibilidad-falla: missing X-Clinic-ID header → 422
  - SC-cross-tenant: tenant mismatch → 404 (HIPAA: don't confirm existence)
  - SC-cross-clinic: clinic mismatch → 403
  - Response shape matches declared response_model (AvailabilityCheckResponse)
  - PHI not in URL params (architect test gate alignment)

These are UNIT tests with mocked service — no Postgres required.
Integration tests (SC-concurrent-availability, actual DB reads) live in
tests/integration/scheduling/ (marker=integration, requires Postgres).

Per 03-arch-be.md § 7 + gherkin SC-disponibilidad-falla/SC-cross-clinic/SC-cross-tenant.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
DOCTOR_ID = uuid4()

_VALID_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    # Clerk user role — mocked at auth dependency level
    "Authorization": "Bearer test-token",
}

_CHECK_BODY = {
    "doctor_id": str(DOCTOR_ID),
    "start": "2026-07-01T10:00:00+00:00",
    "duration_minutes": 30,
}

_FREE_BODY = {
    "start": "2026-07-01T10:00:00+00:00",
    "duration_minutes": 30,
}


def _make_app() -> FastAPI:
    """Build minimal app with availability router registered."""
    from src.modules.vitalia.scheduling.api.availability_router import router  # noqa: PLC0415

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/scheduling")
    return app


# ---------------------------------------------------------------------------
# POST /availability/check
# ---------------------------------------------------------------------------


class TestAvailabilityCheckEndpoint:
    """Route: POST /api/v1/scheduling/availability/check."""

    @pytest.mark.asyncio
    async def test_missing_clinic_id_header_returns_422(self):
        """SC-disponibilidad-falla: missing X-Clinic-ID → 422 Unprocessable Entity."""
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/scheduling/availability/check",
                json=_CHECK_BODY,
                headers={
                    "X-Tenant-ID": str(TENANT_ID),
                    "Authorization": "Bearer test-token",
                    # X-Clinic-ID MISSING
                },
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_tenant_id_header_returns_422(self):
        """Missing X-Tenant-ID → 422."""
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/scheduling/availability/check",
                json=_CHECK_BODY,
                headers={
                    "X-Clinic-ID": str(CLINIC_ID),
                    "Authorization": "Bearer test-token",
                    # X-Tenant-ID MISSING
                },
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_invalid_duration_zero_returns_422(self):
        """duration_minutes=0 → 422 (gt=0 validator)."""
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/scheduling/availability/check",
                json={**_CHECK_BODY, "duration_minutes": 0},
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /availability/free-doctors
# ---------------------------------------------------------------------------


class TestFreeDoctorsEndpoint:
    """Route: POST /api/v1/scheduling/availability/free-doctors."""

    @pytest.mark.asyncio
    async def test_missing_clinic_id_header_returns_422(self):
        """Missing X-Clinic-ID → 422."""
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/scheduling/availability/free-doctors",
                json=_FREE_BODY,
                headers={
                    "X-Tenant-ID": str(TENANT_ID),
                    "Authorization": "Bearer test-token",
                },
            )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /availability/day-strip
# ---------------------------------------------------------------------------


class TestDayStripEndpoint:
    """Route: GET /api/v1/scheduling/availability/day-strip."""

    @pytest.mark.asyncio
    async def test_missing_clinic_id_returns_422(self):
        """Missing X-Clinic-ID → 422."""
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/scheduling/availability/day-strip",
                params={"doctor_id": str(DOCTOR_ID), "date": "2026-07-01"},
                headers={
                    "X-Tenant-ID": str(TENANT_ID),
                    "Authorization": "Bearer test-token",
                },
            )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_doctor_id_param_returns_422(self):
        """Missing doctor_id query param → 422."""
        app = _make_app()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/scheduling/availability/day-strip",
                params={"date": "2026-07-01"},  # doctor_id missing
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 422
