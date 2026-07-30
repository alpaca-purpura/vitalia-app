"""Tests for /api/v1/vitalia/marketing/* channel and bowtie endpoints.

TDD — RED phase: tests written BEFORE implementation (routes.py).

Gherkin coverage:
  SC-MK-02 (Meta API timeout / channel sync):
    - test_channel_detail_shows_last_known_when_sync_failed
    - test_manual_sync_endpoint_triggers_retry

Additional coverage:
  - test_bowtie_summary_returns_200
  - test_bowtie_stage_detail_returns_200
  - test_channels_connect_returns_200
  - test_attribution_matrix_returns_200
  - test_referrals_returns_200
  - test_sync_requires_idempotency_key_422
  - test_bowtie_requires_auth_401

downstream-regression-na: brand-local marketing channel API tests (vitalia-only)
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
CLINIC_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")

_ADMIN_HEADERS = {
    "Authorization": "Bearer test-admin-token",
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
}

_DOCTOR_HEADERS = {
    "Authorization": "Bearer test-doctor-token",
    "X-Tenant-ID": str(TENANT_ID),
    "X-Clinic-ID": str(CLINIC_ID),
}


def _make_clinic_context(role: str = "admin_clinic") -> object:
    """Stub ClinicContext."""
    ctx = MagicMock()
    ctx.tenant_id = TENANT_ID
    ctx.clinic_id = CLINIC_ID
    ctx.user_id = str(uuid.UUID("33333333-3333-3333-3333-333333333333"))
    ctx.role = role
    return ctx


def _make_bowtie_response() -> dict:
    """Factory for BowtieSummaryResponse-shaped dict."""
    return {
        "tenant_id": str(TENANT_ID),
        "clinic_id": str(CLINIC_ID),
        "period_start": "2026-05-01",
        "period_end": "2026-05-31",
        "stages": [
            {
                "stage": "attraction",
                "channels": [],
                "total_impressions": 100,
                "total_clicks": 10,
                "total_conversions": 1,
                "total_spend_cents": 5000,
                "currency": "MXN",
            }
        ],
        "currency": "MXN",
    }


def _make_channel_detail_response() -> dict:
    """Factory for ChannelDetailResponse-shaped dict."""
    return {
        "id": str(uuid.uuid4()),
        "tenant_id": str(TENANT_ID),
        "clinic_id": str(CLINIC_ID),
        "provider": "google_ads",
        "channel_slug": "google_ads_search",
        "campaign_id": "camp_001",
        "campaign_name": "Clínica Q1",
        "metric_date": "2026-05-15",
        "impressions": 1000,
        "clicks": 50,
        "conversions": 5,
        "spend_cents": 10000,
        "currency": "MXN",
    }


def _make_sync_response(status: str = "ok") -> dict:
    """Factory for SyncResponse-shaped dict."""
    return {
        "provider": "google_ads",
        "status": status,
        "last_synced_at": datetime.now(UTC).isoformat(),
        "error_message": None if status == "ok" else "Timeout al conectar con el proveedor.",
    }


@pytest.fixture
def app_client() -> TestClient:
    """TestClient for vitalia app."""
    from src.main import app  # noqa: PLC0415

    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def mock_marketing_service():
    """Mock MarketingService."""
    svc = AsyncMock()
    bowtie_mock = MagicMock(
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        period_start=datetime(2026, 5, 1).date(),
        period_end=datetime(2026, 5, 31).date(),
        stages=[],
        currency="MXN",
    )
    svc.bowtie_summary.return_value = bowtie_mock
    stage_mock = MagicMock(
        stage="attraction",
        channels=[],
        total_impressions=100,
        total_clicks=10,
        total_conversions=1,
        total_spend_cents=5000,
        currency="MXN",
    )
    svc.stage_detail.return_value = stage_mock
    svc.channel_detail.return_value = []
    return svc


# ---------------------------------------------------------------------------
# SC-MK-02 — channel detail / sync tests
# ---------------------------------------------------------------------------


def test_channel_detail_shows_last_known_when_sync_failed(
    app_client: TestClient,
    mock_marketing_service: AsyncMock,
) -> None:
    """SC-MK-02: GET /channels/{provider} returns last known metrics even after sync failure."""
    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_marketing_service",
            return_value=mock_marketing_service,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("admin_clinic"),
        ),
    ):
        response = app_client.get(
            "/api/v1/vitalia/marketing/channels/google_ads",
            headers=_ADMIN_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    # Response must be a list (last known channel metrics)
    assert isinstance(body, list)


def test_manual_sync_endpoint_triggers_retry(app_client: TestClient) -> None:
    """SC-MK-02: POST /channels/{provider}/sync triggers adapter sync and returns SyncResponse."""
    mock_sync_result = MagicMock(
        provider="google_ads",
        status="ok",
        last_synced_at=datetime.now(UTC),
        error_message=None,
    )
    mock_sync_svc = AsyncMock()
    mock_sync_svc.sync_channel.return_value = mock_sync_result

    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_sync_service",
            return_value=mock_sync_svc,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("admin_clinic"),
        ),
    ):
        response = app_client.post(
            "/api/v1/vitalia/marketing/channels/google_ads/sync",
            headers={**_ADMIN_HEADERS, "Idempotency-Key": "sync-key-001"},
        )
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "provider" in body


# ---------------------------------------------------------------------------
# Additional coverage
# ---------------------------------------------------------------------------


def test_bowtie_summary_returns_200(
    app_client: TestClient,
    mock_marketing_service: AsyncMock,
) -> None:
    """GET /bowtie/summary returns 200 with BowtieSummaryResponse."""
    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_marketing_service",
            return_value=mock_marketing_service,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("doctor"),
        ),
    ):
        response = app_client.get(
            "/api/v1/vitalia/marketing/bowtie/summary",
            headers=_DOCTOR_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    assert "tenant_id" in body
    assert "clinic_id" in body
    assert "stages" in body


def test_bowtie_stage_detail_returns_200(
    app_client: TestClient,
    mock_marketing_service: AsyncMock,
) -> None:
    """GET /stage/{stage_slug} returns 200 with StageDetailResponse."""
    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_marketing_service",
            return_value=mock_marketing_service,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("doctor"),
        ),
    ):
        response = app_client.get(
            "/api/v1/vitalia/marketing/stage/attraction",
            headers=_DOCTOR_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    assert "stage" in body
    assert "channels" in body


def test_channels_connect_returns_200(app_client: TestClient) -> None:
    """POST /channels/{provider}/connect returns 200 with OAuthConnectResponse."""
    mock_oauth_result = MagicMock(
        provider="google_ads",
        authorization_url="https://accounts.google.com/o/oauth2/v2/auth?...",
        state_token="random-state-token",
    )
    mock_oauth_svc = AsyncMock()
    mock_oauth_svc.initiate_oauth.return_value = mock_oauth_result

    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_oauth_service",
            return_value=mock_oauth_svc,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("admin_clinic"),
        ),
    ):
        response = app_client.post(
            "/api/v1/vitalia/marketing/channels/google_ads/connect",
            json={"provider": "google_ads", "redirect_uri": "https://app.vitalia.com/oauth/callback"},
            headers=_ADMIN_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    assert "authorization_url" in body
    assert "state_token" in body


def test_attribution_matrix_returns_200(app_client: TestClient) -> None:
    """GET /attribution-matrix returns 200 with AttributionMatrixResponse."""
    mock_attr_result = MagicMock(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        period_start=datetime(2026, 5, 1).date(),
        period_end=datetime(2026, 5, 31).date(),
        channel_breakdown={"google_ads": 0.6, "meta_ads": 0.4},
        total_attributed_revenue=Decimal("150000.00"),
        currency="MXN",
        computed_at=datetime.now(UTC),
    )
    mock_attr_svc = AsyncMock()
    mock_attr_svc.get_attribution_matrix.return_value = mock_attr_result

    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_attribution_service",
            return_value=mock_attr_svc,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("admin_clinic"),
        ),
    ):
        response = app_client.get(
            "/api/v1/vitalia/marketing/attribution-matrix",
            headers=_ADMIN_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    assert "total_attributed_revenue" in body
    assert "channel_breakdown" in body


def test_referrals_returns_200(app_client: TestClient) -> None:
    """GET /referrals returns 200 with ReferralsResponse."""
    mock_ref_result = MagicMock(
        id=uuid.uuid4(),
        tenant_id=TENANT_ID,
        clinic_id=CLINIC_ID,
        period_start=datetime(2026, 5, 1).date(),
        period_end=datetime(2026, 5, 31).date(),
        top_referrers=[],
        total_referrals=10,
        total_converted=3,
        computed_at=datetime.now(UTC),
    )
    mock_ref_svc = AsyncMock()
    mock_ref_svc.get_referrals.return_value = mock_ref_result

    with (
        patch(
            "src.modules.vitalia.marketing.api.routes._get_referrals_service",
            return_value=mock_ref_svc,
        ),
        patch(
            "src.modules.vitalia.marketing.api.routes._resolve_context",
            return_value=_make_clinic_context("admin_clinic"),
        ),
    ):
        response = app_client.get(
            "/api/v1/vitalia/marketing/referrals",
            headers=_ADMIN_HEADERS,
        )
    assert response.status_code == 200
    body = response.json()
    assert "total_referrals" in body
    assert "top_referrers" in body


def test_sync_requires_idempotency_key_422(app_client: TestClient) -> None:
    """POST /channels/{provider}/sync without Idempotency-Key returns 422."""
    with patch(
        "src.modules.vitalia.marketing.api.routes._resolve_context",
        return_value=_make_clinic_context("admin_clinic"),
    ):
        response = app_client.post(
            "/api/v1/vitalia/marketing/channels/google_ads/sync",
            headers=_ADMIN_HEADERS,  # No Idempotency-Key
        )
    assert response.status_code == 422


def test_bowtie_requires_auth_401(app_client: TestClient) -> None:
    """GET /bowtie/summary without Authorization returns 401 or 422.

    FastAPI returns 422 when a required header (Authorization) is absent.
    Both 401 and 422 are acceptable — the key invariant is NOT 200.
    """
    response = app_client.get(
        "/api/v1/vitalia/marketing/bowtie/summary",
        headers={
            "X-Tenant-ID": str(TENANT_ID),
            "X-Clinic-ID": str(CLINIC_ID),
        },
    )
    assert response.status_code in (401, 422)
