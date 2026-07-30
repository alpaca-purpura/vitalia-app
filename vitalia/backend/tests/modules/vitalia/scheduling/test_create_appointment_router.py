"""T-BE-4 — POST /appointments create endpoint tests.

TDD: tests define the create appointment contract BEFORE + AFTER T-BE-4.

Coverage:
  - Happy path: origin=walk_in + patient_id (REQUIRED) → 201 + AppointmentDetailDTO
  - Happy path: origin=telefono + patient_id → 201
  - Validation: patient_id omitted (now REQUIRED) → 422 PATIENT_ID_REQUIRED
  - Validation: origin=desde_paciente_existente rejected (removed in T-BE-4) → 422
  - Overlap: service raises AppointmentOverlapError → 409 APPOINTMENT_OVERLAP
  - Out-of-hours: service raises OutOfWorkingHoursError → 422 OUT_OF_HOURS
  - RBAC: non-PHI role → 403
  - Service called with correct tenant_id + clinic_id (dual filter)

downstream-regression-na: brand-local create appointment test for vitalia scheduling T-BE-4
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
DOCTOR_ID = uuid4()
PATIENT_ID = uuid4()
OFFER_ID = uuid4()  # T-BE-4: required FK
NEW_APPT_ID = uuid4()

_PHI_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "admin_clinic",
}

_NON_PHI_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "marketing",
}

_FAKE_CREATED_DETAIL: dict = {
    "appointment_id": str(NEW_APPT_ID),
    "patient_id": str(PATIENT_ID),
    "patient_name_masked": "L. Fernández",
    "patient_dni_masked": None,
    "patient_phone_masked": None,
    "patient_email_masked": None,
    "start_time": "2026-05-27T09:00:00+00:00",
    "end_time": "2026-05-27T09:30:00+00:00",
    "doctor_id": str(DOCTOR_ID),
    "doctor_label": "Dr. Vargas",
    "service_label": "Extracción simple",
    "appointment_status": "SCHEDULED",
    "payment_status": "sin_pago",
    "origin": "walk_in",
    "balance_due_cents": 12000,
    "balance_paid_cents": 0,
    "currency": "PEN",
    "currency_override": None,
    "payments": [],
    "notes_internal": None,
    "last_activity_at": None,
    "last_activity_by_label": None,
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
        yield MagicMock()

    from src.modules.vitalia.scheduling.api import agenda_router as ar_module

    test_app.dependency_overrides[ar_module._get_db] = _fake_db
    return test_app


# ---------------------------------------------------------------------------
# Tests: create appointment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_appointment_walk_in_with_patient_id_returns_201() -> None:
    """Walk-in with patient_id (required in T-BE-4) → 201 Created."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.CreateAppointmentService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridRepositoryImpl"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.create_appointment = AsyncMock(return_value=_FAKE_CREATED_DETAIL)
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/scheduling/appointments",
                json={
                    "origin": "walk_in",
                    "patient_id": str(PATIENT_ID),
                    "doctor_id": str(DOCTOR_ID),
                    "offer_id": str(OFFER_ID),
                    "service_label": "Extracción simple",
                    "start_time": "2026-05-27T09:00:00+00:00",
                    "end_time": "2026-05-27T09:30:00+00:00",
                },
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 201
    body = resp.json()
    assert body["appointment_id"] == str(NEW_APPT_ID)
    assert "patient_name_masked" in body


@pytest.mark.asyncio
async def test_create_appointment_telefono_with_patient_id_returns_201() -> None:
    """origin=telefono + patient_id → 201 Created."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.CreateAppointmentService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridRepositoryImpl"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.create_appointment = AsyncMock(return_value=_FAKE_CREATED_DETAIL)
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/scheduling/appointments",
                json={
                    "origin": "telefono",
                    "patient_id": str(PATIENT_ID),
                    "doctor_id": str(DOCTOR_ID),
                    "offer_id": str(OFFER_ID),
                    "service_label": "Control de seguimiento",
                    "start_time": "2026-05-27T10:00:00+00:00",
                    "end_time": "2026-05-27T10:30:00+00:00",
                },
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_appointment_missing_patient_id_returns_422() -> None:
    """patient_id now REQUIRED (T-BE-4) — omitting it → 422."""
    app = _build_test_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/scheduling/appointments",
            json={
                "origin": "walk_in",
                # patient_id intentionally omitted
                "doctor_id": str(DOCTOR_ID),
                "service_label": "Limpieza dental",
                "start_time": "2026-05-27T11:00:00+00:00",
                "end_time": "2026-05-27T11:30:00+00:00",
            },
            headers=_PHI_HEADERS,
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_appointment_desde_paciente_existente_rejected() -> None:
    """origin=desde_paciente_existente removed in T-BE-4 → 422 (DTO rejects it)."""
    app = _build_test_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/scheduling/appointments",
            json={
                "origin": "desde_paciente_existente",
                "patient_id": str(PATIENT_ID),
                "doctor_id": str(DOCTOR_ID),
                "service_label": "Control",
                "start_time": "2026-05-27T10:00:00+00:00",
                "end_time": "2026-05-27T10:30:00+00:00",
            },
            headers=_PHI_HEADERS,
        )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_appointment_non_phi_role_forbidden() -> None:
    """Non-PHI role cannot create appointments — 403."""
    app = _build_test_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.post(
            "/api/v1/scheduling/appointments",
            json={
                "origin": "walk_in",
                "patient_id": str(PATIENT_ID),
                "doctor_id": str(DOCTOR_ID),
                "offer_id": str(OFFER_ID),
                "service_label": "Consulta",
                "start_time": "2026-05-27T12:00:00+00:00",
                "end_time": "2026-05-27T12:30:00+00:00",
            },
            headers=_NON_PHI_HEADERS,
        )

    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "PHI_RBAC_DENIED"


@pytest.mark.asyncio
async def test_create_appointment_overlap_returns_409() -> None:
    """Service raises AppointmentOverlapError → 409 APPOINTMENT_OVERLAP."""
    from src.modules.vitalia.scheduling.domain.exceptions import AppointmentOverlapError  # noqa: PLC0415

    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.CreateAppointmentService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridRepositoryImpl"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.create_appointment = AsyncMock(side_effect=AppointmentOverlapError())
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/scheduling/appointments",
                json={
                    "origin": "walk_in",
                    "patient_id": str(PATIENT_ID),
                    "doctor_id": str(DOCTOR_ID),
                    "offer_id": str(OFFER_ID),
                    "service_label": "Consulta",
                    "start_time": "2026-05-27T09:00:00+00:00",
                    "end_time": "2026-05-27T09:30:00+00:00",
                },
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 409
    body = resp.json()
    assert body["detail"]["error_code"] == "APPOINTMENT_OVERLAP"


@pytest.mark.asyncio
async def test_create_appointment_out_of_hours_returns_422() -> None:
    """Service raises OutOfWorkingHoursError → 422 OUT_OF_HOURS."""
    from src.modules.vitalia.scheduling.domain.exceptions import OutOfWorkingHoursError  # noqa: PLC0415

    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.CreateAppointmentService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridRepositoryImpl"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.create_appointment = AsyncMock(side_effect=OutOfWorkingHoursError())
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/scheduling/appointments",
                json={
                    "origin": "walk_in",
                    "patient_id": str(PATIENT_ID),
                    "doctor_id": str(DOCTOR_ID),
                    "offer_id": str(OFFER_ID),
                    "service_label": "Consulta",
                    "start_time": "2026-05-27T07:00:00+00:00",
                    "end_time": "2026-05-27T07:30:00+00:00",
                },
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"]["error_code"] == "OUT_OF_HOURS"


@pytest.mark.asyncio
async def test_create_appointment_past_start_time_returns_422() -> None:
    """Service raises PastAppointmentError → 422 PAST_APPOINTMENT (G-round-2)."""
    from src.modules.vitalia.scheduling.domain.exceptions import PastAppointmentError  # noqa: PLC0415

    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.CreateAppointmentService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridRepositoryImpl"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.create_appointment = AsyncMock(side_effect=PastAppointmentError())
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.post(
                "/api/v1/scheduling/appointments",
                json={
                    "origin": "walk_in",
                    "patient_id": str(PATIENT_ID),
                    "doctor_id": str(DOCTOR_ID),
                    "offer_id": str(OFFER_ID),
                    "service_label": "Limpieza dental",
                    "start_time": "2020-01-01T09:00:00+00:00",
                    "end_time": "2020-01-01T09:30:00+00:00",
                },
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 422
    body = resp.json()
    assert body["detail"]["error_code"] == "PAST_APPOINTMENT"
    assert "pasado" in body["detail"]["message"]


@pytest.mark.asyncio
async def test_create_appointment_service_called_with_dual_filter() -> None:
    """create_appointment service receives tenant_id + clinic_id (dual filter A12)."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.CreateAppointmentService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AgendaGridRepositoryImpl"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.create_appointment = AsyncMock(return_value=_FAKE_CREATED_DETAIL)
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            await client.post(
                "/api/v1/scheduling/appointments",
                json={
                    "origin": "walk_in",
                    "patient_id": str(PATIENT_ID),
                    "doctor_id": str(DOCTOR_ID),
                    "offer_id": str(OFFER_ID),
                    "service_label": "Consulta",
                    "start_time": "2026-05-27T13:00:00+00:00",
                    "end_time": "2026-05-27T13:30:00+00:00",
                },
                headers=_PHI_HEADERS,
            )

    # Verify service was called with correct tenant_id + clinic_id
    svc_instance.create_appointment.assert_awaited_once()
    call_kwargs = svc_instance.create_appointment.call_args.kwargs
    from uuid import UUID

    assert call_kwargs["tenant_id"] == UUID(str(TENANT_ID))
    assert call_kwargs["clinic_id"] == UUID(str(CLINIC_ID))
