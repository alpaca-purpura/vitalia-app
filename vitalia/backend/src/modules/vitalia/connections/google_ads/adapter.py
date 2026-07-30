# cap: connections.oauth-meta-google-ads
# story-origin: TBD
"""GoogleAdsAdapter — OAuth + Campaign Metrics integration for Google Ads API v13.

Resilience:
- Timeout: 30 s (configurable via GOOGLE_ADS_TIMEOUT_SECONDS env var)
- Retry: 3× exponential backoff (1 s, 2 s, 4 s) on 5xx responses
- Circuit breaker: per (tenant_id, provider) key; threshold=5 failures → 1 h cool-down

Queries use GAQL (Google Ads Query Language) via REST API v13.

HIPAA-lite: OAuth tokens (access_token + refresh_token) MUST be stored via
ChannelSyncStateRepository.save_with_encrypted_token() (pgcrypto).
Never log raw token values.

Per `.claude/rules/hipaa-lite.md` and `.claude/rules/tenant-isolation.md`.
"""

from __future__ import annotations

# downstream-regression-na: brand-local vitalia connections adapter — EP-8 registration only
import asyncio
import os
import time
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_OAUTH_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
_GOOGLE_ADS_API_BASE = "https://googleads.googleapis.com/v13"
_LIST_CUSTOMERS_URL = "https://googleads.googleapis.com/v13/customers:listAccessibleCustomers"

_DEFAULT_TIMEOUT_SECONDS: float = float(os.getenv("GOOGLE_ADS_TIMEOUT_SECONDS", "30"))
_MAX_RETRIES: int = 3
_CIRCUIT_BREAKER_THRESHOLD: int = 5
_CIRCUIT_BREAKER_COOLDOWN_SECONDS: float = 3600.0  # 1 hour

# Google Ads required scope
_OAUTH_SCOPES = "https://www.googleapis.com/auth/adwords"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class CircuitBreakerOpenError(Exception):
    """Raised when the circuit breaker is open for a tenant.

    Indicates that the tenant's Google Ads integration has exceeded the
    consecutive failure threshold and is cooling down.
    Error message is in Spanish neutro LatAm (user-facing context).
    """

    def __init__(self, tenant_id: str, opens_until: float) -> None:
        """Initialize with tenant context and cooldown expiry timestamp."""
        remaining = max(0, opens_until - time.monotonic())
        minutes = int(remaining // 60)
        super().__init__(
            f"El circuito de Google Ads está abierto para el tenant '{tenant_id}'. "
            f"Reintenta en aproximadamente {minutes} minutos."
        )
        self.tenant_id = tenant_id
        self.opens_until = opens_until


# ---------------------------------------------------------------------------
# Circuit breaker state (in-memory, per process)
# ---------------------------------------------------------------------------


class _BreakerState:
    """Internal state for a circuit breaker instance."""

    __slots__ = ("failure_count", "open_until")

    def __init__(self) -> None:
        """Initialize with zero failures."""
        self.failure_count: int = 0
        self.open_until: float = 0.0


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
            "google_ads.circuit_breaker_opened",
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
    """Execute coro_factory() with exponential backoff retry on 5xx errors."""
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
                    "google_ads.retry",
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
    if last_exc:
        _record_failure(tenant_id, provider_slug)
        raise last_exc
    raise RuntimeError("Unexpected retry exhaustion")  # pragma: no cover


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class GoogleAdsAdapter:
    """Google Ads OAuth + Campaign Metrics adapter using REST API v13 + GAQL.

    Usage:
        adapter = GoogleAdsAdapter(
            client_id=os.environ["GOOGLE_ADS_CLIENT_ID"],
            client_secret=os.environ["GOOGLE_ADS_CLIENT_SECRET"],
            redirect_uri=os.environ["GOOGLE_ADS_REDIRECT_URI"],
            developer_token=os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        )
        url = adapter.authorize_url(tenant_id=tenant_id, state=csrf_token)
        tokens = await adapter.callback(code=code, tenant_id=tenant_id)
        # Store tokens via ChannelSyncStateRepository.save_with_encrypted_token()

    HIPAA-lite: never log access_token or refresh_token values.
    """

    _PROVIDER_SLUG = "google_ads"

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        developer_token: str,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize adapter with OAuth credentials and developer token."""
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri
        self._developer_token = developer_token
        self._timeout = timeout_seconds

    def _auth_headers(self, access_token: str) -> dict[str, str]:
        """Build authorization headers required by Google Ads API."""
        return {
            "Authorization": f"Bearer {access_token}",
            "developer-token": self._developer_token,
        }

    # ------------------------------------------------------------------
    # OAuth
    # ------------------------------------------------------------------

    def authorize_url(self, *, tenant_id: str, state: str) -> str:
        """Build Google OAuth 2.0 authorization URL.

        Args:
            tenant_id: Vitalia tenant identifier.
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
            "access_type": "offline",
            "prompt": "consent",
        }
        url = f"{_OAUTH_AUTH_URL}?{urlencode(params)}"
        logger.info("google_ads.authorize_url_generated", tenant_id=tenant_id)
        return url

    async def callback(self, *, code: str, tenant_id: str) -> dict[str, Any]:
        """Exchange authorization code for access + refresh tokens.

        Args:
            code: Authorization code from Google OAuth callback.
            tenant_id: Vitalia tenant identifier.

        Returns:
            Token response dict with 'access_token', 'refresh_token', 'expires_in'.

        Note:
            Caller MUST store the returned tokens via
            ChannelSyncStateRepository.save_with_encrypted_token() (pgcrypto).
        """
        _check_circuit(tenant_id, self._PROVIDER_SLUG)

        payload = {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "redirect_uri": self._redirect_uri,
            "code": code,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await _with_retry(
                lambda: client.post(_OAUTH_TOKEN_URL, data=payload),
                tenant_id=tenant_id,
                provider_slug=self._PROVIDER_SLUG,
            )

        data: dict[str, Any] = response.json()
        logger.info("google_ads.token_exchange_success", tenant_id=tenant_id)
        return data

    # ------------------------------------------------------------------
    # Customer accounts
    # ------------------------------------------------------------------

    async def list_accessible_customers(self, *, access_token: str, tenant_id: str) -> list[str]:
        """List Google Ads customer resource names accessible to the user.

        Args:
            access_token: Valid Google access token (decrypted by caller).
            tenant_id: Vitalia tenant identifier.

        Returns:
            List of customer resource names (e.g., ['customers/123456789']).
        """
        _check_circuit(tenant_id, self._PROVIDER_SLUG)

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await _with_retry(
                lambda: client.get(
                    _LIST_CUSTOMERS_URL,
                    headers=self._auth_headers(access_token),
                ),
                tenant_id=tenant_id,
                provider_slug=self._PROVIDER_SLUG,
            )

        data: dict[str, Any] = response.json()
        resource_names: list[str] = data.get("resourceNames", [])
        logger.info(
            "google_ads.customers_listed",
            tenant_id=tenant_id,
            count=len(resource_names),
        )
        return resource_names

    # ------------------------------------------------------------------
    # Campaign metrics via GAQL
    # ------------------------------------------------------------------

    async def fetch_campaign_metrics(
        self,
        *,
        access_token: str,
        customer_id: str,
        tenant_id: str,
        since: str,
        until: str,
        login_customer_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Fetch campaign-level metrics via GAQL (Google Ads Query Language).

        Uses Google Ads API v13 REST endpoint with a GAQL SELECT query to
        retrieve impressions, clicks, cost, and conversions for the given date range.

        Args:
            access_token: Valid Google access token (decrypted by caller).
            customer_id: Google Ads customer ID without dashes (e.g., '123456789').
            tenant_id: Vitalia tenant identifier (circuit breaker key).
            since: Start date ISO 8601 (e.g. '2026-01-01').
            until: End date ISO 8601 (e.g. '2026-01-31').
            login_customer_id: Manager account ID for MCC hierarchies (optional).

        Returns:
            List of result rows from the GAQL query.

        Raises:
            CircuitBreakerOpenError: If circuit is open for this tenant.
            httpx.TimeoutException: If request exceeds timeout.
            httpx.ConnectError: If connection fails.
            httpx.HTTPStatusError: If API returns non-2xx after retries exhausted.
        """
        _check_circuit(tenant_id, self._PROVIDER_SLUG)

        gaql_query = (
            "SELECT "
            "campaign.id, campaign.name, campaign.status, "
            "metrics.impressions, metrics.clicks, metrics.cost_micros, "
            "metrics.conversions, metrics.ctr, "
            "segments.date "
            "FROM campaign "
            f"WHERE segments.date BETWEEN '{since}' AND '{until}' "
            "ORDER BY segments.date DESC"
        )

        url = f"{_GOOGLE_ADS_API_BASE}/customers/{customer_id}/googleAds:search"
        headers = self._auth_headers(access_token)
        if login_customer_id:
            headers["login-customer-id"] = login_customer_id

        body = {"query": gaql_query}

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await _with_retry(
                lambda: client.post(url, headers=headers, json=body),
                tenant_id=tenant_id,
                provider_slug=self._PROVIDER_SLUG,
            )

        data: dict[str, Any] = response.json()
        rows: list[dict[str, Any]] = data.get("results", [])
        logger.info(
            "google_ads.campaign_metrics_fetched",
            tenant_id=tenant_id,
            customer_id=customer_id,
            rows=len(rows),
        )
        return rows
