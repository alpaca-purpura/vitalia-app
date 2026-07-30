# cap: clinics.lisa.doctores
"""Regression tests — T-FIX-1-BE: malformed UUID headers must return 422, not 500.

Bug reproduced (2026-06-01): GET /api/v1/vitalia/clinics/doctors with non-UUID
X-Clinic-ID → ValueError: badly formed hexadecimal UUID string → HTTP 500 ASGI.

These tests MUST fail (RED) before the fix is applied, and PASS (GREEN) after.
All endpoints that accept X-Tenant-ID / X-Clinic-ID are covered.
"""

from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

VALID_TENANT = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
VALID_CLINIC = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
VALID_DOCTOR = "cccccccc-cccc-cccc-cccc-cccccccccccc"
VALID_BLOCK = "dddddddd-dddd-dddd-dddd-dddddddddddd"
VALID_USER = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
# Provide an admin_clinic role header so RBAC passes on mutation endpoints
ADMIN_ROLE = "admin_clinic"

BAD_UUID = "not-a-uuid"


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """Minimal app with doctors_router — dependencies overridden to avoid DB."""
    from src.modules.vitalia.clinics.api.doctors_router import _get_db, router

    test_app = FastAPI(redirect_slashes=False)
    test_app.include_router(router, prefix="/api/v1/vitalia/clinics/doctors")

    # Override DB dep with a no-op so we never hit Postgres
    async def _fake_db():  # noqa: ANN202
        yield None  # type: ignore[misc]

    test_app.dependency_overrides[_get_db] = _fake_db
    return TestClient(test_app, raise_server_exceptions=False)


# ── list_doctors ──────────────────────────────────────────────────────────────


class TestListDoctorsHeaderValidation:
    """GET / — list doctors endpoint header validation."""

    def test_malformed_clinic_id_returns_422(self, client: TestClient) -> None:
        """X-Clinic-ID='not-a-uuid' → 422 (was 500 before fix)."""
        resp = client.get(
            "/api/v1/vitalia/clinics/doctors/",
            headers={
                "X-Tenant-ID": VALID_TENANT,
                "X-Clinic-ID": BAD_UUID,
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for malformed X-Clinic-ID, got {resp.status_code}. Body: {resp.text[:300]}"
        )

    def test_malformed_tenant_id_returns_422(self, client: TestClient) -> None:
        """X-Tenant-ID='not-a-uuid' → 422 (was 500 before fix)."""
        resp = client.get(
            "/api/v1/vitalia/clinics/doctors/",
            headers={
                "X-Tenant-ID": BAD_UUID,
                "X-Clinic-ID": VALID_CLINIC,
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for malformed X-Tenant-ID, got {resp.status_code}. Body: {resp.text[:300]}"
        )

    def test_missing_clinic_id_returns_422(self, client: TestClient) -> None:
        """Missing X-Clinic-ID header → 422 (not 500)."""
        resp = client.get(
            "/api/v1/vitalia/clinics/doctors/",
            headers={"X-Tenant-ID": VALID_TENANT},
        )
        assert resp.status_code == 422, f"Expected 422 for missing X-Clinic-ID, got {resp.status_code}."

    def test_missing_tenant_id_returns_422(self, client: TestClient) -> None:
        """Missing X-Tenant-ID header → 422 (not 500)."""
        resp = client.get(
            "/api/v1/vitalia/clinics/doctors/",
            headers={"X-Clinic-ID": VALID_CLINIC},
        )
        assert resp.status_code == 422, f"Expected 422 for missing X-Tenant-ID, got {resp.status_code}."

    def test_empty_clinic_id_returns_422(self, client: TestClient) -> None:
        """X-Clinic-ID='' (empty string) → 422 (not 500)."""
        resp = client.get(
            "/api/v1/vitalia/clinics/doctors/",
            headers={
                "X-Tenant-ID": VALID_TENANT,
                "X-Clinic-ID": "",
            },
        )
        assert resp.status_code == 422, f"Expected 422 for empty X-Clinic-ID, got {resp.status_code}."


# ── get_doctor ────────────────────────────────────────────────────────────────


class TestGetDoctorHeaderValidation:
    """GET /{doctor_id} — get doctor detail endpoint header validation."""

    def test_malformed_clinic_id_returns_422(self, client: TestClient) -> None:
        """X-Clinic-ID='not-a-uuid' → 422 for get_doctor endpoint."""
        resp = client.get(
            f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}",
            headers={
                "X-Tenant-ID": VALID_TENANT,
                "X-Clinic-ID": BAD_UUID,
                "X-User-ID": VALID_USER,
            },
        )
        assert resp.status_code == 422, f"Expected 422 for malformed X-Clinic-ID in get_doctor, got {resp.status_code}."

    def test_malformed_tenant_id_returns_422(self, client: TestClient) -> None:
        """X-Tenant-ID='not-a-uuid' → 422 for get_doctor endpoint."""
        resp = client.get(
            f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}",
            headers={
                "X-Tenant-ID": BAD_UUID,
                "X-Clinic-ID": VALID_CLINIC,
                "X-User-ID": VALID_USER,
            },
        )
        assert resp.status_code == 422, f"Expected 422 for malformed X-Tenant-ID in get_doctor, got {resp.status_code}."


# ── patch_doctor ──────────────────────────────────────────────────────────────


class TestPatchDoctorHeaderValidation:
    """PATCH /{doctor_id} — patch doctor endpoint header validation.

    These endpoints use RBAC via Depends(require_brand_owner_access(...)).
    We include X-User-Role: admin_clinic so RBAC passes and UUID validation
    is exercised (FastAPI resolves deps in parallel; RBAC fires on missing role first).
    """

    def test_malformed_clinic_id_returns_422(self, client: TestClient) -> None:
        """X-Clinic-ID='not-a-uuid' → 422 for patch_doctor endpoint (with valid RBAC role)."""
        resp = client.patch(
            f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}",
            headers={
                "X-Tenant-ID": VALID_TENANT,
                "X-Clinic-ID": BAD_UUID,
                "X-User-ID": VALID_USER,
                "X-User-Role": ADMIN_ROLE,
            },
            json={},
        )
        assert resp.status_code == 422, (
            f"Expected 422 for malformed X-Clinic-ID in patch_doctor, got {resp.status_code}."
        )

    def test_malformed_tenant_id_returns_422(self, client: TestClient) -> None:
        """X-Tenant-ID='not-a-uuid' → 422 for patch_doctor endpoint (with valid RBAC role)."""
        resp = client.patch(
            f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}",
            headers={
                "X-Tenant-ID": BAD_UUID,
                "X-Clinic-ID": VALID_CLINIC,
                "X-User-ID": VALID_USER,
                "X-User-Role": ADMIN_ROLE,
            },
            json={},
        )
        assert resp.status_code == 422, (
            f"Expected 422 for malformed X-Tenant-ID in patch_doctor, got {resp.status_code}."
        )


# ── availability blocks sub-routes ───────────────────────────────────────────


class TestAvailabilityBlocksHeaderValidation:
    """Availability block sub-routes — header validation."""

    def test_list_blocks_malformed_clinic_id_returns_422(self, client: TestClient) -> None:
        """GET /{id}/availability-blocks with bad X-Clinic-ID → 422."""
        resp = client.get(
            f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}/availability-blocks",
            headers={
                "X-Tenant-ID": VALID_TENANT,
                "X-Clinic-ID": BAD_UUID,
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for malformed X-Clinic-ID in list_blocks, got {resp.status_code}."
        )

    def test_list_blocks_malformed_tenant_id_returns_422(self, client: TestClient) -> None:
        """GET /{id}/availability-blocks with bad X-Tenant-ID → 422."""
        resp = client.get(
            f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}/availability-blocks",
            headers={
                "X-Tenant-ID": BAD_UUID,
                "X-Clinic-ID": VALID_CLINIC,
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for malformed X-Tenant-ID in list_blocks, got {resp.status_code}."
        )


# ── delete block ──────────────────────────────────────────────────────────────


class TestDeleteBlockHeaderValidation:
    """DELETE /{doctor_id}/availability-blocks/{block_id} — header validation."""

    def test_malformed_clinic_id_returns_422(self, client: TestClient) -> None:
        """DELETE block with bad X-Clinic-ID → 422 (with valid RBAC role)."""
        resp = client.delete(
            f"/api/v1/vitalia/clinics/doctors/{VALID_DOCTOR}/availability-blocks/{VALID_BLOCK}",
            headers={
                "X-Tenant-ID": VALID_TENANT,
                "X-Clinic-ID": BAD_UUID,
                "X-User-ID": VALID_USER,
                "X-User-Role": ADMIN_ROLE,
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for malformed X-Clinic-ID in delete_block, got {resp.status_code}."
        )
