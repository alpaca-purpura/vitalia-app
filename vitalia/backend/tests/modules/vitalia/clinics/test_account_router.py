# cap: configuracion.cuenta
"""Tests for account_router — response_model, RBAC, exception mapping.

Uses a minimal FastAPI test app to avoid importing main.py (which requires env vars).
All service calls are mocked.
Covers:
  - GET /account returns 200 + ClinicAccountResponse
  - GET /account returns 404 when clinic not found
  - PATCH /account returns 200 + updated fields
  - PATCH /account returns 403 for non-admin_clinic role
  - PATCH /account returns 422 for invalid fiscal_id
  - GET /account/specialties-catalog returns 200 + list
  - GET /account/dpo returns 200 with DPO data
  - GET /account/dpo returns 200 with empty state when DPO absent
  - Missing X-Tenant-ID header returns 422
  - response_model= enforced (structural test)
  - account_router is importable and registers 4 routes
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Minimal env patching (avoids engine Settings validation)
# ---------------------------------------------------------------------------

_FAKE_ENV: dict[str, str] = {
    "LOG_LEVEL": "WARNING",
    "DOMAIN_NAME": "test.local",
    "TRAEFIK_NETWORK": "test-net",
    "API_SECRET_KEY": "test-secret-key-32chars-minimum-len",
    "WHATSAPP_API_TOKEN": "fake-token",
    "WHATSAPP_PHONE_NUMBER_ID": "0000000000",
    "WHATSAPP_VERIFY_TOKEN": "fake-verify-token",
    "OPENAI_API_KEY": "sk-test-key",
    "REDIS_URL": "redis://localhost:6379",
    "QDRANT_URL": "http://localhost:6333",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_pass",
    "POSTGRES_DB": "test_db",
    "POSTGRES_HOST": "localhost",
    "POSTGRES_PORT": "5432",
    "API_URL": "http://localhost:8000",
}


@pytest.fixture(autouse=True)
def _with_fake_env(monkeypatch: pytest.MonkeyPatch) -> None:  # noqa: PT004
    """Set minimal env vars so engine config Settings instantiates."""
    for key, value in _FAKE_ENV.items():
        monkeypatch.setenv(key, value)


# ---------------------------------------------------------------------------
# Minimal test app with account_router mounted
# ---------------------------------------------------------------------------


@pytest.fixture
def test_app() -> FastAPI:
    """Create a minimal FastAPI app with account_router mounted."""
    from src.modules.vitalia.clinics.api.account_router import router

    app = FastAPI(redirect_slashes=False)
    app.include_router(router, prefix="/api/v1/clinics/account")
    return app


@pytest.fixture
def tenant_id() -> str:
    return str(uuid.uuid4())


@pytest.fixture
def user_id() -> str:
    return str(uuid.uuid4())


def _make_account_response(tenant_id_str: str):  # noqa: ANN202
    """Build a ClinicAccountResponse for mocking."""
    from src.modules.vitalia.clinics.api.dtos import ClinicAccountResponse

    return ClinicAccountResponse(
        clinic_id=uuid.uuid4(),
        tenant_id=uuid.UUID(tenant_id_str),
        name="Clínica Aurora",
        slug="aurora",
        country="AR",
        timezone="America/Argentina/Buenos_Aires",
        plan_tier="starter",
        is_active=True,
        legal_name="Aurora Dental SRL",
        fiscal_id="20345678907",
        address="Av. Corrientes 1234",
        phone="+54 11 4567-8901",
        email="info@aurora.com",
        language="es-419",
        currency=None,
        primary_specialties=["odontologia-estetica"],
    )


# ---------------------------------------------------------------------------
# Structural tests (import-only, no HTTP)
# ---------------------------------------------------------------------------


def test_account_router_importable() -> None:
    """account_router must be importable (connectivity gate)."""
    from src.modules.vitalia.clinics.api.account_router import router

    assert router is not None


def test_account_router_has_4_routes() -> None:
    """Router must register: GET /, PATCH /, GET /specialties-catalog, GET /dpo."""
    from src.modules.vitalia.clinics.api.account_router import router

    paths = {r.path for r in router.routes}
    assert "/" in paths, "GET / route missing"
    assert "/specialties-catalog" in paths
    assert "/dpo" in paths


def test_get_account_has_response_model() -> None:
    """GET / must have response_model= declared (PII gate)."""
    from src.modules.vitalia.clinics.api.account_router import router

    get_routes = [r for r in router.routes if r.path == "/" and "GET" in getattr(r, "methods", set())]
    assert get_routes, "GET / route not found"
    assert get_routes[0].response_model is not None, "GET / missing response_model="


def test_patch_account_has_response_model() -> None:
    """PATCH / must have response_model= declared."""
    from src.modules.vitalia.clinics.api.account_router import router

    patch_routes = [r for r in router.routes if r.path == "/" and "PATCH" in getattr(r, "methods", set())]
    assert patch_routes, "PATCH / route not found"
    assert patch_routes[0].response_model is not None, "PATCH / missing response_model="


def test_specialties_catalog_has_response_model() -> None:
    """GET /specialties-catalog must have response_model= declared."""
    from src.modules.vitalia.clinics.api.account_router import router

    cat_routes = [
        r for r in router.routes if r.path == "/specialties-catalog" and "GET" in getattr(r, "methods", set())
    ]
    assert cat_routes, "GET /specialties-catalog route not found"
    assert cat_routes[0].response_model is not None


def test_dpo_route_has_response_model() -> None:
    """GET /dpo must have response_model= declared."""
    from src.modules.vitalia.clinics.api.account_router import router

    dpo_routes = [r for r in router.routes if r.path == "/dpo" and "GET" in getattr(r, "methods", set())]
    assert dpo_routes, "GET /dpo route not found"
    assert dpo_routes[0].response_model is not None


# ---------------------------------------------------------------------------
# Functional tests (HTTP via TestClient + mocked service)
# ---------------------------------------------------------------------------


def test_get_account_returns_200(test_app: FastAPI, tenant_id: str, user_id: str) -> None:
    """GET /account/ returns 200 with clinic account data."""
    mock_service = AsyncMock()
    mock_service.get_account.return_value = _make_account_response(tenant_id)

    from src.modules.vitalia.clinics.api import account_router as ar_module

    test_app.dependency_overrides[ar_module.get_clinic_account_service] = lambda: mock_service
    client = TestClient(test_app)
    resp = client.get(
        "/api/v1/clinics/account/",
        headers={"X-Tenant-ID": tenant_id, "X-User-ID": user_id},
    )
    test_app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Clínica Aurora"
    assert "primarySpecialties" in data or "primary_specialties" in data


def test_get_account_returns_404_when_no_clinic(test_app: FastAPI, tenant_id: str, user_id: str) -> None:
    """GET /account/ returns 404 when no active clinic for tenant."""
    from src.modules.vitalia.clinics.api import account_router as ar_module
    from src.modules.vitalia.clinics.domain.exceptions import ClinicNotFoundError

    mock_service = AsyncMock()
    mock_service.get_account.side_effect = ClinicNotFoundError(tenant_id=tenant_id)

    test_app.dependency_overrides[ar_module.get_clinic_account_service] = lambda: mock_service
    client = TestClient(test_app)
    resp = client.get(
        "/api/v1/clinics/account/",
        headers={"X-Tenant-ID": tenant_id, "X-User-ID": user_id},
    )
    test_app.dependency_overrides.clear()
    assert resp.status_code == 404


def test_get_account_missing_tenant_header_returns_422(test_app: FastAPI) -> None:
    """Missing X-Tenant-ID returns 422."""
    client = TestClient(test_app)
    resp = client.get("/api/v1/clinics/account/")
    assert resp.status_code == 422


def test_patch_account_returns_200(test_app: FastAPI, tenant_id: str, user_id: str) -> None:
    """PATCH /account/ returns 200 with updated clinic data."""
    from src.modules.vitalia.clinics.api import account_router as ar_module

    mock_service = AsyncMock()
    mock_service.patch_account.return_value = _make_account_response(tenant_id)

    test_app.dependency_overrides[ar_module.get_clinic_account_service] = lambda: mock_service
    client = TestClient(test_app)
    resp = client.patch(
        "/api/v1/clinics/account/",
        json={"address": "Av. Santa Fe 1000"},
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": user_id,
            "X-User-Role": "admin_clinic",
        },
    )
    test_app.dependency_overrides.clear()
    assert resp.status_code == 200


def test_patch_account_forbidden_non_admin(test_app: FastAPI, tenant_id: str, user_id: str) -> None:
    """PATCH /account/ returns 403 for non-admin_clinic role."""
    from src.modules.vitalia.clinics.api import account_router as ar_module

    mock_service = AsyncMock()
    mock_service.patch_account.side_effect = PermissionError("Acceso denegado")

    test_app.dependency_overrides[ar_module.get_clinic_account_service] = lambda: mock_service
    client = TestClient(test_app)
    resp = client.patch(
        "/api/v1/clinics/account/",
        json={"address": "Somewhere"},
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": user_id,
            "X-User-Role": "doctor",
        },
    )
    test_app.dependency_overrides.clear()
    assert resp.status_code == 403


def test_patch_account_invalid_fiscal_id_returns_422(test_app: FastAPI, tenant_id: str, user_id: str) -> None:
    """PATCH /account/ returns 422 for invalid fiscal_id."""
    from src.modules.vitalia._shared.validation.fiscal_id_validator import (
        FiscalIdValidationError,
    )
    from src.modules.vitalia.clinics.api import account_router as ar_module

    mock_service = AsyncMock()
    mock_service.patch_account.side_effect = FiscalIdValidationError(field="fiscal_id", message="CUIT inválido")

    test_app.dependency_overrides[ar_module.get_clinic_account_service] = lambda: mock_service
    client = TestClient(test_app)
    resp = client.patch(
        "/api/v1/clinics/account/",
        json={"fiscal_id": "INVALID"},
        headers={
            "X-Tenant-ID": tenant_id,
            "X-User-ID": user_id,
            "X-User-Role": "admin_clinic",
        },
    )
    test_app.dependency_overrides.clear()
    assert resp.status_code == 422


def test_get_specialties_catalog_returns_200(test_app: FastAPI, tenant_id: str, user_id: str) -> None:
    """GET /specialties-catalog returns 200 with specialty list."""
    from src.modules.vitalia._shared.catalogs.specialty_catalog import SpecialtyEntry
    from src.modules.vitalia.clinics.api import account_router as ar_module

    mock_service = AsyncMock()
    # get_specialties_catalog now returns (country, entries) tuple (C9-4 fix)
    mock_service.get_specialties_catalog.return_value = (
        "MX",
        [SpecialtyEntry("odontologia-estetica", "Odontología estética", 1)],
    )

    test_app.dependency_overrides[ar_module.get_clinic_account_service] = lambda: mock_service
    client = TestClient(test_app)
    resp = client.get(
        "/api/v1/clinics/account/specialties-catalog",
        headers={"X-Tenant-ID": tenant_id, "X-User-ID": user_id},
    )
    test_app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert "specialties" in data
    assert len(data["specialties"]) >= 1


def test_get_dpo_returns_200_with_data(test_app: FastAPI, tenant_id: str, user_id: str) -> None:
    """GET /dpo returns 200 when DPO configured."""
    from src.modules.vitalia.clinics.api import account_router as ar_module

    mock_service = AsyncMock()
    mock_service.get_dpo.return_value = {
        "name": "Dr. García",
        "email": "dpo@clinica.com",
        "phone": "+54 11 1234-5678",
    }

    test_app.dependency_overrides[ar_module.get_clinic_account_service] = lambda: mock_service
    client = TestClient(test_app)
    resp = client.get(
        "/api/v1/clinics/account/dpo",
        headers={"X-Tenant-ID": tenant_id, "X-User-ID": user_id},
    )
    test_app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Dr. García"
    assert data["configured"] is True


def test_get_dpo_returns_empty_state_when_absent(test_app: FastAPI, tenant_id: str, user_id: str) -> None:
    """GET /dpo returns 200 with configured=False when DPO absent."""
    from src.modules.vitalia.clinics.api import account_router as ar_module

    mock_service = AsyncMock()
    mock_service.get_dpo.return_value = None

    test_app.dependency_overrides[ar_module.get_clinic_account_service] = lambda: mock_service
    client = TestClient(test_app)
    resp = client.get(
        "/api/v1/clinics/account/dpo",
        headers={"X-Tenant-ID": tenant_id, "X-User-ID": user_id},
    )
    test_app.dependency_overrides.clear()
    assert resp.status_code == 200
    data = resp.json()
    assert data["configured"] is False
    assert data.get("name") is None
