"""Tests para fidelización summary + activity stream API endpoints — T-7.

Gherkin coverage:
  SC-SUM-01: GET /summary retorna 5 KPIs del hero dashboard
  SC-SUM-02: GET /summary sin clinic_id header retorna 422
  SC-SUM-03: GET /activity-stream retorna items recientes sin PHI
  SC-SUM-04: GET /activity-stream con role=marketing retorna 403
  SC-SUM-05: GET /summary con role=nurse (PHI role) retorna 200

downstream-regression-na: brand-local API tests vitalia fidelizacion summary
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.vitalia.fidelizacion.application.dtos.re_engagement_dtos import (
    ActivityStreamResponse,
    FidelizacionSummaryResponse,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid4()
CLINIC_ID = uuid4()
USER_ID = uuid4()

PHI_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "nurse",
}

MARKETING_HEADERS = {
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
    "X-User-ID": str(USER_ID),
    "X-User-Role": "marketing",
}


def _now() -> datetime:
    return datetime.now(UTC)


@pytest.fixture
def test_app() -> FastAPI:
    """FastAPI test app con router de summary montado."""
    from src.modules.vitalia.fidelizacion.api.router import fidelizacion_router

    app = FastAPI(redirect_slashes=False)
    app.include_router(fidelizacion_router, prefix="/api/v1/vitalia/fidelizacion")
    return app


@pytest.fixture
def client(test_app: FastAPI) -> TestClient:
    """Test client para summary endpoints."""
    return TestClient(test_app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# SC-SUM-01: GET /summary — 5 KPIs hero dashboard
# ---------------------------------------------------------------------------


def test_summary_returns_200_with_5_kpis(client: TestClient) -> None:
    """SC-SUM-01: GET /summary retorna los 5 KPIs del hero dashboard."""
    now = _now()
    mock_result = FidelizacionSummaryResponse(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        snapshot_at=now,
        patients_in_followup=42,
        near_abandonment=8,
        return_rate=0.65,
        re_engaged_count_period=15,
        nps_average=52.3,
    )

    with patch("src.modules.vitalia.fidelizacion.api.fidelizacion_summary_endpoints._build_summary") as mock_fn:
        mock_fn.return_value = mock_result

        response = client.get(
            "/api/v1/vitalia/fidelizacion/summary",
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()
    # Verificar los 5 KPIs presentes
    assert "patients_in_followup" in data
    assert "near_abandonment" in data
    assert "return_rate" in data
    assert "re_engaged_count_period" in data
    assert "nps_average" in data
    assert "tenant_id" in data
    assert "clinic_id" in data
    assert "snapshot_at" in data


def test_summary_no_phi_fields(client: TestClient) -> None:
    """SC-SUM-01-P: GET /summary response NO contiene PHI per-patient."""
    now = _now()
    mock_result = FidelizacionSummaryResponse(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        snapshot_at=now,
        patients_in_followup=10,
        near_abandonment=2,
        return_rate=0.5,
        re_engaged_count_period=5,
    )

    with patch("src.modules.vitalia.fidelizacion.api.fidelizacion_summary_endpoints._build_summary") as mock_fn:
        mock_fn.return_value = mock_result

        response = client.get(
            "/api/v1/vitalia/fidelizacion/summary",
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    body_str = response.text
    # PHI fields never in aggregate summary
    assert "patient_name" not in body_str
    assert "diagnosis" not in body_str
    assert "dni" not in body_str
    assert "comment" not in body_str


# ---------------------------------------------------------------------------
# SC-SUM-02: GET /summary — header obligatorio
# ---------------------------------------------------------------------------


def test_summary_missing_clinic_id_returns_422(client: TestClient) -> None:
    """SC-SUM-02: GET /summary sin X-Clinic-ID retorna 422."""
    headers_no_clinic = {
        "X-Tenant-ID": str(TENANT_ID),
        "X-User-ID": str(USER_ID),
        "X-User-Role": "nurse",
    }
    response = client.get(
        "/api/v1/vitalia/fidelizacion/summary",
        headers=headers_no_clinic,
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# SC-SUM-03: GET /activity-stream — items sin PHI
# ---------------------------------------------------------------------------


def test_activity_stream_returns_200(client: TestClient) -> None:
    """SC-SUM-03: GET /activity-stream retorna items recientes sin PHI."""
    now = _now()
    mock_result = ActivityStreamResponse(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        since=now - timedelta(minutes=5),
        items=[],
        total=0,
    )

    with patch("src.modules.vitalia.fidelizacion.api.fidelizacion_summary_endpoints._build_activity_stream") as mock_fn:
        mock_fn.return_value = mock_result

        response = client.get(
            "/api/v1/vitalia/fidelizacion/activity-stream",
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "tenant_id" in data


def test_activity_stream_no_phi_in_items(client: TestClient) -> None:
    """SC-SUM-03-P: GET /activity-stream items NO contienen PHI."""
    now = _now()
    mock_result = ActivityStreamResponse(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        since=now - timedelta(minutes=5),
        items=[],
        total=0,
    )

    with patch("src.modules.vitalia.fidelizacion.api.fidelizacion_summary_endpoints._build_activity_stream") as mock_fn:
        mock_fn.return_value = mock_result

        response = client.get(
            "/api/v1/vitalia/fidelizacion/activity-stream",
            headers=PHI_HEADERS,
        )

    assert response.status_code == 200
    body_str = response.text
    assert "diagnosis" not in body_str
    assert "patient_name" not in body_str
    assert "dni" not in body_str


# ---------------------------------------------------------------------------
# SC-SUM-04: GET /activity-stream — RBAC marketing = 403
# ---------------------------------------------------------------------------


def test_activity_stream_marketing_role_forbidden(client: TestClient) -> None:
    """SC-SUM-04: GET /activity-stream con role=marketing retorna 403."""
    response = client.get(
        "/api/v1/vitalia/fidelizacion/activity-stream",
        headers=MARKETING_HEADERS,
    )
    assert response.status_code == 403


# ---------------------------------------------------------------------------
# SC-SUM-05: GET /summary con role=nurse retorna 200
# ---------------------------------------------------------------------------


def test_summary_nurse_role_allowed(client: TestClient) -> None:
    """SC-SUM-05: GET /summary con role=nurse (PHI role) retorna 200."""
    now = _now()
    mock_result = FidelizacionSummaryResponse(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        snapshot_at=now,
        patients_in_followup=5,
        near_abandonment=1,
        return_rate=0.4,
        re_engaged_count_period=2,
    )

    with patch("src.modules.vitalia.fidelizacion.api.fidelizacion_summary_endpoints._build_summary") as mock_fn:
        mock_fn.return_value = mock_result

        response = client.get(
            "/api/v1/vitalia/fidelizacion/summary",
            headers=PHI_HEADERS,  # role=nurse
        )

    assert response.status_code == 200
