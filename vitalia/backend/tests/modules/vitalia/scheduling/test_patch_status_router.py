"""T-6 A3 — PATCH /appointments/{id}/status status transition tests.

TDD: tests define the PATCH status endpoint contract BEFORE implementation.

Coverage:
  - Happy path: CONFIRMED transition → 200 + AppointmentDetailDTO
  - Happy path: CANCELLED with reason → 200
  - Happy path: NO_SHOW transition → 200
  - Happy path: COMPLETED transition → 200
  - Cross-clinic: AppointmentNotFoundError → 404 (not 403 — HIPAA-lite substrate)
  - RBAC: non-PHI role → 403
  - Audit log: service receives audit_writer (from_status→to_status logged)
  - Service called with correct tenant_id + clinic_id (dual filter)

Per T-6 acceptance A3:
  "PATCH status emits status_change audit row with from→to"

downstream-regression-na: brand-local patch status test for vitalia scheduling T-6
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
CLINIC_ID = uuid4()
APPT_ID = uuid4()
USER_ID = uuid4()

_PHI_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "doctor",
}

_NON_PHI_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "operaciones",
}


def _fake_updated_detail(status: str) -> dict:
    return {
        "appointment_id": str(APPT_ID),
        "patient_id": str(uuid4()),
        "patient_name_masked": "M. Castillo",
        "patient_dni_masked": None,
        "patient_phone_masked": None,
        "patient_email_masked": None,
        "start_time": "2026-05-26T15:00:00+00:00",
        "end_time": "2026-05-26T15:30:00+00:00",
        "doctor_id": str(uuid4()),
        "doctor_label": "Dr. Soto",
        "service_label": "Blanqueamiento",
        "appointment_status": status,
        "payment_status": "sin_pago",
        "origin": "telefono",
        "balance_due_cents": 20000,
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
# Tests: status transitions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_patch_status_confirmed_returns_200() -> None:
    """CONFIRMED transition → 200 + AppointmentDetailDTO with updated status."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentStatusService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.change_status = AsyncMock(return_value=_fake_updated_detail("CONFIRMED"))
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.patch(
                f"/api/v1/scheduling/appointments/{APPT_ID}/status",
                json={"new_status": "CONFIRMED", "reason": None},
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 200
    body = resp.json()
    assert body["appointment_status"] == "CONFIRMED"
    assert body["appointment_id"] == str(APPT_ID)


@pytest.mark.asyncio
async def test_patch_status_cancelled_with_reason_returns_200() -> None:
    """CANCELLED with reason → 200. Reason is forwarded to service."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentStatusService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.change_status = AsyncMock(return_value=_fake_updated_detail("CANCELLED"))
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.patch(
                f"/api/v1/scheduling/appointments/{APPT_ID}/status",
                json={"new_status": "CANCELLED", "reason": "Paciente no puede asistir"},
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 200
    # Verify reason was forwarded to service
    svc_instance.change_status.assert_awaited_once()
    call_kwargs = svc_instance.change_status.call_args.kwargs
    assert call_kwargs["reason"] == "Paciente no puede asistir"


@pytest.mark.asyncio
async def test_patch_status_no_show_returns_200() -> None:
    """NO_SHOW transition → 200."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentStatusService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.change_status = AsyncMock(return_value=_fake_updated_detail("NO_SHOW"))
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.patch(
                f"/api/v1/scheduling/appointments/{APPT_ID}/status",
                json={"new_status": "NO_SHOW", "reason": None},
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 200
    assert resp.json()["appointment_status"] == "NO_SHOW"


@pytest.mark.asyncio
async def test_patch_status_completed_returns_200() -> None:
    """COMPLETED transition → 200."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentStatusService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.change_status = AsyncMock(return_value=_fake_updated_detail("COMPLETED"))
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.patch(
                f"/api/v1/scheduling/appointments/{APPT_ID}/status",
                json={"new_status": "COMPLETED", "reason": None},
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_patch_status_cross_clinic_returns_404() -> None:
    """Cross-clinic PATCH returns 404 (not 403) — HIPAA-lite substrate."""
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
                clinic_id=CLINIC_ID,
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
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 404
    assert resp.json()["detail"]["error_code"] == "APPOINTMENT_NOT_FOUND"


@pytest.mark.asyncio
async def test_patch_status_non_phi_role_forbidden() -> None:
    """Non-PHI role → 403 before calling service."""
    app = _build_test_app()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        resp = await client.patch(
            f"/api/v1/scheduling/appointments/{APPT_ID}/status",
            json={"new_status": "CONFIRMED", "reason": None},
            headers=_NON_PHI_HEADERS,
        )

    assert resp.status_code == 403
    assert resp.json()["detail"]["error_code"] == "PHI_RBAC_DENIED"


@pytest.mark.asyncio
async def test_patch_status_service_receives_dual_filter() -> None:
    """Service is called with tenant_id + clinic_id — dual filter enforcement."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentStatusService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter"),
    ):
        svc_instance = MagicMock()
        svc_instance.change_status = AsyncMock(return_value=_fake_updated_detail("CONFIRMED"))
        MockSvc.return_value = svc_instance

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            await client.patch(
                f"/api/v1/scheduling/appointments/{APPT_ID}/status",
                json={"new_status": "CONFIRMED", "reason": None},
                headers=_PHI_HEADERS,
            )

    svc_instance.change_status.assert_awaited_once()
    call_kwargs = svc_instance.change_status.call_args.kwargs
    from uuid import UUID

    assert call_kwargs["tenant_id"] == UUID(str(TENANT_ID))
    assert call_kwargs["clinic_id"] == UUID(str(CLINIC_ID))
    assert call_kwargs["new_status"] == "CONFIRMED"


@pytest.mark.asyncio
async def test_patch_status_audit_writer_constructed() -> None:
    """AsyncAuditWriter is constructed per-request (passed to AppointmentStatusService)."""
    with (
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentStatusService") as MockSvc,
        patch("src.modules.vitalia.scheduling.api.agenda_router.AppointmentDetailRepository"),
        patch("src.modules.vitalia.scheduling.api.agenda_router.AsyncAuditWriter") as MockAudit,
    ):
        svc_instance = MagicMock()
        svc_instance.change_status = AsyncMock(return_value=_fake_updated_detail("CONFIRMED"))
        MockSvc.return_value = svc_instance
        MockAudit.return_value = MagicMock()

        app = _build_test_app()
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            resp = await client.patch(
                f"/api/v1/scheduling/appointments/{APPT_ID}/status",
                json={"new_status": "COMPLETED", "reason": None},
                headers=_PHI_HEADERS,
            )

    assert resp.status_code == 200
    # Audit writer constructed once per request
    MockAudit.assert_called_once()
    # Service received the audit_writer instance
    MockSvc.assert_called_once()
    call_kwargs = MockSvc.call_args.kwargs
    assert "audit_writer" in call_kwargs
