"""Unit tests for admin helpers API — internal DB state verification endpoints.

TDD: RED tests defined per vitalia-adopt-luana-core-iam story.

Security tests verify:
- X-Internal-Token header required (403 without it)
- 500 if VITALIA_INTERNAL_API_TOKEN not configured
- No PHI in responses (only counts, exists flags)
- Tenant isolation enforced via X-Tenant-ID header

downstream-regression-na: brand-local admin helpers API tests
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def anyio_backend():
    return "asyncio"


INTERNAL_TOKEN = "test-internal-token-abc123"


@pytest.mark.anyio
class TestAdminHelpersAuthGate:
    """Authentication gate — X-Internal-Token required."""

    async def test_audit_count_without_token_returns_403(self, monkeypatch) -> None:
        """GET /audit-log/count without X-Internal-Token → 403."""
        monkeypatch.setenv("VITALIA_INTERNAL_API_TOKEN", INTERNAL_TOKEN)
        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/vitalia/admin/audit-log/count",
                params={"action": "user.created"},
                headers={"X-Tenant-ID": str(uuid4())},
                # No X-Internal-Token
            )
        assert response.status_code == 403

    async def test_audit_count_with_wrong_token_returns_403(self, monkeypatch) -> None:
        """GET /audit-log/count with wrong token → 403."""
        monkeypatch.setenv("VITALIA_INTERNAL_API_TOKEN", INTERNAL_TOKEN)
        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/vitalia/admin/audit-log/count",
                params={"action": "user.created"},
                headers={
                    "X-Tenant-ID": str(uuid4()),
                    "X-Internal-Token": "WRONG_TOKEN",
                },
            )
        assert response.status_code == 403

    async def test_tenants_exists_without_token_returns_403(self, monkeypatch) -> None:
        """GET /tenants/exists without X-Internal-Token → 403."""
        monkeypatch.setenv("VITALIA_INTERNAL_API_TOKEN", INTERNAL_TOKEN)
        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/vitalia/admin/tenants/exists",
                params={"slug": "test-tenant"},
                # No X-Internal-Token
            )
        assert response.status_code == 403

    async def test_token_not_configured_returns_500(self, monkeypatch) -> None:
        """GET /audit-log/count when VITALIA_INTERNAL_API_TOKEN not set → 500."""
        monkeypatch.delenv("VITALIA_INTERNAL_API_TOKEN", raising=False)
        from importlib import reload

        import src.modules.vitalia.admin.api.admin_helpers_router as helpers_mod

        reload(helpers_mod)

        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/vitalia/admin/audit-log/count",
                params={"action": "user.created"},
                headers={
                    "X-Tenant-ID": str(uuid4()),
                    "X-Internal-Token": "any-token",
                },
            )
        assert response.status_code == 500
        assert response.json()["detail"]["error"] == "configuration_error"


@pytest.mark.anyio
class TestAdminHelpersResponseSchema:
    """Response schemas — no PHI, only metadata."""

    def test_audit_count_response_model_schema(self) -> None:
        """AuditLogCountResponse has {tenant_id, action, count} — no payload content.

        Verifies the Pydantic response model directly without hitting DB.
        DB-dependent integration test is in tests/integration/.
        """
        from src.modules.vitalia.admin.api.admin_helpers_router import AuditLogCountResponse

        response = AuditLogCountResponse(tenant_id="uuid-123", action="user.created", count=3)
        data = response.model_dump()

        assert "tenant_id" in data
        assert "action" in data
        assert "count" in data
        # HIPAA: no "payload" content field in response
        assert "payload" not in data
        assert "payload_redacted" not in data
        assert data["count"] == 3

    def test_clinic_exists_response_model_schema(self) -> None:
        """ClinicExistsResponse has {clinic_id, tenant_id, slug, exists} — no PHI."""
        from src.modules.vitalia.admin.api.admin_helpers_router import ClinicExistsResponse

        response = ClinicExistsResponse(
            clinic_id=None,
            tenant_id="uuid-456",
            slug="nonexistent-clinic",
            exists=False,
        )
        data = response.model_dump()

        assert data["tenant_id"] == "uuid-456"
        assert data["exists"] is False
        assert data["slug"] == "nonexistent-clinic"
        # No PHI fields
        assert "diagnosis" not in data
        assert "treatment_plan" not in data

    async def test_clinic_exists_endpoint_missing_tenant_id(self, monkeypatch) -> None:
        """clinics/exists without X-Tenant-ID → validation error (422)."""
        monkeypatch.setenv("VITALIA_INTERNAL_API_TOKEN", INTERNAL_TOKEN)
        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(
                "/api/v1/vitalia/admin/clinics/exists",
                params={"slug": "test-clinic"},
                headers={
                    # Missing X-Tenant-ID
                    "X-Internal-Token": INTERNAL_TOKEN,
                },
            )
        # Missing X-Tenant-ID → FastAPI validation error (422) or 403
        assert response.status_code in (422, 400, 403)


@pytest.mark.anyio
class TestAdminHelpersNotInOpenAPISchema:
    """Admin helper endpoints must be hidden from OpenAPI docs."""

    async def test_endpoints_not_in_openapi_schema(self, monkeypatch) -> None:
        """All admin helper routes have include_in_schema=False."""
        monkeypatch.setenv("VITALIA_INTERNAL_API_TOKEN", INTERNAL_TOKEN)
        from src.main import app

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        paths = schema.get("paths", {})

        # Admin helper routes must NOT appear in OpenAPI
        assert "/api/v1/vitalia/admin/audit-log/count" not in paths
        assert "/api/v1/vitalia/admin/tenants/exists" not in paths
        assert "/api/v1/vitalia/admin/clinics/exists" not in paths
