"""TDD RED→GREEN repro · P6 access-control gap (cap-coherence sweep 2026-06-06).

GAP: `GET /api/v1/vitalia/medical-compliance/events` y `/export-csv` (exporta el
audit log HIPAA-lite entero) NO tenían autorización por rol — solo auth Clerk JWT.
Cualquier rol autenticado (patient/marketing/nurse/receptionist) podía listar/exportar
el log de compliance. La cap `compliance.hipaa-lite-defensive-stack` declara
`requires_role: [admin_clinic, staff_vitalia]` + `forbidden_roles: [patient, marketing,
nurse, receptionist]` — nada de eso estaba enforced en código (cross_check_4 SOFT lo
flaggeó). `hipaa-lite.md`: "@require_phi_access en TODOS endpoints PHI · RBAC strict".

FIX: gatear ambos endpoints con `require_brand_owner_access(roles={admin_clinic,
staff_vitalia})` (lee X-User-Role → 403). Las roles enforced == las roles de la cap.

downstream-regression-na: brand-local vitalia compliance API test (vitalia-only).
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

TENANT_ID = uuid.UUID("e69a691d-070e-5caf-a053-6e74642ec100")

_EVENTS = "/api/v1/vitalia/medical-compliance/events"
_EXPORT = "/api/v1/vitalia/medical-compliance/export-csv"

# Roles que la cap declara forbidden (+ rol vacío = sin header).
FORBIDDEN_ROLES = ["patient", "marketing", "nurse", "receptionist", "doctor", ""]
# Roles que la cap declara requires_role.
ALLOWED_ROLES = ["admin_clinic", "staff_vitalia"]


@pytest.fixture
def client() -> TestClient:
    from src.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=False)


def _headers(role: str) -> dict[str, str]:
    return {"X-Tenant-ID": str(TENANT_ID), "X-User-Role": role}


@pytest.mark.parametrize("role", FORBIDDEN_ROLES)
def test_compliance_events_forbidden_role_gets_403(client: TestClient, role: str) -> None:
    resp = client.get(_EVENTS, headers=_headers(role))
    assert resp.status_code == 403, f"role={role!r} debería ser 403, fue {resp.status_code}: {resp.text}"


@pytest.mark.parametrize("role", FORBIDDEN_ROLES)
def test_compliance_export_csv_forbidden_role_gets_403(client: TestClient, role: str) -> None:
    resp = client.get(_EXPORT, headers=_headers(role))
    assert resp.status_code == 403, f"role={role!r} debería ser 403, fue {resp.status_code}: {resp.text}"


@pytest.mark.parametrize("role", ALLOWED_ROLES)
def test_compliance_events_allowed_role_not_403(client: TestClient, role: str) -> None:
    resp = client.get(_EVENTS, headers=_headers(role))
    assert resp.status_code != 403, f"role={role!r} NO debería ser 403, fue {resp.status_code}: {resp.text}"


@pytest.mark.parametrize("role", ALLOWED_ROLES)
def test_compliance_export_csv_allowed_role_not_403(client: TestClient, role: str) -> None:
    resp = client.get(_EXPORT, headers=_headers(role))
    assert resp.status_code != 403, f"role={role!r} NO debería ser 403, fue {resp.status_code}: {resp.text}"
