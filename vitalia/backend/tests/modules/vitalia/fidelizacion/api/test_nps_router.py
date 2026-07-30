"""Tests para NPS API endpoints — T-7 fidelización vitalia.

Gherkin coverage:
  SC-NPS-01: POST /nps/submit registra respuesta NPS del paciente (200)
  SC-NPS-02: POST /nps/submit con score fuera de rango retorna 422
  SC-NPS-03: GET /nps/summary retorna estadísticas agregadas (200)
  SC-NPS-04: GET /nps/summary sin PHI per-patient en respuesta
  SC-NPS-05: POST /nps/submit sin X-Tenant-ID retorna 422

Arquitectura tests:
  - response_model= verificado (PII gate HIPAA-lite)
  - comment (PHI) excluido de respuesta
  - Dual filter tenant_id + clinic_id

downstream-regression-na: brand-local API tests vitalia fidelizacion NPS
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.vitalia.fidelizacion.application.dtos.nps_dtos import (
    NPSResponseResponse,
    NPSSummaryResponse,
)
from src.modules.vitalia.fidelizacion.domain.value_objects.nps_band import NPSBand

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
PATIENT_ID = uuid4()
USER_ID = uuid4()
RESPONSE_ID = uuid4()

COMMON_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "patient",
}


def _now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def test_app() -> FastAPI:
    """FastAPI test app con NPS router montado."""
    from src.modules.vitalia.fidelizacion.api.router import fidelizacion_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(fidelizacion_router, prefix="/api/v1/vitalia/fidelizacion")
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Test client para NPS endpoints."""
    return TestClient(test_app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# SC-NPS-01: POST /nps/submit — registro NPS exitoso
# ---------------------------------------------------------------------------


def test_nps_submit_returns_200(client: TestClient) -> None:
    """SC-NPS-01: POST /nps/submit con score válido retorna 200.

    HIPAA-lite: comment (PHI) excluido del response_model.
    """
    now = _now()
    mock_result = NPSResponseResponse(
        id=RESPONSE_ID,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        patient_id=PATIENT_ID,
        score=9,
        band=NPSBand.PROMOTER,
        appointment_id=None,
        responded_via="whatsapp",
        responded_at=now,
        tagged_in_inbox=False,
        created_at=now,
    )

    with patch("src.modules.vitalia.fidelizacion.api.nps_endpoints.NPSService") as MockService:
        instance = MagicMock()
        instance.submit = AsyncMock(return_value=mock_result)
        MockService.return_value = instance

        response = client.post(
            "/api/v1/vitalia/fidelizacion/nps/submit",
            json={
                "patient_id": str(PATIENT_ID),
                "clinic_id": str(CLINIC_ID),
                "score": 9,
                "comment_plain": "Muy buena atención",
                "responded_via": "whatsapp",
            },
            headers=COMMON_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "score" in data
    assert "band" in data
    # PHI guard: comment_plain NO debe aparecer en respuesta
    assert "comment_plain" not in data
    assert "comment" not in data


def test_nps_submit_promoter_band(client: TestClient) -> None:
    """SC-NPS-01-B: Score 9-10 resulta en band PROMOTER."""
    now = _now()
    mock_result = NPSResponseResponse(
        id=RESPONSE_ID,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        patient_id=PATIENT_ID,
        score=10,
        band=NPSBand.PROMOTER,
        responded_via="whatsapp",
        responded_at=now,
        tagged_in_inbox=False,
        created_at=now,
    )

    with patch("src.modules.vitalia.fidelizacion.api.nps_endpoints.NPSService") as MockService:
        instance = MagicMock()
        instance.submit = AsyncMock(return_value=mock_result)
        MockService.return_value = instance

        response = client.post(
            "/api/v1/vitalia/fidelizacion/nps/submit",
            json={
                "patient_id": str(PATIENT_ID),
                "clinic_id": str(CLINIC_ID),
                "score": 10,
                "responded_via": "whatsapp",
            },
            headers=COMMON_HEADERS,
        )

    assert response.status_code == 200
    assert response.json()["band"] == NPSBand.PROMOTER.value


# ---------------------------------------------------------------------------
# SC-NPS-02: POST /nps/submit — score fuera de rango
# ---------------------------------------------------------------------------


def test_nps_submit_score_out_of_range_returns_422(client: TestClient) -> None:
    """SC-NPS-02: POST /nps/submit con score=11 retorna 422."""
    response = client.post(
        "/api/v1/vitalia/fidelizacion/nps/submit",
        json={
            "patient_id": str(PATIENT_ID),
            "clinic_id": str(CLINIC_ID),
            "score": 11,  # inválido — máximo es 10
            "responded_via": "whatsapp",
        },
        headers=COMMON_HEADERS,
    )
    assert response.status_code == 422


def test_nps_submit_score_negative_returns_422(client: TestClient) -> None:
    """SC-NPS-02-N: POST /nps/submit con score=-1 retorna 422."""
    response = client.post(
        "/api/v1/vitalia/fidelizacion/nps/submit",
        json={
            "patient_id": str(PATIENT_ID),
            "clinic_id": str(CLINIC_ID),
            "score": -1,  # inválido — mínimo es 0
            "responded_via": "whatsapp",
        },
        headers=COMMON_HEADERS,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# SC-NPS-03: GET /nps/summary — estadísticas agregadas
# ---------------------------------------------------------------------------


def test_nps_summary_returns_200(client: TestClient) -> None:
    """SC-NPS-03: GET /nps/summary retorna estadísticas NPS agregadas."""
    now = _now()
    period_start = now - timedelta(days=30)
    mock_result = NPSSummaryResponse(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        period_start=period_start,
        period_end=now,
        total_responses=25,
        promoters=15,
        passives=7,
        detractors=3,
        nps_score=48.0,
        detractors_untagged=2,
    )

    with (
        patch("src.modules.vitalia.fidelizacion.api.nps_endpoints.NPSService") as MockService,
        patch("src.modules.vitalia.fidelizacion.api.nps_endpoints.NPSResponseRepository") as MockRepo,
    ):
        mock_nps_repo = MagicMock()
        mock_nps_repo.list_by_period = AsyncMock(return_value=[])
        MockRepo.return_value = mock_nps_repo

        instance = MagicMock()
        instance.summary = AsyncMock(return_value=mock_result)
        MockService.return_value = instance

        response = client.get(
            "/api/v1/vitalia/fidelizacion/nps/summary",
            params={
                "clinic_id": str(CLINIC_ID),
                "period_days": 30,
            },
            headers={
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
                "X-User-ID": str(USER_ID),
                "X-User-Role": "admin_clinic",
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "total_responses" in data
    assert "promoters" in data
    assert "detractors" in data
    assert "nps_score" in data


# ---------------------------------------------------------------------------
# SC-NPS-04: PHI guard — comment excluido de respuesta
# ---------------------------------------------------------------------------


def test_nps_summary_no_phi_in_response(client: TestClient) -> None:
    """SC-NPS-04: GET /nps/summary NO incluye comment ni patient names (PHI)."""
    now = _now()
    period_start = now - timedelta(days=30)
    mock_result = NPSSummaryResponse(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        period_start=period_start,
        period_end=now,
        total_responses=5,
        promoters=3,
        passives=1,
        detractors=1,
        nps_score=40.0,
    )

    with (
        patch("src.modules.vitalia.fidelizacion.api.nps_endpoints.NPSService") as MockService,
        patch("src.modules.vitalia.fidelizacion.api.nps_endpoints.NPSResponseRepository") as MockRepo,
    ):
        mock_nps_repo = MagicMock()
        mock_nps_repo.list_by_period = AsyncMock(return_value=[])
        MockRepo.return_value = mock_nps_repo

        instance = MagicMock()
        instance.summary = AsyncMock(return_value=mock_result)
        MockService.return_value = instance

        response = client.get(
            "/api/v1/vitalia/fidelizacion/nps/summary",
            params={"clinic_id": str(CLINIC_ID), "period_days": 30},
            headers={
                "X-Tenant-ID": str(TENANT_ID),
                "X-Clinic-ID": str(CLINIC_ID),
                "X-User-ID": str(USER_ID),
                "X-User-Role": "admin_clinic",
            },
        )

    assert response.status_code == 200
    body_str = response.text
    # Verificar ausencia de PHI
    assert "comment" not in body_str
    assert "patient_name" not in body_str
    assert "dni" not in body_str


# ---------------------------------------------------------------------------
# SC-NPS-05: Headers obligatorios
# ---------------------------------------------------------------------------


def test_nps_submit_missing_tenant_id_returns_422(client: TestClient) -> None:
    """SC-NPS-05: POST /nps/submit sin X-Tenant-ID retorna 422."""
    headers_no_tenant = {
        "X-Clinic-ID": str(CLINIC_ID),
        "X-User-ID": str(USER_ID),
        "X-User-Role": "patient",
    }
    response = client.post(
        "/api/v1/vitalia/fidelizacion/nps/submit",
        json={
            "patient_id": str(PATIENT_ID),
            "clinic_id": str(CLINIC_ID),
            "score": 8,
            "responded_via": "whatsapp",
        },
        headers=headers_no_tenant,
    )
    assert response.status_code == 422
