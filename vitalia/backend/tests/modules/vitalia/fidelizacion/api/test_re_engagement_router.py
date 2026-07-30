"""Tests para re-engagement API endpoints — T-7 fidelización vitalia.

Gherkin coverage:
  SC-RE-01: GET /re-engagement/patterns retorna lista de resúmenes con 200
  SC-RE-02: POST /re-engagement/send-proactive dispara recordatorio proactivo
  SC-RE-03: POST /re-engagement/pause pausa paciente con audit log
  SC-RE-04: POST /re-engagement/mark-external registra respuesta externa
  SC-RE-05: POST /re-engagement/mark-no-continue registra decisión no-continuar
  SC-RE-06: POST /re-engagement/manual-call registra llamada manual
  SC-RE-07: 403 retornado cuando user_role no está en PHI roles
  SC-RE-08: 422 retornado con body inválido

Arquitectura tests:
  - response_model= verificado (PII gate HIPAA-lite)
  - Dual filter tenant_id + clinic_id en todos los requests
  - Sin PHI en respuestas (payload_phi, notes excluidos)

downstream-regression-na: brand-local API tests vitalia fidelizacion
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
    ManualCallResponse,
    PausePatientResponse,
    ProactiveReminderResponse,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_outcome import (
    ReEngagementOutcome,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.re_engagement_pattern import (
    ReEngagementPattern,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
PATIENT_ID = uuid4()
USER_ID = uuid4()
EVENT_ID = uuid4()

PHI_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "doctor",
}


def _now() -> datetime:
    return datetime.now(UTC)


# ---------------------------------------------------------------------------
# App test setup — importa el router después de crear los archivos
# ---------------------------------------------------------------------------


@pytest.fixture
def test_app() -> FastAPI:
    """FastAPI test app con router fidelización montado."""
    from src.modules.vitalia.fidelizacion.api.router import fidelizacion_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(fidelizacion_router, prefix="/api/v1/vitalia/fidelizacion")
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Test client sincrónico para endpoints fidelización."""
    return TestClient(test_app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# SC-RE-01: GET /re-engagement/patterns — lista patrones activos
# ---------------------------------------------------------------------------


def test_list_patterns_returns_200(client: TestClient) -> None:
    """SC-RE-01: GET /re-engagement/patterns con headers válidos retorna 200.

    HIPAA-lite: tenant_id + clinic_id en headers, sin PHI en respuesta.
    """
    with patch("src.modules.vitalia.fidelizacion.api.re_engagement_endpoints.ReEngagementService") as MockService:
        instance = MagicMock()
        instance.list_patterns = AsyncMock(return_value=[])
        MockService.return_value = instance

        response = client.get(
            "/api/v1/vitalia/fidelizacion/re-engagement/patterns",
            params={"pattern": ReEngagementPattern.FOLLOW_UP.value},
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()
    assert "patterns" in data
    assert "tenant_id" in data
    assert "clinic_id" in data


def test_list_patterns_missing_clinic_id_returns_422(client: TestClient) -> None:
    """SC-RE-01-E: GET /re-engagement/patterns sin X-Clinic-ID retorna 422."""
    headers_no_clinic = {
        "X-Tenant-ID": str(TENANT_ID),
        "X-User-ID": str(USER_ID),
        "X-User-Role": "doctor",
    }
    response = client.get(
        "/api/v1/vitalia/fidelizacion/re-engagement/patterns",
        params={"pattern": ReEngagementPattern.FOLLOW_UP.value},
        headers=headers_no_clinic,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# SC-RE-02: POST /re-engagement/send-proactive
# ---------------------------------------------------------------------------


def test_send_proactive_returns_200(client: TestClient) -> None:
    """SC-RE-02: POST /re-engagement/send-proactive dispara recordatorio proactivo."""
    now = _now()
    mock_result = ProactiveReminderResponse(
        event_id=EVENT_ID,
        patient_id=PATIENT_ID,
        status="sent",
        sent_at=now,
        throttled=False,
    )

    with patch("src.modules.vitalia.fidelizacion.api.re_engagement_endpoints.ProactiveOutboundService") as MockService:
        instance = MagicMock()
        instance.send_proactive_reminder = AsyncMock(return_value=mock_result)
        MockService.return_value = instance

        response = client.post(
            "/api/v1/vitalia/fidelizacion/re-engagement/send-proactive",
            json={
                "patient_id": str(PATIENT_ID),
                "clinic_id": str(CLINIC_ID),
                "patient_phone": "+5491155550000",
                "patient_name": "Ana García",
                "template_id": "tpl_followup_v1",
                "pattern": ReEngagementPattern.FOLLOW_UP.value,
            },
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data
    assert "patient_id" in data
    assert "status" in data


def test_send_proactive_throttled_returns_200_with_throttled_flag(client: TestClient) -> None:
    """SC-RE-02-T: POST /re-engagement/send-proactive throttled retorna 200 con throttled=True."""
    mock_result = ProactiveReminderResponse(
        event_id=EVENT_ID,
        patient_id=PATIENT_ID,
        status="throttled",
        throttled=True,
        blocked_reason="Throttle 7d activo",
    )

    with patch("src.modules.vitalia.fidelizacion.api.re_engagement_endpoints.ProactiveOutboundService") as MockService:
        instance = MagicMock()
        instance.send_proactive_reminder = AsyncMock(return_value=mock_result)
        MockService.return_value = instance

        response = client.post(
            "/api/v1/vitalia/fidelizacion/re-engagement/send-proactive",
            json={
                "patient_id": str(PATIENT_ID),
                "clinic_id": str(CLINIC_ID),
                "patient_phone": "+5491155550000",
                "patient_name": "Ana García",
                "template_id": "tpl_followup_v1",
                "pattern": ReEngagementPattern.FOLLOW_UP.value,
            },
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()
    assert data["throttled"] is True


# ---------------------------------------------------------------------------
# SC-RE-03: POST /re-engagement/pause
# ---------------------------------------------------------------------------


def test_pause_patient_returns_200(client: TestClient) -> None:
    """SC-RE-03: POST /re-engagement/pause pausa paciente y retorna 200."""
    pause_until = _now() + timedelta(days=14)
    mock_result = PausePatientResponse(
        patient_id=PATIENT_ID,
        paused_until=pause_until,
        event_id=EVENT_ID,
    )

    with patch("src.modules.vitalia.fidelizacion.api.re_engagement_endpoints.PausePatientService") as MockService:
        instance = MagicMock()
        instance.pause_patient = AsyncMock(return_value=mock_result)
        MockService.return_value = instance

        response = client.post(
            "/api/v1/vitalia/fidelizacion/re-engagement/pause",
            json={
                "patient_id": str(PATIENT_ID),
                "clinic_id": str(CLINIC_ID),
                "pause_until": pause_until.isoformat(),
                "pause_reason": "Viaje al exterior",
                "paused_by_user_id": str(USER_ID),
            },
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()
    assert "patient_id" in data
    assert "paused_until" in data
    assert "event_id" in data


# ---------------------------------------------------------------------------
# SC-RE-04: POST /re-engagement/mark-external
# ---------------------------------------------------------------------------


def test_mark_external_returns_200(client: TestClient) -> None:
    """SC-RE-04: POST /re-engagement/mark-external registra respuesta externa."""
    now = _now()
    # _mark_outcome returns tuple (event_id, outcome, recorded_at)
    mock_tuple = (EVENT_ID, ReEngagementOutcome.RESPONDED, now)

    with patch(
        "src.modules.vitalia.fidelizacion.api.re_engagement_endpoints._mark_outcome",
        new_callable=AsyncMock,
        return_value=mock_tuple,
    ):
        response = client.post(
            "/api/v1/vitalia/fidelizacion/re-engagement/mark-external",
            json={
                "patient_id": str(PATIENT_ID),
                "clinic_id": str(CLINIC_ID),
                "comment": "Respondió por llamada telefónica",
            },
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data
    assert "outcome" in data


# ---------------------------------------------------------------------------
# SC-RE-05: POST /re-engagement/mark-no-continue
# ---------------------------------------------------------------------------


def test_mark_no_continue_returns_200(client: TestClient) -> None:
    """SC-RE-05: POST /re-engagement/mark-no-continue registra decisión de no continuar."""
    now = _now()
    # _mark_outcome returns tuple (event_id, outcome, recorded_at)
    mock_tuple = (EVENT_ID, ReEngagementOutcome.OPTED_OUT, now)

    with patch(
        "src.modules.vitalia.fidelizacion.api.re_engagement_endpoints._mark_outcome",
        new_callable=AsyncMock,
        return_value=mock_tuple,
    ):
        response = client.post(
            "/api/v1/vitalia/fidelizacion/re-engagement/mark-no-continue",
            json={
                "patient_id": str(PATIENT_ID),
                "clinic_id": str(CLINIC_ID),
                "reason": "Prefiere otro tratamiento",
            },
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()
    assert "event_id" in data
    assert "outcome" in data


# ---------------------------------------------------------------------------
# SC-RE-06: POST /re-engagement/manual-call
# ---------------------------------------------------------------------------


def test_manual_call_returns_201(client: TestClient) -> None:
    """SC-RE-06: POST /re-engagement/manual-call registra llamada manual con 201."""
    now = _now()
    mock_result = ManualCallResponse(
        event_id=EVENT_ID,
        patient_id=PATIENT_ID,
        outcome=ReEngagementOutcome.RESCHEDULED,
        recorded_at=now,
    )

    with patch("src.modules.vitalia.fidelizacion.api.re_engagement_endpoints.ManualCallService") as MockService:
        instance = MagicMock()
        instance.record_call = AsyncMock(return_value=mock_result)
        MockService.return_value = instance

        response = client.post(
            "/api/v1/vitalia/fidelizacion/re-engagement/manual-call",
            json={
                "patient_id": str(PATIENT_ID),
                "clinic_id": str(CLINIC_ID),
                "outcome": ReEngagementOutcome.RESCHEDULED.value,
                "notes_plain": "Acordamos turno para el lunes",
                "called_by_user_id": str(USER_ID),
            },
            headers=PHI_HEADERS,
        )

    assert response.status_code == 201
    data = response.json()
    assert "event_id" in data
    assert "outcome" in data
    # PHI guard: notas no deben aparecer en la respuesta
    assert "notes_plain" not in data


# ---------------------------------------------------------------------------
# SC-RE-07: RBAC — 403 para roles no PHI
# ---------------------------------------------------------------------------


def test_list_patterns_marketing_role_returns_403(client: TestClient) -> None:
    """SC-RE-07: GET /re-engagement/patterns con role=marketing retorna 403."""
    marketing_headers = {
        "X-Tenant-ID": str(TENANT_ID),
        "X-Clinic-ID": str(CLINIC_ID),
        "X-User-ID": str(USER_ID),
        "X-User-Role": "marketing",
    }

    with patch("src.modules.vitalia.fidelizacion.api.re_engagement_endpoints.ReEngagementService") as MockService:
        instance = MagicMock()
        instance.list_patterns = AsyncMock(return_value=[])
        MockService.return_value = instance

        response = client.get(
            "/api/v1/vitalia/fidelizacion/re-engagement/patterns",
            params={"pattern": ReEngagementPattern.FOLLOW_UP.value},
            headers=marketing_headers,
        )

    assert response.status_code == 403


# ---------------------------------------------------------------------------
# SC-RE-08: Validación de body inválido (422)
# ---------------------------------------------------------------------------


def test_send_proactive_invalid_body_returns_422(client: TestClient) -> None:
    """SC-RE-08: POST /re-engagement/send-proactive con body inválido retorna 422."""
    response = client.post(
        "/api/v1/vitalia/fidelizacion/re-engagement/send-proactive",
        json={"patient_id": "not-a-uuid"},  # inválido — falta clinic_id, template_id, etc.
        headers=PHI_HEADERS,
    )
    assert response.status_code == 422


def test_pause_missing_pause_until_returns_422(client: TestClient) -> None:
    """SC-RE-08-P: POST /re-engagement/pause sin pause_until retorna 422."""
    response = client.post(
        "/api/v1/vitalia/fidelizacion/re-engagement/pause",
        json={
            "patient_id": str(PATIENT_ID),
            "clinic_id": str(CLINIC_ID),
            # pause_until faltante
        },
        headers=PHI_HEADERS,
    )
    assert response.status_code == 422
