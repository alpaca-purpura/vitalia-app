"""Tests for CRM consent endpoints — POST /opt-out + PATCH /marketing-opt-in.

TDD RED phase: tests written BEFORE implementation per .claude/rules/tdd-mandatory.md.

Endpoints under test:
  POST   /api/v1/crm/patients/{patient_id}/opt-out
  PATCH  /api/v1/crm/patients/{patient_id}/marketing-opt-in

HIPAA-lite assertions:
  - Dual filter (X-Tenant-ID + X-Clinic-ID) both required
  - RBAC: opt-out = admin_clinic only; marketing-opt-in = doctor/nurse/admin_clinic
  - response_model= enforced (no PII bleed via extra fields)

downstream-regression-na: brand-local vitalia CRM consent API tests
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def anyio_backend():
    """Use asyncio backend for anyio."""
    return "asyncio"


@pytest.mark.anyio
class TestOptOutEndpoint:
    """POST /api/v1/crm/patients/{id}/opt-out — admin_clinic only."""

    async def test_opt_out_returns_200_for_admin_clinic(self) -> None:
        """admin_clinic can successfully opt out a patient."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:admin_clinic:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/crm/patients/{patient_id}/opt-out",
                json={"reason": "Solicitud del paciente para exclusión de marketing."},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 200

    async def test_opt_out_response_shape(self) -> None:
        """Response MUST match OptOutResponse schema (response_model enforcement)."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:admin_clinic:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/crm/patients/{patient_id}/opt-out",
                json={"reason": "Solicitud del paciente."},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "patient_id" in data
        assert "opted_out" in data
        assert data["opted_out"] is True
        assert "message" in data

    async def test_opt_out_returns_403_for_doctor_role(self) -> None:
        """Doctor role must be denied opt-out — only admin_clinic allowed."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:doctor:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/crm/patients/{patient_id}/opt-out",
                json={"reason": "Test."},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 403

    async def test_opt_out_returns_403_for_nurse_role(self) -> None:
        """Nurse role must be denied opt-out — only admin_clinic allowed."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:nurse:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/crm/patients/{patient_id}/opt-out",
                json={"reason": "Test."},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 403

    async def test_opt_out_returns_403_for_marketing_role(self) -> None:
        """Marketing role must be denied — not a PHI-allowed role."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:marketing:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/crm/patients/{patient_id}/opt-out",
                json={"reason": "Test."},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 403

    async def test_opt_out_requires_clinic_id_header(self) -> None:
        """Missing X-Clinic-ID header must return 422 (dual filter required)."""
        from src.main import app

        tenant_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:any:admin_clinic:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/crm/patients/{patient_id}/opt-out",
                json={"reason": "Test."},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    # X-Clinic-ID intentionally omitted
                },
            )

        assert response.status_code == 422

    async def test_opt_out_requires_reason_body(self) -> None:
        """Missing 'reason' in body must return 422 (Pydantic validation)."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:admin_clinic:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/crm/patients/{patient_id}/opt-out",
                json={},  # Missing reason field
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 422


@pytest.mark.anyio
class TestMarketingOptInEndpoint:
    """PATCH /api/v1/crm/patients/{id}/marketing-opt-in — doctor/nurse/admin_clinic."""

    async def test_marketing_opt_in_returns_200_for_doctor(self) -> None:
        """Doctor can update marketing consent successfully."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:doctor:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/crm/patients/{patient_id}/marketing-opt-in",
                json={"opt_in": True},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 200

    async def test_marketing_opt_in_returns_200_for_nurse(self) -> None:
        """Nurse can update marketing consent successfully."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:nurse:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/crm/patients/{patient_id}/marketing-opt-in",
                json={"opt_in": False},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 200

    async def test_marketing_opt_in_returns_200_for_admin_clinic(self) -> None:
        """admin_clinic can update marketing consent successfully."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:admin_clinic:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/crm/patients/{patient_id}/marketing-opt-in",
                json={"opt_in": True},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 200

    async def test_marketing_opt_in_returns_403_for_marketing_role(self) -> None:
        """Marketing role must be denied — not a PHI-allowed role."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:marketing:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/crm/patients/{patient_id}/marketing-opt-in",
                json={"opt_in": True},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 403

    async def test_marketing_opt_in_response_shape(self) -> None:
        """Response MUST include consent fields (response_model enforcement)."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:admin_clinic:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/crm/patients/{patient_id}/marketing-opt-in",
                json={"opt_in": True},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 200
        data = response.json()
        # Must return MarketingOptInResponse with patient_id + marketing_opt_in + message
        assert "patient_id" in data
        assert "marketing_opt_in" in data
        assert "message" in data

    async def test_marketing_opt_in_requires_opt_in_body_field(self) -> None:
        """Missing 'opt_in' field must return 422 (Pydantic validation)."""
        from src.main import app

        tenant_id = str(uuid4())
        clinic_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:{clinic_id}:admin_clinic:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/crm/patients/{patient_id}/marketing-opt-in",
                json={},  # Missing opt_in
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    "X-Clinic-ID": clinic_id,
                },
            )

        assert response.status_code == 422

    async def test_marketing_opt_in_requires_clinic_id_header(self) -> None:
        """Missing X-Clinic-ID header must return 422 (dual filter required)."""
        from src.main import app

        tenant_id = str(uuid4())
        patient_id = str(uuid4())
        token = f"stub:{tenant_id}:any:admin_clinic:{str(uuid4())}"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/crm/patients/{patient_id}/marketing-opt-in",
                json={"opt_in": True},
                headers={
                    "Authorization": f"Bearer {token}",
                    "X-Tenant-ID": tenant_id,
                    # X-Clinic-ID intentionally omitted
                },
            )

        assert response.status_code == 422
