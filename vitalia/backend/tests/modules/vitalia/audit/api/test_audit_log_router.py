"""Tests for POST /api/v1/vitalia/audit-log — FE PHI-read audit ingestion.

TDD RED→GREEN: written BEFORE the router (tdd-mandatory.md).

Context (vitalia-fase2-adrian-inbox · audit-log-404 twin-fix, Chris decision A):
  The FE `AuditedSection` (PHI-read audit on `ContactSidebar` mount) POSTed to
  /api/v1/vitalia/audit-log but NO router served it → 404 → tripped the
  anti-burbuja e2e gate AND lost the HIPAA-lite PHI-read audit row. This endpoint
  wires the FE beacon to `AsyncAuditWriter` (sync pre-response write, dual filter).

  NOTE (follow-up, NOT this story): the architecturally-ideal place to audit the
  PHI read is server-side in `crm.get_conversation_detail` (where the lead PHI is
  decrypted). That file is under the concurrent embudo session's `code:crm` lock,
  so the FE-beacon endpoint is the unblocked path now.

Coverage:
  - test_returns_201_and_writes_audit (happy: authed → row written, dual filter)
  - test_resolves_actor_uuid_from_clerk_sub (user_id col = users.id UUID, not sub)
  - test_invalid_resource_id_rejected_422 (resource_id must be UUID — CAST safety)
  - test_missing_auth_header_rejected (PHI audit is tenant-scoped, not public)

downstream-regression-na: brand-local vitalia audit API test (vitalia-only)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_ROUTER = "src.modules.vitalia.audit.api.audit_log_router"

TENANT_ID = uuid.UUID("e69a691d-070e-5caf-a053-6e74642ec100")
CLINIC_ID = uuid.UUID("f035be5b-0ac4-5210-8fc3-395650ca2b83")
ACTOR_UUID = uuid.UUID("33333333-3333-3333-3333-333333333333")
RESOURCE_UUID = uuid.UUID("0d2313ff-72fa-45be-9e8e-e14eb0c3633e")

_HEADERS = {
    "Authorization": "Bearer test-owner-token",
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
}


def _make_ctx(role: str = "owner") -> MagicMock:
    """Stub ClinicContext — ctx.user_id is the Clerk sub (non-UUID), as in prod."""
    ctx = MagicMock()
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.user_id = "user_clerk_abc"  # Clerk sub — NOT a UUID
    ctx.role = role
    return ctx


@pytest.fixture
def app_client() -> TestClient:
    """TestClient for the vitalia app (server exceptions surfaced as 500, not raised)."""
    from src.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=False)


def test_returns_201_and_writes_audit(app_client: TestClient) -> None:
    """Happy path: authenticated PHI-read beacon → audit row written + 201."""
    writer = MagicMock()
    writer.write = AsyncMock(return_value=None)

    with (
        patch(f"{_ROUTER}._resolve_context", new=AsyncMock(return_value=_make_ctx())),
        patch(f"{_ROUTER}.resolve_user_uuid_from_clerk_id", new=AsyncMock(return_value=ACTOR_UUID)),
        patch(f"{_ROUTER}.AsyncAuditWriter", return_value=writer),
    ):
        response = app_client.post(
            "/api/v1/vitalia/audit-log",
            headers=_HEADERS,
            json={
                "action": "view",
                "resourceType": "patient_profile",
                "resourceId": str(RESOURCE_UUID),
                "userId": "user_clerk_abc",
            },
        )

    assert response.status_code == 201, response.text
    assert response.json() == {"recorded": True}
    writer.write.assert_awaited_once()


def test_resolves_actor_uuid_from_clerk_sub(app_client: TestClient) -> None:
    """Dual filter + actor: row uses RESOLVED tenant/clinic + users.id UUID (not the sub)."""
    writer = MagicMock()
    writer.write = AsyncMock(return_value=None)

    with (
        patch(f"{_ROUTER}._resolve_context", new=AsyncMock(return_value=_make_ctx())),
        patch(f"{_ROUTER}.resolve_user_uuid_from_clerk_id", new=AsyncMock(return_value=ACTOR_UUID)),
        patch(f"{_ROUTER}.AsyncAuditWriter", return_value=writer),
    ):
        response = app_client.post(
            "/api/v1/vitalia/audit-log",
            headers=_HEADERS,
            json={
                "action": "view",
                "resourceType": "patient_profile",
                "resourceId": str(RESOURCE_UUID),
                "userId": "user_clerk_abc",
            },
        )

    assert response.status_code == 201, response.text
    _, kwargs = writer.write.call_args
    assert kwargs["tenant_id"] == TENANT_ID
    assert kwargs["clinic_id"] == CLINIC_ID
    assert kwargs["user_id"] == ACTOR_UUID  # users.id UUID, NOT the Clerk sub
    assert kwargs["resource_id"] == RESOURCE_UUID
    assert kwargs["resource_type"] == "patient_profile"
    assert kwargs["action"] == "view"


def test_invalid_resource_id_rejected_422(app_client: TestClient) -> None:
    """resource_id must be a UUID (audit_writer CASTs resource_id AS uuid)."""
    writer = MagicMock()
    writer.write = AsyncMock(return_value=None)

    with (
        patch(f"{_ROUTER}._resolve_context", new=AsyncMock(return_value=_make_ctx())),
        patch(f"{_ROUTER}.resolve_user_uuid_from_clerk_id", new=AsyncMock(return_value=ACTOR_UUID)),
        patch(f"{_ROUTER}.AsyncAuditWriter", return_value=writer),
    ):
        response = app_client.post(
            "/api/v1/vitalia/audit-log",
            headers=_HEADERS,
            json={
                "action": "view",
                "resourceType": "patient_profile",
                "resourceId": "not-a-uuid",
                "userId": "user_clerk_abc",
            },
        )

    assert response.status_code == 422, response.text
    writer.write.assert_not_awaited()


def test_missing_auth_header_rejected(app_client: TestClient) -> None:
    """No Authorization header → rejected (PHI audit is tenant-scoped, not public)."""
    response = app_client.post(
        "/api/v1/vitalia/audit-log",
        headers={"X-Tenant-ID": str(TENANT_ID), "X-Clinic-ID": str(CLINIC_ID)},
        json={
            "action": "view",
            "resourceType": "patient_profile",
            "resourceId": str(RESOURCE_UUID),
        },
    )
    assert response.status_code in (401, 422), response.text
