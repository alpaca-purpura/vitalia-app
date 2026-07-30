"""RED tests for GoogleAdsAdapter — same resilience contract as MetaAdsAdapter.

TDD: these tests FAIL until adapter.py is implemented.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.modules.vitalia.connections.google_ads import adapter as _google_module
from src.modules.vitalia.connections.google_ads.adapter import (
    CircuitBreakerOpenError,
    GoogleAdsAdapter,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = "tenant-abc"
CLINIC_ID = "clinic-001"


@pytest.fixture(autouse=True)
def reset_circuit_breaker_state() -> None:
    """Reset shared in-memory circuit breaker state between tests."""
    _google_module._breaker_registry.clear()
    yield
    _google_module._breaker_registry.clear()


@pytest.fixture()
def adapter() -> GoogleAdsAdapter:
    """GoogleAdsAdapter wired with test ENV config."""
    return GoogleAdsAdapter(
        client_id="google-client-id",
        client_secret="google-client-secret",
        redirect_uri="https://app.vitalia.test/oauth/google/callback",
        developer_token="dev-token-xyz",
    )


@pytest.fixture()
def adapter_fresh() -> GoogleAdsAdapter:
    """Fresh adapter — circuit breaker state not shared with other tests."""
    return GoogleAdsAdapter(
        client_id="gid",
        client_secret="gsecret",
        redirect_uri="https://app.vitalia.test/oauth/google/callback",
        developer_token="dev-tok",
    )


# ---------------------------------------------------------------------------
# OAuth flows
# ---------------------------------------------------------------------------


def test_authorize_url_returns_google_oauth_url(adapter: GoogleAdsAdapter) -> None:
    """authorize_url() returns accounts.google.com URL with required OAuth params."""
    url = adapter.authorize_url(tenant_id=TENANT_ID, state="csrf-state-token")
    assert "google.com" in url or "accounts.google" in url
    assert "client_id=google-client-id" in url
    assert "state=csrf-state-token" in url
    assert "redirect_uri" in url
    # Google Ads requires specific scope
    assert "scope" in url


@pytest.mark.asyncio
async def test_callback_exchanges_code_for_token(adapter: GoogleAdsAdapter) -> None:
    """callback() exchanges authorization code for access_token + refresh_token."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "access_token": "ya29.access",
        "refresh_token": "1//refresh",
        "expires_in": 3600,
        "token_type": "Bearer",
    }

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(return_value=mock_response)

        result = await adapter.callback(
            code="auth-code-xyz",
            tenant_id=TENANT_ID,
        )

    assert result["access_token"] == "ya29.access"
    assert "refresh_token" in result


@pytest.mark.asyncio
async def test_list_accessible_customers_returns_list(adapter: GoogleAdsAdapter) -> None:
    """list_accessible_customers() returns customer resource names."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"resourceNames": ["customers/123456789"]}

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_response)

        customers = await adapter.list_accessible_customers(
            access_token="ya29.access",
            tenant_id=TENANT_ID,
        )

    assert len(customers) == 1
    assert customers[0] == "customers/123456789"


@pytest.mark.asyncio
async def test_fetch_campaign_metrics_via_gaql(adapter: GoogleAdsAdapter) -> None:
    """fetch_campaign_metrics() uses GAQL query and returns list of campaign rows."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "results": [
            {
                "campaign": {"id": "111", "name": "Blanqueamiento"},
                "metrics": {"impressions": "5000", "costMicros": "10000000"},
                "segments": {"date": "2026-01-15"},
            }
        ]
    }

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(return_value=mock_response)

        rows = await adapter.fetch_campaign_metrics(
            access_token="ya29.access",
            customer_id="123456789",
            tenant_id=TENANT_ID,
            since="2026-01-01",
            until="2026-01-31",
        )

    assert len(rows) == 1
    assert rows[0]["campaign"]["id"] == "111"


# ---------------------------------------------------------------------------
# SC-MK-02 equivalent — timeout
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_timeout_30s_raises(adapter: GoogleAdsAdapter) -> None:
    """fetch_campaign_metrics raises TimeoutException on slow Google API response."""
    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

        with pytest.raises(httpx.TimeoutException):
            await adapter.fetch_campaign_metrics(
                access_token="ya29.access",
                customer_id="123456789",
                tenant_id=TENANT_ID,
                since="2026-01-01",
                until="2026-01-31",
            )


# ---------------------------------------------------------------------------
# Circuit breaker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_breaker_after_5_consecutive_failures(adapter_fresh: GoogleAdsAdapter) -> None:
    """After 5 consecutive failures for tenant, circuit opens → CircuitBreakerOpenError."""
    adapter = adapter_fresh

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        for _ in range(5):
            with pytest.raises((httpx.ConnectError, CircuitBreakerOpenError)):
                await adapter.fetch_campaign_metrics(
                    access_token="ya29.access",
                    customer_id="123456789",
                    tenant_id=TENANT_ID,
                    since="2026-01-01",
                    until="2026-01-31",
                )

    # 6th call → circuit open
    with pytest.raises(CircuitBreakerOpenError):
        await adapter.fetch_campaign_metrics(
            access_token="ya29.access",
            customer_id="123456789",
            tenant_id=TENANT_ID,
            since="2026-01-01",
            until="2026-01-31",
        )


@pytest.mark.asyncio
async def test_circuit_breaker_isolated_per_tenant(adapter_fresh: GoogleAdsAdapter) -> None:
    """Circuit breaker state is isolated per tenant_id."""
    adapter = adapter_fresh
    tenant_a = "tenant-a"
    tenant_b = "tenant-b"

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(side_effect=httpx.ConnectError("refused"))

        for _ in range(5):
            with pytest.raises((httpx.ConnectError, CircuitBreakerOpenError)):
                await adapter.fetch_campaign_metrics(
                    access_token="tok",
                    customer_id="123",
                    tenant_id=tenant_a,
                    since="2026-01-01",
                    until="2026-01-31",
                )

        # tenant_b should still get underlying error, not circuit
        with pytest.raises(httpx.ConnectError):
            await adapter.fetch_campaign_metrics(
                access_token="tok",
                customer_id="123",
                tenant_id=tenant_b,
                since="2026-01-01",
                until="2026-01-31",
            )


# ---------------------------------------------------------------------------
# Retry behavior
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_campaign_metrics_retries_on_server_error(adapter_fresh: GoogleAdsAdapter) -> None:
    """fetch_campaign_metrics retries up to 3× on 5xx responses."""
    # Use isolated tenant to avoid circuit breaker state from other tests
    retry_tenant = "tenant-retry-test-google"
    mock_error_resp = MagicMock(spec=httpx.Response)
    mock_error_resp.status_code = 500
    mock_error_resp.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("500", request=MagicMock(), response=mock_error_resp)
    )

    mock_ok = MagicMock(spec=httpx.Response)
    mock_ok.raise_for_status = MagicMock()
    mock_ok.json.return_value = {"results": []}

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.post = AsyncMock(side_effect=[mock_error_resp, mock_error_resp, mock_ok])

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter_fresh.fetch_campaign_metrics(
                access_token="ya29.access",
                customer_id="123456789",
                tenant_id=retry_tenant,
                since="2026-01-01",
                until="2026-01-31",
            )

    assert isinstance(result, list)
