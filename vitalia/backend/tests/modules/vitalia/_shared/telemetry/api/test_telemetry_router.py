"""Tests for POST /api/telemetry/growth-studio-event ingestion endpoint.

TDD RED→GREEN: written BEFORE the router (tdd-mandatory.md).

Context (vitalia-fase2-adrian-inbox · telemetry-404 side-fix, Chris option A):
  The FE `mateo/lib/telemetry.ts` POSTs to /api/telemetry/growth-studio-event but
  NO router served it → 404 app-wide → tripped the anti-burbuja e2e gate. This
  endpoint wires the FE ingestion to the existing server-side GrowthStudioEmitter
  (fire-forget), tenant-scoped via the same ClinicResolver as the rest.

Coverage:
  - test_ingest_returns_202_and_calls_emitter (happy: authed → 202 + persist)
  - test_emitter_receives_tenant_and_clinic_from_context (tenant isolation)
  - test_invalid_event_type_rejected_422 (event_type pattern guard)
  - test_event_type_too_long_rejected_422 (≤64 chars guard)
  - test_missing_auth_header_rejected (auth required — secure write)

downstream-regression-na: brand-local vitalia telemetry API test (vitalia-only)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

_ROUTER = "src.modules.vitalia._shared.telemetry.api.telemetry_router"

TENANT_ID = uuid.UUID("e69a691d-070e-5caf-a053-6e74642ec100")
CLINIC_ID = uuid.UUID("f035be5b-0ac4-5210-8fc3-395650ca2b83")

_HEADERS = {
    "Authorization": "Bearer test-owner-token",
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
}


def _make_ctx(role: str = "owner") -> MagicMock:
    """Stub ClinicContext (resolution is patched — DB/JWT not exercised here)."""
    ctx = MagicMock()
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.user_id = "user_clerk_abc"
    ctx.role = role
    return ctx


@pytest.fixture
def app_client() -> TestClient:
    """TestClient for the vitalia app (server exceptions surfaced as 500, not raised)."""
    from src.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=False)


def test_ingest_returns_202_and_calls_emitter(app_client: TestClient) -> None:
    """Happy path: authenticated POST → 202 Accepted + emitter invoked (fire-forget)."""
    emitter = MagicMock()
    emitter.emit_event = AsyncMock(return_value=None)

    with (
        patch(f"{_ROUTER}._resolve_context", new=AsyncMock(return_value=_make_ctx())),
        patch(f"{_ROUTER}.GrowthStudioEmitter", return_value=emitter),
    ):
        response = app_client.post(
            "/api/telemetry/growth-studio-event",
            headers=_HEADERS,
            json={
                "event_type": "agenda_viewed",
                "occurred_at": "2026-06-04T12:00:00Z",
                "payload": {"view_mode": "semana"},
            },
        )

    assert response.status_code == 202, response.text
    assert response.json() == {"accepted": True}
    emitter.emit_event.assert_awaited_once()


def test_emitter_receives_tenant_and_clinic_from_context(app_client: TestClient) -> None:
    """Tenant isolation: the event is persisted under the RESOLVED tenant/clinic, not the body."""
    emitter = MagicMock()
    emitter.emit_event = AsyncMock(return_value=None)

    with (
        patch(f"{_ROUTER}._resolve_context", new=AsyncMock(return_value=_make_ctx())),
        patch(f"{_ROUTER}.GrowthStudioEmitter", return_value=emitter),
    ):
        response = app_client.post(
            "/api/telemetry/growth-studio-event",
            headers=_HEADERS,
            json={
                "event_type": "agenda_viewed",
                "occurred_at": "2026-06-04T12:00:00Z",
                "payload": {"view_mode": "mes", "tenant_id": "SPOOFED"},
            },
        )

    assert response.status_code == 202, response.text
    _, kwargs = emitter.emit_event.call_args
    assert kwargs["event_type"] == "agenda_viewed"
    assert kwargs["tenant_id"] == TENANT_ID
    assert kwargs["clinic_id"] == CLINIC_ID
    # actor user_id is not derived from the (non-UUID) clerk sub — telemetry is anon-ok
    assert kwargs["user_id"] is None
    assert kwargs["props"] == {"view_mode": "mes", "tenant_id": "SPOOFED"}


def test_invalid_event_type_rejected_422(app_client: TestClient) -> None:
    """event_type must be a snake_case identifier (no spaces / PHI free-text)."""
    emitter = MagicMock()
    emitter.emit_event = AsyncMock(return_value=None)

    with (
        patch(f"{_ROUTER}._resolve_context", new=AsyncMock(return_value=_make_ctx())),
        patch(f"{_ROUTER}.GrowthStudioEmitter", return_value=emitter),
    ):
        response = app_client.post(
            "/api/telemetry/growth-studio-event",
            headers=_HEADERS,
            json={
                "event_type": "Bad Event! María",
                "occurred_at": "2026-06-04T12:00:00Z",
                "payload": {},
            },
        )

    assert response.status_code == 422, response.text
    emitter.emit_event.assert_not_awaited()


def test_event_type_too_long_rejected_422(app_client: TestClient) -> None:
    """event_type capped at 64 chars (DB column width)."""
    with patch(f"{_ROUTER}._resolve_context", new=AsyncMock(return_value=_make_ctx())):
        response = app_client.post(
            "/api/telemetry/growth-studio-event",
            headers=_HEADERS,
            json={
                "event_type": "a" * 65,
                "occurred_at": "2026-06-04T12:00:00Z",
                "payload": {},
            },
        )
    assert response.status_code == 422, response.text


def test_missing_auth_header_rejected(app_client: TestClient) -> None:
    """No Authorization header → request rejected (telemetry write is tenant-scoped, not public)."""
    response = app_client.post(
        "/api/telemetry/growth-studio-event",
        headers={"X-Tenant-ID": str(TENANT_ID), "X-Clinic-ID": str(CLINIC_ID)},
        json={"event_type": "agenda_viewed", "occurred_at": "2026-06-04T12:00:00Z", "payload": {}},
    )
    assert response.status_code in (401, 422), response.text
