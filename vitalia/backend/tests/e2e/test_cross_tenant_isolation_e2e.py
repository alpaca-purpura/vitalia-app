"""E2E test — cross-tenant isolation (T-be-7 A2 + V-F-9).

A2 acceptance criterion: Cross-tenant request returns 403 or empty (NOT leak).

Per spec § 3.1.D (Scenario — adversarial cross-tenant attempt):
  Tenant-A tries to access Tenant-B resources via manipulated X-Tenant-ID header.
  Expected: 404 (not found — no leak) OR 403 (forbidden).
  NOT expected: 200 with Tenant-B data.

Tests verify the tenant_id propagation at the API layer ensures queries are
filtered by the authenticated tenant. Full isolation is verified at the
repository layer (test_booking_repository.py integration tests).

These tests run WITHOUT live Postgres — httpx.AsyncClient + ASGITransport.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app

TENANT_A = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
TENANT_B = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
HEADERS_A = {"X-Tenant-ID": TENANT_A}
HEADERS_B = {"X-Tenant-ID": TENANT_B}
# Audit log de compliance es admin-only (RBAC require_brand_owner_access) — el admin
# autorizado verificando el tenant-scope de SU clínica. La denegación por rol se cubre
# aparte en tests/modules/vitalia/compliance/test_compliance_endpoints_rbac.py.
HEADERS_A_ADMIN = {**HEADERS_A, "X-User-Role": "admin_clinic"}


@pytest.fixture
async def client():
    """httpx.AsyncClient targeting vitalia FastAPI app via ASGITransport."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestCrossTenantIsolation:
    """Spec § 3.1.D — cross-tenant adversarial scenarios."""

    async def test_tenant_a_cannot_see_tenant_b_patient(self, client: AsyncClient) -> None:
        """GET /patients/{id} with Tenant-A headers returns 404 for Tenant-B patient.

        A2: cross-tenant request returns 404 (not found) — NOT a data leak.
        The API layer propagates tenant_id from X-Tenant-ID header to service layer.
        Repository layer filters WHERE tenant_id = X-Tenant-ID (R2 tenant isolation).
        """
        patient_id = str(uuid4())

        # Tenant-A requests patient with Tenant-A headers (no leak — returns 404 stub)
        response_a = await client.get(
            f"/api/v1/vitalia/patients/{patient_id}",
            headers=HEADERS_A,
        )
        # 404 is correct: patient does not exist in Tenant-A's scope
        assert response_a.status_code == 404, (
            f"Expected 404 (not found in Tenant-A scope), got {response_a.status_code}"
        )

        # Tenant-B requests same patient with Tenant-B headers (also 404 — different tenant)
        response_b = await client.get(
            f"/api/v1/vitalia/patients/{patient_id}",
            headers=HEADERS_B,
        )
        assert response_b.status_code == 404

    async def test_tenant_a_cannot_see_tenant_b_treatment(self, client: AsyncClient) -> None:
        """GET /treatments/{id} with Tenant-A headers returns 404 for Tenant-B treatment."""
        treatment_id = str(uuid4())

        response = await client.get(
            f"/api/v1/vitalia/treatments/{treatment_id}",
            headers=HEADERS_A,
        )
        assert response.status_code == 404, (
            f"Expected 404 (tenant isolation — no cross-tenant leak), got {response.status_code}"
        )

    async def test_invalid_tenant_id_format_returns_422(self, client: AsyncClient) -> None:
        """X-Tenant-ID with invalid UUID format → 422 (not 500 crash).

        Adversarial: attacker sends malformed tenant_id header.
        Must be rejected at API boundary with 422.
        """
        response = await client.get(
            "/api/v1/vitalia/patients",
            headers={"X-Tenant-ID": "not-a-valid-uuid"},
        )
        assert response.status_code == 422, f"Malformed X-Tenant-ID must return 422, got {response.status_code}"

    async def test_sql_injection_tenant_id_returns_422(self, client: AsyncClient) -> None:
        """X-Tenant-ID with SQL injection attempt → 422.

        Adversarial: attacker tries to inject SQL via X-Tenant-ID.
        UUID parsing rejects non-UUID strings before any DB interaction.
        """
        response = await client.get(
            "/api/v1/vitalia/bookings",
            headers={"X-Tenant-ID": "' OR 1=1 --"},
        )
        assert response.status_code == 422

    async def test_empty_tenant_id_returns_422(self, client: AsyncClient) -> None:
        """Empty X-Tenant-ID → 422 (FastAPI header validation)."""
        response = await client.get(
            "/api/v1/vitalia/patients",
            headers={"X-Tenant-ID": ""},
        )
        assert response.status_code == 422

    async def test_tenant_id_injected_in_booking_creation(self, client: AsyncClient) -> None:
        """POST /bookings — tenant_id comes from X-Tenant-ID header, not request body.

        Security boundary: tenant_id is injected from header (authoritative).
        The request body does NOT have a tenant_id field (extra="forbid" in DTO).
        Attacker cannot escalate to another tenant by putting tenant_id in body.
        """
        doctor_id = str(uuid4())
        offer_id = str(uuid4())
        patient_id = str(uuid4())

        # Extra field "tenant_id" in body → 422 (extra="forbid" DTO validation)
        response = await client.post(
            "/api/v1/vitalia/bookings",
            json={
                "offer_id": offer_id,
                "doctor_id": doctor_id,
                "patient_id": patient_id,
                "slot_iso": "2026-12-15T10:00:00Z",
                "delivery_channel": "whatsapp",
                "tenant_id": TENANT_B,  # attacker tries to inject different tenant
            },
            headers=HEADERS_A,
        )
        assert response.status_code == 422, (
            "Extra 'tenant_id' in body must be rejected (extra='forbid' — security boundary)"
        )

    async def test_onboarding_profile_extra_field_rejected(self, client: AsyncClient) -> None:
        """POST /onboarding/clinic-profile with extra fields → 422 (extra='forbid')."""
        response = await client.post(
            "/api/v1/vitalia/onboarding/clinic-profile",
            json={
                "clinic_name": "Test",
                "clinic_type": "dental",
                "country": "AR",
                "city": "Buenos Aires",
                "plan_tier": "starter",
                "admin_override": True,  # malicious extra field
            },
            headers=HEADERS_A,
        )
        assert response.status_code == 422, (
            "Extra fields must be rejected (extra='forbid' — prevents parameter pollution)"
        )

    async def test_compliance_events_tenant_scoped(self, client: AsyncClient) -> None:
        """GET /medical-compliance/events returns empty list for Tenant-A (no cross-tenant data)."""
        response = await client.get(
            "/api/v1/vitalia/medical-compliance/events",
            headers=HEADERS_A_ADMIN,
        )
        assert response.status_code == 200
        body = response.json()
        assert "events" in body
        # Empty list is correct for unknown tenant in stub (not a 200 with Tenant-B data)
        assert isinstance(body["events"], list)
        assert body["total"] == 0

    async def test_compliance_export_csv_tenant_scoped(self, client: AsyncClient) -> None:
        """GET /medical-compliance/export-csv returns 200 (empty CSV — tenant-scoped)."""
        response = await client.get(
            "/api/v1/vitalia/medical-compliance/export-csv",
            headers=HEADERS_A_ADMIN,
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")

    async def test_redirect_slashes_false_post_bookings(self, client: AsyncClient) -> None:
        """POST /bookings/ (trailing slash) does NOT redirect to 307.

        redirect_slashes=False ensures Next.js POST body is not dropped.
        Trailing slash variant should return 404/405 (not 307 redirect).
        """
        doctor_id = str(uuid4())
        offer_id = str(uuid4())
        patient_id = str(uuid4())

        response = await client.post(
            "/api/v1/vitalia/bookings/",  # trailing slash
            json={
                "offer_id": offer_id,
                "doctor_id": doctor_id,
                "patient_id": patient_id,
                "slot_iso": "2026-12-15T10:00:00Z",
                "delivery_channel": "whatsapp",
            },
            headers=HEADERS_A,
            follow_redirects=False,  # Do NOT follow redirect — detect 307
        )
        # Must NOT be 307 (redirect_slashes=False enforced in main.py)
        assert response.status_code != 307, (
            "307 redirect detected — redirect_slashes=False must be set in FastAPI app "
            "(main.py) to prevent Next.js body drop"
        )

    async def test_treatments_followup_state_not_found(self, client: AsyncClient) -> None:
        """GET /treatments/{id}/followup for non-existent ID → 404."""
        treatment_id = str(uuid4())
        response = await client.get(
            f"/api/v1/vitalia/treatments/{treatment_id}/followup",
            headers=HEADERS_A,
        )
        assert response.status_code == 404

    async def test_all_endpoints_have_json_response_shape(self, client: AsyncClient) -> None:
        """Sanity: all list endpoints return JSON with expected shape (no raw ORM dump)."""
        list_endpoints = [
            "/api/v1/vitalia/bookings",
            "/api/v1/vitalia/treatments",
            "/api/v1/vitalia/patients",
            "/api/v1/vitalia/medical-compliance/events",
            "/api/v1/vitalia/medical-compliance/consent-records",
            "/api/v1/vitalia/onboarding/plans",
            "/api/v1/vitalia/onboarding/status",
        ]
        # HEADERS_A_ADMIN: /medical-compliance/events es admin-only (RBAC); el resto
        # de endpoints ignora X-User-Role → enviarlo es inocuo para todos.
        for endpoint in list_endpoints:
            response = await client.get(endpoint, headers=HEADERS_A_ADMIN)
            assert response.status_code == 200, (
                f"Expected 200 for {endpoint}, got {response.status_code}: {response.text}"
            )
            body = response.json()
            assert isinstance(body, dict), f"Expected dict response from {endpoint}, got {type(body)}"
