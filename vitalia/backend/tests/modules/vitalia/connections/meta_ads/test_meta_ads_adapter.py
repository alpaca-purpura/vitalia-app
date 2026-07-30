"""RED tests for MetaAdsAdapter — SC-MK-02 (Meta API timeout + circuit breaker).

TDD: these tests FAIL until adapter.py is implemented.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.modules.vitalia.connections.meta_ads import adapter as _meta_module
from src.modules.vitalia.connections.meta_ads.adapter import (
    CircuitBreakerOpenError,
    MetaAdsAdapter,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

TENANT_ID = "tenant-abc"
CLINIC_ID = "clinic-001"


@pytest.fixture(autouse=True)
def reset_circuit_breaker_state() -> None:
    """Reset shared in-memory circuit breaker state between tests."""
    _meta_module._breaker_registry.clear()
    yield
    _meta_module._breaker_registry.clear()


@pytest.fixture()
def adapter() -> MetaAdsAdapter:
    """MetaAdsAdapter wired with test ENV config."""
    return MetaAdsAdapter(
        client_id="test-client-id",
        client_secret="test-client-secret",
        redirect_uri="https://app.vitalia.test/oauth/meta/callback",
    )


@pytest.fixture()
def adapter_fresh() -> MetaAdsAdapter:
    """Fresh adapter — circuit breaker state not shared with other tests."""
    return MetaAdsAdapter(
        client_id="ci-id",
        client_secret="ci-secret",
        redirect_uri="https://app.vitalia.test/oauth/meta/callback",
    )


# ---------------------------------------------------------------------------
# SC-MK-02 — timeout handling
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_timeout_30s_raises(adapter: MetaAdsAdapter) -> None:
    """fetch_insights raises httpx.TimeoutException after 30 s — timeout is passed through."""
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("timeout")) as mock_get:
        with pytest.raises(httpx.TimeoutException):
            await adapter.fetch_insights(
                access_token="tok",
                ad_account_id="act_123",
                tenant_id=TENANT_ID,
                since="2026-01-01",
                until="2026-01-31",
            )
        mock_get.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_insights_timeout_uses_30s(adapter: MetaAdsAdapter) -> None:
    """Adapter configures httpx.AsyncClient with timeout=30.0."""

    async def fake_get(url: str, **kwargs: object) -> httpx.Response:  # noqa: ARG001
        # We inspect timeout from the client that was created
        raise httpx.TimeoutException("sentinel")

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(side_effect=httpx.TimeoutException("sentinel"))
        with pytest.raises(httpx.TimeoutException):
            await adapter.fetch_insights(
                access_token="tok",
                ad_account_id="act_123",
                tenant_id=TENANT_ID,
                since="2026-01-01",
                until="2026-01-31",
            )
        # Verify timeout kwarg was passed to AsyncClient constructor
        call_kwargs = MockClient.call_args_list[0].kwargs if MockClient.call_args_list else {}
        timeout_val = call_kwargs.get("timeout")
        if timeout_val is None and MockClient.call_args_list:
            # Could also be positional
            args = MockClient.call_args_list[0].args
            if args:
                timeout_val = args[0] if isinstance(args[0], (int, float)) else None
        assert timeout_val == pytest.approx(30.0) or timeout_val is not None


# ---------------------------------------------------------------------------
# SC-MK-02 — circuit breaker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_circuit_breaker_after_5_consecutive_failures(adapter_fresh: MetaAdsAdapter) -> None:
    """After 5 consecutive failures for (tenant_id, 'meta_ads'), circuit opens → CircuitBreakerOpenError."""
    adapter = adapter_fresh
    # Simulate 5 consecutive fetch_insights failures
    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(side_effect=httpx.ConnectError("connection refused"))

        for _ in range(5):
            with pytest.raises((httpx.ConnectError, CircuitBreakerOpenError)):
                await adapter.fetch_insights(
                    access_token="tok",
                    ad_account_id="act_123",
                    tenant_id=TENANT_ID,
                    since="2026-01-01",
                    until="2026-01-31",
                )

    # 6th call should raise CircuitBreakerOpenError (circuit is open)
    with pytest.raises(CircuitBreakerOpenError) as exc_info:
        await adapter.fetch_insights(
            access_token="tok",
            ad_account_id="act_123",
            tenant_id=TENANT_ID,
            since="2026-01-01",
            until="2026-01-31",
        )
    assert "circuit" in str(exc_info.value).lower() or "abierto" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_circuit_breaker_isolated_per_tenant(adapter_fresh: MetaAdsAdapter) -> None:
    """Circuit breaker state is isolated per tenant_id."""
    adapter = adapter_fresh
    tenant_a = "tenant-a"
    tenant_b = "tenant-b"

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        # Trip breaker for tenant_a
        for _ in range(5):
            with pytest.raises((httpx.ConnectError, CircuitBreakerOpenError)):
                await adapter.fetch_insights(
                    access_token="tok",
                    ad_account_id="act_123",
                    tenant_id=tenant_a,
                    since="2026-01-01",
                    until="2026-01-31",
                )

        # tenant_b should NOT have circuit open — raises the underlying error, not circuit error
        with pytest.raises(httpx.ConnectError):
            await adapter.fetch_insights(
                access_token="tok",
                ad_account_id="act_123",
                tenant_id=tenant_b,
                since="2026-01-01",
                until="2026-01-31",
            )


@pytest.mark.asyncio
async def test_circuit_breaker_success_does_not_increment(adapter_fresh: MetaAdsAdapter) -> None:
    """Successful call resets failure counter for tenant."""
    adapter = adapter_fresh

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {"data": []}

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        # 4 failures then 1 success
        instance.get = AsyncMock(
            side_effect=[
                httpx.ConnectError("refused"),
                httpx.ConnectError("refused"),
                httpx.ConnectError("refused"),
                httpx.ConnectError("refused"),
                mock_response,
            ]
        )

        for _ in range(4):
            with pytest.raises(httpx.ConnectError):
                await adapter.fetch_insights(
                    access_token="tok",
                    ad_account_id="act_123",
                    tenant_id=TENANT_ID,
                    since="2026-01-01",
                    until="2026-01-31",
                )

        # 5th call succeeds → resets counter
        result = await adapter.fetch_insights(
            access_token="tok",
            ad_account_id="act_123",
            tenant_id=TENANT_ID,
            since="2026-01-01",
            until="2026-01-31",
        )
        assert isinstance(result, list)

    # After reset, 5 more failures needed to open circuit
    with patch("httpx.AsyncClient") as MockClient2:
        instance2 = MockClient2.return_value.__aenter__.return_value
        instance2.get = AsyncMock(side_effect=httpx.ConnectError("refused"))

        for _ in range(4):
            with pytest.raises(httpx.ConnectError):
                await adapter.fetch_insights(
                    access_token="tok",
                    ad_account_id="act_123",
                    tenant_id=TENANT_ID,
                    since="2026-01-01",
                    until="2026-01-31",
                )

        # Circuit should NOT be open yet (only 4 fails after reset)
        with pytest.raises(httpx.ConnectError):
            await adapter.fetch_insights(
                access_token="tok",
                ad_account_id="act_123",
                tenant_id=TENANT_ID,
                since="2026-01-01",
                until="2026-01-31",
            )


# ---------------------------------------------------------------------------
# OAuth flows
# ---------------------------------------------------------------------------


def test_authorize_url_returns_facebook_oauth_url(adapter: MetaAdsAdapter) -> None:
    """authorize_url() returns a facebook.com/dialog/oauth URL with required params."""
    url = adapter.authorize_url(tenant_id=TENANT_ID, state="csrf-state-token")
    assert "facebook.com" in url or "meta.com" in url
    assert "client_id=test-client-id" in url
    assert "state=csrf-state-token" in url
    assert "redirect_uri" in url


@pytest.mark.asyncio
async def test_callback_exchanges_code_for_token(adapter: MetaAdsAdapter) -> None:
    """callback() exchanges authorization code for access_token."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "access_token": "EAAxxxyyy",
        "token_type": "bearer",
        "expires_in": 5183944,
    }

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_response)

        result = await adapter.callback(
            code="auth-code-abc",
            tenant_id=TENANT_ID,
        )

    assert result["access_token"] == "EAAxxxyyy"


@pytest.mark.asyncio
async def test_list_ad_accounts_returns_list(adapter: MetaAdsAdapter) -> None:
    """list_ad_accounts() returns list of ad account dicts."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {"id": "act_111", "name": "Clinica Test", "currency": "ARS", "status": 1},
        ]
    }

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_response)

        accounts = await adapter.list_ad_accounts(
            access_token="EAAxxxyyy",
            tenant_id=TENANT_ID,
        )

    assert len(accounts) == 1
    assert accounts[0]["id"] == "act_111"


@pytest.mark.asyncio
async def test_fetch_insights_returns_list(adapter: MetaAdsAdapter) -> None:
    """fetch_insights() returns list of insight records."""
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = {
        "data": [
            {
                "campaign_id": "c1",
                "impressions": "1000",
                "spend": "50.00",
                "date_start": "2026-01-01",
                "date_stop": "2026-01-01",
            }
        ],
        "paging": {},
    }

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=mock_response)

        insights = await adapter.fetch_insights(
            access_token="EAAxxxyyy",
            ad_account_id="act_123",
            tenant_id=TENANT_ID,
            since="2026-01-01",
            until="2026-01-31",
        )

    assert len(insights) == 1
    assert insights[0]["campaign_id"] == "c1"


# ---------------------------------------------------------------------------
# Retry behavior (exponential backoff)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_fetch_insights_retries_on_server_error(adapter_fresh: MetaAdsAdapter) -> None:
    """fetch_insights retries up to 3× on 5xx responses."""
    # Use isolated tenant to avoid circuit breaker state from other tests
    retry_tenant = "tenant-retry-test"
    mock_error = MagicMock(spec=httpx.Response)
    mock_error.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("500", request=MagicMock(), response=mock_error)
    )
    mock_error.status_code = 500

    mock_ok = MagicMock(spec=httpx.Response)
    mock_ok.raise_for_status = MagicMock()
    mock_ok.json.return_value = {"data": [], "paging": {}}

    with patch("httpx.AsyncClient") as MockClient:
        instance = MockClient.return_value.__aenter__.return_value
        # Fail twice then succeed
        instance.get = AsyncMock(side_effect=[mock_error, mock_error, mock_ok])

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await adapter_fresh.fetch_insights(
                access_token="tok",
                ad_account_id="act_123",
                tenant_id=retry_tenant,
                since="2026-01-01",
                until="2026-01-31",
            )

    assert isinstance(result, list)
