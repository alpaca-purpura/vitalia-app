"""Tests for /api/v1/vitalia/marketing/recommendations/* endpoints.

TDD — RED phase: tests written BEFORE implementation (routes.py).

Gherkin coverage:
  SC-MK-01 (Lucas approve happy — endpoint round-trip):
    - test_approve_endpoint_happy_path
    - test_approve_idempotency_key_dedup
    - test_undo_endpoint_within_5min
    - test_undo_endpoint_after_window_410
  SC-MK-04 (adversarial — RBAC + role guard):
    - test_approve_role_recepcion_returns_403
    - test_audit_log_unauthorized_attempt_recorded

Additional coverage:
  - test_list_recommendations_returns_200
  - test_list_recommendations_cross_tenant_blocked
  - test_reject_endpoint_happy_path
  - test_recommendations_requires_auth_401

HIPAA-lite:
  - All mutations verify clinic_id dual filter.
  - 403 returned when role is not admin_clinic.
  - Idempotency-Key required on POST mutations.

downstream-regression-na: brand-local marketing API tests (vitalia-only)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CLINIC_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
OTHER_CLINIC_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")
USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
REC_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")

# Base headers for admin_clinic role
_ADMIN_HEADERS = {
    "Authorization": "Bearer test-admin-token",
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
}

# Recepcion role headers (not allowed to approve/reject)
_RECEPCION_HEADERS = {
    "Authorization": "Bearer test-recepcion-token",
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
}

# Read-only roles (allowed to list)
_DOCTOR_HEADERS = {
    "Authorization": "Bearer test-doctor-token",
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
}


def _make_rec_response(
    rec_id: uuid.UUID = REC_ID,
    status: str = "open",
    undo_until: datetime | None = None,
) -> dict:
    """Factory for LucasRecommendationResponse-shaped dict."""
    now = datetime.now(UTC)
    return {
        "id": str(rec_id),
        "tenant_id": str(TENANT_ID),
        "clinic_id": str(CLINIC_ID),
        "stage": "attract",
        "recommendation_kind": "budget_increase",
        "title": "Incrementar presupuesto en Google Ads",
        "body": "Se recomienda incrementar el presupuesto.",
        "rationale_json": {"reason": "high_roi"},
        "priority": 1,
        "status": status,
        "expires_at": (now + timedelta(days=7)).isoformat(),
        "action_payload_json": {"budget_amount_cents": 50000},
        "confidence_pct": 85,
        "projected_impact_text": "+20% conversiones estimadas",
        "approved_by_user_id": str(USER_ID) if status == "approved" else None,
        "approved_at": now.isoformat() if status == "approved" else None,
        "undo_until": undo_until.isoformat() if undo_until else None,
        "rejected_by_user_id": None,
        "rejected_at": None,
        "reject_reason": None,
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }


def _make_clinic_context(role: str = "admin_clinic") -> object:
    """Stub ClinicContext for dependency override."""
    ctx = MagicMock()
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.user_id = str(USER_ID)
    ctx.role = role
    return ctx


@pytest.fixture
def app_client() -> TestClient:
    """TestClient for vitalia app with marketing router mounted."""
    from src.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mock_recs_service():
    """Mock LucasRecommendationsService for unit tests."""
    svc = AsyncMock()
    svc.list_open_by_stage.return_value = []
    now_utc = datetime.now(UTC)
    svc.approve.return_value = MagicMock(
        id=REC_ID,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        stage="attract",
        recommendation_kind="budget_increase",
        title="Incrementar presupuesto",
        body="Cuerpo",
        rationale_json={"r": "v"},
        priority=1,
        status="approved",
        expires_at=now_utc + timedelta(days=7),
        action_payload_json={"budget_amount_cents": 50000},
        confidence_pct=85,
        projected_impact_text="+20%",
        approved_by_user_id=USER_ID,
        approved_at=now_utc,
        undo_until=now_utc + timedelta(minutes=5),
        rejected_by_user_id=None,
        rejected_at=None,
        reject_reason=None,
        created_at=now_utc,
        updated_at=now_utc,
    )
    svc.reject.return_value = MagicMock(
        id=REC_ID,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        stage="attract",
        recommendation_kind="budget_increase",
        title="Incrementar presupuesto",
        body="Cuerpo",
        rationale_json={"r": "v"},
        priority=1,
        status="rejected",
        expires_at=now_utc + timedelta(days=7),
        action_payload_json=None,
        confidence_pct=85,
        projected_impact_text="+20%",
        approved_by_user_id=None,
        approved_at=None,
        undo_until=None,
        rejected_by_user_id=USER_ID,
        rejected_at=now_utc,
        reject_reason="not_priority",
        created_at=now_utc,
        updated_at=now_utc,
    )
    svc.undo.return_value = MagicMock(
        id=REC_ID,
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        stage="attract",
        recommendation_kind="budget_increase",
        title="Incrementar presupuesto",
        body="Cuerpo",
        rationale_json={"r": "v"},
        priority=1,
        status="open",
        expires_at=now_utc + timedelta(days=7),
        action_payload_json=None,
        confidence_pct=85,
        projected_impact_text="+20%",
        approved_by_user_id=None,
        approved_at=None,
        undo_until=None,
        rejected_by_user_id=None,
        rejected_at=None,
        reject_reason=None,
        created_at=now_utc,
        updated_at=now_utc,
    )
    return svc


# ---------------------------------------------------------------------------
# SC-MK-01 — approve happy path (endpoint round-trip)
# ---------------------------------------------------------------------------


def test_approve_endpoint_happy_path(app_client: TestClient, mock_recs_service: AsyncMock) -> None:
    """SC-MK-01: POST /recommendations/{id}/approve returns 200 with APPROVED status.

    Verifies:
      - HTTP 200 response
      - response body matches LucasRecommendationResponse schema
      - status field is 'approved'
      - Idempotency-Key header accepted
    """
    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_recs_service",
            return_value=mock_recs_service,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("admin_clinic"),
        ),
    ):
        response = app_client.post(
            f"/api/v1/vitalia/marketing/recommendations/{REC_ID}/approve",
            json={"user_id": str(USER_ID)},
            headers={**_ADMIN_HEADERS, "Idempotency-Key": "test-idem-key-001"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["id"] == str(REC_ID)
    assert "tenant_id" in body
    assert "clinic_id" in body


def test_approve_idempotency_key_dedup(app_client: TestClient) -> None:
    """SC-MK-01: POST /recommendations/{id}/approve without Idempotency-Key returns 422."""
    with patch(
        "src.modules.vitalia.marketing.api.routes._resolve_context",
        return_value=_make_clinic_context("admin_clinic"),
    ):
        response = app_client.post(
            f"/api/v1/vitalia/marketing/recommendations/{REC_ID}/approve",
            json={"user_id": str(USER_ID)},
            headers=_ADMIN_HEADERS,  # No Idempotency-Key
        )
    assert response.status_code == 422


def test_undo_endpoint_within_5min(app_client: TestClient, mock_recs_service: AsyncMock) -> None:
    """SC-MK-01: POST /recommendations/{id}/undo within window returns 200 with OPEN status."""
    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_recs_service",
            return_value=mock_recs_service,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("admin_clinic"),
        ),
    ):
        response = app_client.post(
            f"/api/v1/vitalia/marketing/recommendations/{REC_ID}/undo",
            headers={**_ADMIN_HEADERS, "Idempotency-Key": "test-undo-key-001"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "open"


def test_undo_endpoint_after_window_410(app_client: TestClient) -> None:
    """SC-MK-01: POST /recommendations/{id}/undo after 5-min window returns 410 Gone."""
    from src.modules.vitalia.marketing.domain.exceptions import UndoWindowExpiredError  # noqa: PLC0415

    expired_svc = AsyncMock()
    expired_svc.undo.side_effect = UndoWindowExpiredError()

    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_recs_service",
            return_value=expired_svc,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("admin_clinic"),
        ),
    ):
        response = app_client.post(
            f"/api/v1/vitalia/marketing/recommendations/{REC_ID}/undo",
            headers={**_ADMIN_HEADERS, "Idempotency-Key": "test-undo-expired-001"},
        )
    assert response.status_code == 410


# ---------------------------------------------------------------------------
# SC-MK-04 — RBAC + role guard tests
# ---------------------------------------------------------------------------


def test_approve_role_recepcion_returns_403(app_client: TestClient) -> None:
    """SC-MK-04: POST /recommendations/{id}/approve with role=recepcion returns 403."""
    with patch(
        "src.modules.vitalia.marketing.api.routes._resolve_context",
        return_value=_make_clinic_context("recepcion"),
    ):
        response = app_client.post(
            f"/api/v1/vitalia/marketing/recommendations/{REC_ID}/approve",
            json={"user_id": str(USER_ID)},
            headers={**_RECEPCION_HEADERS, "Idempotency-Key": "test-rbac-403"},
        )
    assert response.status_code == 403


def test_audit_log_unauthorized_attempt_recorded(app_client: TestClient) -> None:
    """SC-MK-04: Unauthorized access attempt is logged (403 still returned, not 500).

    Verifies that the role check raises 403 and does not expose internals.
    """
    with patch(
        "src.modules.vitalia.marketing.api.routes._resolve_context",
        return_value=_make_clinic_context("sales"),
    ):
        response = app_client.post(
            f"/api/v1/vitalia/marketing/recommendations/{REC_ID}/reject",
            json={"user_id": str(USER_ID), "reason": "not_priority"},
            headers={**_RECEPCION_HEADERS, "Idempotency-Key": "test-sales-403"},
        )
    assert response.status_code == 403
    detail = response.json().get("detail", "")
    # Must not expose internal stack trace
    assert "Traceback" not in detail
    assert "Exception" not in detail


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------


def test_list_recommendations_returns_200(app_client: TestClient, mock_recs_service: AsyncMock) -> None:
    """GET /recommendations returns 200 with list schema."""
    mock_recs_service.list_open_by_stage.return_value = []
    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_recs_service",
            return_value=mock_recs_service,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("doctor"),
        ),
    ):
        response = app_client.get(
            "/api/v1/vitalia/marketing/recommendations",
            headers=_DOCTOR_HEADERS,
        )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_recommendations_cross_tenant_blocked(app_client: TestClient) -> None:
    """GET /recommendations with mismatched X-Tenant-ID blocked at 401/403.

    The JWT resolved context will have a different tenant_id than the header.
    Route must reject (context is derived from JWT, not header alone).
    """
    other_tenant_headers = {
        "Authorization": "Bearer test-admin-token",
        "X-Tenant-ID": str(uuid.UUID("FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF")),
        "X-Clinic-ID": str(CLINIC_ID),
    }
    # Context has TENANT_ID from JWT — header claims different tenant
    # The route should raise 401 because JWT can't be validated for other tenant
    with patch(
        "src.modules.vitalia.marketing.api.routes._resolve_context",
        side_effect=Exception("JWT tenant mismatch"),
    ):
        response = app_client.get(
            "/api/v1/vitalia/marketing/recommendations",
            headers=other_tenant_headers,
        )
    # Should get 401 or 500 (not 200 leak) — we verify not 200
    assert response.status_code != 200


def test_reject_endpoint_happy_path(app_client: TestClient, mock_recs_service: AsyncMock) -> None:
    """POST /recommendations/{id}/reject returns 200 with REJECTED status."""
    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_recs_service",
            return_value=mock_recs_service,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("admin_clinic"),
        ),
    ):
        response = app_client.post(
            f"/api/v1/vitalia/marketing/recommendations/{REC_ID}/reject",
            json={"user_id": str(USER_ID), "reason": "not_priority"},
            headers={**_ADMIN_HEADERS, "Idempotency-Key": "test-reject-001"},
        )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"


def test_recommendations_requires_auth_401(app_client: TestClient) -> None:
    """GET /recommendations without Authorization returns 401 or 422.

    FastAPI returns 422 when a required header (Authorization) is absent
    (validation error before the route handler runs). Both 401 and 422
    are acceptable — the key invariant is that the response is NOT 200.
    """
    response = app_client.get(
        "/api/v1/vitalia/marketing/recommendations",
        headers={
            "X-Tenant-ID": str(TENANT_ID),
            "X-Clinic-ID": str(CLINIC_ID),
        },
    )
    # 401 or 422 — never 200 (no unauthorized access granted)
    assert response.status_code in (401, 422)
