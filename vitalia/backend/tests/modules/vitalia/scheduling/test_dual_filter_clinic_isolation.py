"""T-6 A2 — Cross-clinic isolation: GET /appointments/{id} returns 404 (NOT 403).

TDD: tests define the HIPAA-lite cross-clinic security contract.

Per vitalia/.claude/rules/hipaa-lite.md:
  "Cross-clinic query bloqueada: request con tenant_id_A + clinic_id_X
  siendo user de clinic_id_Y mismo tenant → 403."

IMPORTANT: 03-arch § 5 overrides hipaa-lite.md general guidance for the
drawer endpoint specifically:
  "Cross-clinic returns 404 (NOT 403 — HIPAA-lite substrate:
  don't confirm existence to other clinic)."

This is intentional: responding with 403 would confirm the appointment exists
(just forbidden), which is an information leak. 404 hides existence entirely.

Gherkin SC-4 coverage:
  test_cross_clinic_returns_404 covers:
    "Given user from clinic_id_Y requests appointment belonging to clinic_id_X
    When GET /appointments/{id}
    Then 404 is returned (not 403)"

downstream-regression-na: brand-local clinic isolation test for vitalia scheduling T-6
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.modules.vitalia.scheduling.domain.exceptions import AppointmentNotFoundError

# ---------------------------------------------------------------------------
# Test constants
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_A_ID = uuid4()  # The appointment's clinic
CLINIC_B_ID = uuid4()  # The requesting user's clinic (different)
APPT_ID = uuid4()
USER_ID = uuid4()

_CLINIC_A_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_A_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "doctor",
}

_CLINIC_B_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_B_ID),  # cross-clinic attempt
    "X-User-ID": str(USER_ID),
    "X-User-Role": "doctor",
}


# ---------------------------------------------------------------------------
# Test app factory
# ---------------------------------------------------------------------------


def _build_test_app() -> FastAPI:
    """Build minimal FastAPI test app with agenda router."""
    from src.modules.vitalia.scheduling.api.agenda_router import router

    test_app = FastAPI(redirect_slashes=False)
    test_app.include_router(router, prefix="/api/v1/scheduling")

    async def _fake_db():
        session = MagicMock()
        session.__aenter__ = AsyncMock(return_value=session)
        session.__aexit__ = AsyncMock(return_value=False)
        yield session

    from src.modules.vitalia.scheduling.api import agenda_router as ar_module

    test_app.dependency_overrides[ar_module._get_db] = _fake_db
    return test_app


# ---------------------------------------------------------------------------
# Tests: Cross-clinic isolation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cross_clinic_returns_404() -> None:
    """SC-4: Cross-clinic appointment request returns 404 (not 403 — HIPAA-lite substrate).

    AppointmentDetailService raises AppointmentNotFoundError when dual filter
    (tenant_id + clinic_id) returns no rows. Router must map this to HTTP 404.
    """
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        # Cross-clinic: service raises AppointmentNotFoundError
        svc_instance.get_detail = AsyncMock(
            side_effect=AppointmentNotFoundError(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_B_ID,
            )
        )
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                f"/api/v1/scheduling/appointments/{APPT_ID}",
                headers=_CLINIC_B_HEADERS,  # wrong clinic
            )

    # CRITICAL: must be 404, NOT 403
    assert resp.status_code == 404, (
        f"Expected 404 (HIPAA-lite cross-clinic substrate), got {resp.status_code}. "
        "Cross-clinic must NOT confirm appointment existence with 403."
    )
    assert resp.json()["detail"]["error_code"] == "APPOINTMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_cross_clinic_not_403() -> None:
    """Explicit assertion: cross-clinic MUST NOT return 403.

    403 would confirm the appointment exists, which is an information leak.
    HIPAA-lite requires 404 to hide existence from other clinics.
    """
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.get_detail = AsyncMock(
            side_effect=AppointmentNotFoundError(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_B_ID,
            )
        )
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                f"/api/v1/scheduling/appointments/{APPT_ID}",
                headers=_CLINIC_B_HEADERS,
            )

    assert resp.status_code != 403, "Got 403 — information leak! Cross-clinic must return 404 per HIPAA-lite substrate."


@pytest.mark.asyncio
async def test_correct_clinic_returns_200() -> None:
    """Happy path: correct clinic_id returns appointment detail."""
    fake_detail: dict = {
        "appointment_id": str(APPT_ID),
        "patient_id": str(uuid4()),
        "patient_name_masked": "P. García",
        "patient_dni_masked": None,
        "patient_phone_masked": None,
        "patient_email_masked": None,
        "start_time": "2026-05-26T10:00:00+00:00",
        "end_time": "2026-05-26T10:30:00+00:00",
        "doctor_id": str(uuid4()),
        "doctor_label": "Dr. Ramírez",
        "service_label": "Limpieza dental",
        "appointment_status": "SCHEDULED",
        "payment_status": "sin_pago",
        "origin": "walk_in",
        "balance_due_cents": 15000,
        "balance_paid_cents": 0,
        "currency": "PEN",
        "currency_override": None,
        "payments": [],
        "notes_internal": None,
        "last_activity_at": None,
        "last_activity_by_label": None,
    }

    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.get_detail = AsyncMock(return_value=fake_detail)
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.get(
                f"/api/v1/scheduling/appointments/{APPT_ID}",
                headers=_CLINIC_A_HEADERS,  # correct clinic
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["appointment_id"] == str(APPT_ID)
    # PHI fields must be masked (never raw)
    assert "patient_name_masked" in body
    assert "patient_dni_masked" in body


@pytest.mark.asyncio
async def test_cross_clinic_patch_status_also_returns_404() -> None:
    """PATCH /status cross-clinic also returns 404 (not 403) — same HIPAA-lite rule."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentStatusService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.change_status = AsyncMock(
            side_effect=AppointmentNotFoundError(
                appointment_id=APPT_ID,
                tenant_id=TENANT_ID,
                clinic_id=CLINIC_B_ID,
            )
        )
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.patch(
                f"/api/v1/scheduling/appointments/{APPT_ID}/status",
                json={"new_status": "CONFIRMED", "reason": None},
                headers=_CLINIC_B_HEADERS,
            )

    assert resp.status_code == 404
    assert resp.json()["detail"]["error_code"] == "APPOINTMENT_NOT_FOUND"
