# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""MetaAdsAdapter — OAuth + Insights integration for Meta Ads (Facebook).

Resilience:
- Timeout: 30 s (configurable via META_ADS_TIMEOUT_SECONDS env var)
- Retry: 3× exponential backoff (1 s, 2 s, 4 s) on 5xx responses
- Circuit breaker: per (tenant_id, provider) key; threshold=5 failures → 1 h cool-down

HIPAA-lite: OAuth tokens MUST be stored via ChannelSyncStateRepository.save_with_encrypted_token()
(pgcrypto); never log or return raw tokens in observability traces.

Per `.claude/rules/hipaa-lite.md` and `.claude/rules/tenant-isolation.md`.
"""

from __future__ import annotations

# downstream-regression-na: brand-local vitalia connections adapter — EP-8 registration only
import asyncio
import os
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_GRAPH_API_BASE = "https://graph.facebook.com/v19.0"
_OAUTH_DIALOG_URL = "https://www.facebook.com/dialog/oauth"
_TOKEN_URL = "https://graph.facebook.com/oauth/access_token"

_DEFAULT_TIMEOUT_SECONDS: float = float(os.getenv("META_ADS_TIMEOUT_SECONDS", "30"))
_MAX_RETRIES: int = 3
_CIRCUIT_BREAKER_THRESHOLD: int = 5
_CIRCUIT_BREAKER_COOLDOWN_SECONDS: float = 3600.0  # 1 hour

_OAUTH_SCOPES = "ads_read,ads_management,business_management"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open for a tenant.

    Indicates that the tenant's Meta Ads integration has exceeded the
    consecutive failure threshold and is cooling down.
    Error message is in Spanish neutro LatAm (user-facing context).
    """

    def __init__(self, tenant_id: str, opens_until: float) -> None:
        """Initialize with tenant context and cooldown expiry timestamp."""
        remaining = max(0, opens_until - time.monotonic())
        minutes = int(remaining // 60)
        super().__init__(
            f"El circuito de Meta Ads está abierto para el tenant '{tenant_id}'. "
            f"Reintenta en aproximadamente {minutes} minutos."
        )
        self.tenant_id = tenant_id
        self.opens_until = opens_until


# ---------------------------------------------------------------------------
# Circuit breaker state (in-memory, per process)
# ---------------------------------------------------------------------------


@dataclass
class _BreakerState:
    """Internal state for a circuit breaker instance."""

    failure_count: int = 0
    open_until: float = 0.0  # monotonic clock timestamp when circuit closes again


# Shared in-memory state: keyed by (tenant_id, provider_slug)
_breaker_registry: dict[tuple[str, str], _BreakerState] = {}


def _get_breaker(tenant_id: str, provider_slug: str) -> _BreakerState:
    """Get or create circuit breaker state for (tenant_id, provider_slug)."""
    key = (tenant_id, provider_slug)
    if key not in _breaker_registry:
        _breaker_registry[key] = _BreakerState()
    return _breaker_registry[key]


def _check_circuit(tenant_id: str, provider_slug: str) -> None:
    """Raise CircuitBreakerOpenError if circuit is open."""
    state = _get_breaker(tenant_id, provider_slug)
    if state.open_until > 0 and time.monotonic() < state.open_until:
        raise CircuitBreakerOpenError(tenant_id, state.open_until)
    # Reset if cooldown expired
    if state.open_until > 0 and time.monotonic() >= state.open_until:
        state.failure_count = 0
        state.open_until = 0.0


def _record_failure(tenant_id: str, provider_slug: str) -> None:
    """Record a failure; open circuit if threshold reached."""
    state = _get_breaker(tenant_id, provider_slug)
    state.failure_count += 1
    if state.failure_count >= _CIRCUIT_BREAKER_THRESHOLD:
        state.open_until = time.monotonic() + _CIRCUIT_BREAKER_COOLDOWN_SECONDS
        logger.warning(
            "meta_ads.circuit_breaker_opened",
            tenant_id=tenant_id,
            failure_count=state.failure_count,
            cooldown_seconds=_CIRCUIT_BREAKER_COOLDOWN_SECONDS,
        )


def _record_success(tenant_id: str, provider_slug: str) -> None:
    """Reset failure counter on success."""
    state = _get_breaker(tenant_id, provider_slug)
    state.failure_count = 0
    state.open_until = 0.0


# ---------------------------------------------------------------------------
# Retry helper
# ---------------------------------------------------------------------------


async def _with_retry(
    coro_factory: Any,
    tenant_id: str,
    provider_slug: str,
    max_retries: int = _MAX_RETRIES,
) -> httpx.Response:
    """Execute coro_factory() with exponential backoff retry on 5xx errors.

    On repeated failure, records failure in circuit breaker.
    On success, resets failure counter.
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            response: httpx.Response = await coro_factory()
            response.raise_for_status()
            _record_success(tenant_id, provider_slug)
            return response
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code >= 500 and attempt < max_retries:
                wait = 2**attempt  # 1s, 2s, 4s
                logger.warning(
                    "meta_ads.retry",
                    attempt=attempt + 1,
                    wait_seconds=wait,
                    tenant_id=tenant_id,
                    status_code=exc.response.status_code,
                )
                await asyncio.sleep(wait)
                last_exc = exc
                continue
            _record_failure(tenant_id, provider_slug)
            raise
        except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError):
            _record_failure(tenant_id, provider_slug)
            raise
    # Should not reach here
    if last_exc:
        _record_failure(tenant_id, provider_slug)
        raise last_exc
    raise RuntimeError("Unexpected retry exhaustion")  # pragma: no cover


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class MetaAdsAdapter:
    """Meta Ads OAuth + Insights API adapter.

    Usage:
        adapter = MetaAdsAdapter(
            client_id=os.environ["META_OAUTH_CLIENT_ID"],
            client_secret=os.environ["META_OAUTH_CLIENT_SECRET"],
            redirect_uri=os.environ["META_OAUTH_REDIRECT_URI"],
        )
        url = adapter.authorize_url(tenant_id=tenant_id, state=csrf_token)
        # ... redirect user to url ...
        tokens = await adapter.callback(code=code, tenant_id=tenant_id)
        # Store tokens via ChannelSyncStateRepository.save_with_encrypted_token()

    HIPAA-lite: never log access_token values. Use structlog with tenant_id only.
    """

    _PROVIDER_SLUG = "meta_ads"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize adapter with OAuth credentials."""
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._timeout = timeout_seconds

    # ------------------------------------------------------------------
    # OAuth
    # ------------------------------------------------------------------

    def authorize_url(self, *, tenant_id: str, state: str) -> str:
        """Build Meta OAuth authorization URL.

        Args:
            tenant_id: Vitalia tenant identifier (for logging/circuit breaker key).
            state: CSRF token to verify on callback.

        Returns:
            Full authorization URL to redirect the user to.
        """
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": _OAUTH_SCOPES,
            "response_type": "code",
            "state": state,
        }
        url = f"{_OAUTH_DIALOG_URL}?{urlencode(params)}"
        logger.info("meta_ads.authorize_url_generated", tenant_id=tenant_id)
        return url

    async def callback(self, *, code: str, tenant_id: str) -> dict[str, Any]:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from Meta OAuth callback.
            tenant_id: Vitalia tenant identifier.

        Returns:
            Token response dict with 'access_token', 'token_type', 'expires_in'.

        Note:
            Caller MUST store the returned access_token via
            ChannelSyncStateRepository.save_with_encrypted_token() (pgcrypto).
            Never log the token value.
        """
        _check_circuit(tenant_id, self._PROVIDER_SLUG)

        params = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": self._redirect_uri,
            "code": code,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await _with_retry(
                lambda: client.get(_TOKEN_URL, params=params),
                tenant_id=tenant_id,
                provider_slug=self._PROVIDER_SLUG,
            )

        data: dict[str, Any] = response.json()
        logger.info("meta_ads.token_exchange_success", tenant_id=tenant_id)
        return data

    # ------------------------------------------------------------------
    # Ad Accounts
    # ------------------------------------------------------------------

    async def list_ad_accounts(self, *, access_token: str, tenant_id: str) -> list[dict[str, Any]]:
        """List ad accounts accessible to the authenticated user.

        Args:
            access_token: Valid Meta long-lived access token (decrypted by caller).
            tenant_id: Vitalia tenant identifier.

        Returns:
            List of ad account dicts with id, name, currency, status.
        """
        _check_circuit(tenant_id, self._PROVIDER_SLUG)

        url = f"{_GRAPH_API_BASE}/me/adaccounts"
        params = {
            "access_token": access_token,
            "fields": "id,name,currency,account_status",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await _with_retry(
                lambda: client.get(url, params=params),
                tenant_id=tenant_id,
                provider_slug=self._PROVIDER_SLUG,
            )

        data: dict[str, Any] = response.json()
        accounts: list[dict[str, Any]] = data.get("data", [])
        logger.info(
            "meta_ads.ad_accounts_listed",
            tenant_id=tenant_id,
            count=len(accounts),
        )
        return accounts

    # ------------------------------------------------------------------
    # Insights
    # ------------------------------------------------------------------

    async def fetch_insights(
        self,
        *,
        access_token: str,
        ad_account_id: str,
        tenant_id: str,
        since: str,
        until: str,
        level: str = "campaign",
        fields: str = "campaign_id,impressions,clicks,spend,cpc,cpm,ctr,reach,frequency",
    ) -> list[dict[str, Any]]:
        """Fetch ad performance insights for a given date range.

        Args:
            access_token: Valid Meta access token (caller decrypts via pgcrypto).
            ad_account_id: Ad account ID in format 'act_XXXXXXXXX'.
            tenant_id: Vitalia tenant identifier (circuit breaker key).
            since: Start date ISO 8601 (e.g. '2026-01-01').
            until: End date ISO 8601 (e.g. '2026-01-31').
            level: Aggregation level ('campaign', 'adset', 'ad').
            fields: Comma-separated insight fields to retrieve.

        Returns:
            List of insight records (dicts).

        Raises:
            CircuitBreakerOpenError: If circuit is open for this tenant.
            httpx.TimeoutException: If request exceeds timeout.
            httpx.ConnectError: If connection fails.
            httpx.HTTPStatusError: If API returns non-2xx after retries exhausted.
        """
        _check_circuit(tenant_id, self._PROVIDER_SLUG)

        url = f"{_GRAPH_API_BASE}/{ad_account_id}/insights"
        params = {
            "access_token": access_token,
            "fields": fields,
            "level": level,
            "time_range": f'{{"since":"{since}","until":"{until}"}}',
            "time_increment": 1,
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await _with_retry(
                lambda: client.get(url, params=params),
                tenant_id=tenant_id,
                provider_slug=self._PROVIDER_SLUG,
            )

        data: dict[str, Any] = response.json()
        rows: list[dict[str, Any]] = data.get("data", [])
        logger.info(
            "meta_ads.insights_fetched",
            tenant_id=tenant_id,
            ad_account_id=ad_account_id,
            rows=len(rows),
        )
        return rows
