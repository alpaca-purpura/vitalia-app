# T-mk-be-4 result — Meta Ads + Google Ads OAuth adapters + EP-8 registration

**Ticket:** T-mk-be-4
**Story:** vitalia-slice-1-marketing
**Brand:** vitalia
**Wave:** 2 (parallel with T-mk-be-3)
**SHA:** 08555c5
**Branch:** wip/vitalia
**Date:** 2026-05-20

---

## Summary

Implemented brand-local Meta Ads and Google Ads OAuth + Insights adapters, registered
both via Extension SDK EP-8. All adapters wrapped with timeout 30 s, exponential backoff
retry 3x, and in-memory circuit breaker per (tenant_id, provider) key (threshold=5,
cooldown=1 h). HIPAA-lite: OAuth tokens never persisted by adapters — callers route
through `ChannelSyncStateRepository.save_with_encrypted_token()` (pgcrypto).

Anti-duplication grep verified: no meta_ads/google_ads mirrors in nicolify, comunify,
or lupulo (brand-local EP-8 extension pattern per anti-duplication.md).

---

## Files created

### Meta Ads adapter
- `vitalia/backend/src/modules/vitalia/connections/meta_ads/__init__.py`
- `vitalia/backend/src/modules/vitalia/connections/meta_ads/adapter.py`
  - `MetaAdsAdapter` class with methods: `authorize_url`, `callback`, `list_ad_accounts`, `fetch_insights`
  - `CircuitBreakerOpenError` exception (Spanish neutro LatAm error message)
  - Module-level `_breaker_registry: dict[tuple[str, str], _BreakerState]` for per-tenant isolation
  - `_with_retry()` helper: 3x exponential backoff (1s, 2s, 4s) on HTTPStatusError >= 500
  - ENV: `META_ADS_TIMEOUT_SECONDS` (default 30), `META_OAUTH_CLIENT_ID/SECRET/REDIRECT_URI`
  - Graph API base: `https://graph.facebook.com/v19.0`

### Google Ads adapter
- `vitalia/backend/src/modules/vitalia/connections/google_ads/__init__.py`
- `vitalia/backend/src/modules/vitalia/connections/google_ads/adapter.py`
  - `GoogleAdsAdapter` class with methods: `authorize_url`, `callback`, `list_accessible_customers`, `fetch_campaign_metrics`
  - `CircuitBreakerOpenError` exception (Spanish neutro LatAm error message)
  - Same circuit breaker pattern as MetaAdsAdapter (per-process `_breaker_registry`)
  - GAQL query for Google Ads API v13 REST endpoint (`/v13/customers/{id}/googleAds:search`)
  - Scope: `https://www.googleapis.com/auth/adwords`
  - ENV: `GOOGLE_ADS_TIMEOUT_SECONDS` (default 30), `GOOGLE_ADS_CLIENT_ID/SECRET/REDIRECT_URI/DEVELOPER_TOKEN`
  - Includes `login-customer-id` header support for MCC hierarchies

### Tests (TDD RED first, then GREEN)
- `vitalia/backend/tests/modules/vitalia/connections/meta_ads/__init__.py`
- `vitalia/backend/tests/modules/vitalia/connections/meta_ads/test_meta_ads_adapter.py`
  - 10 tests covering: timeout, circuit breaker (5 failures threshold, per-tenant isolation, success reset), OAuth flows, retry on 5xx
  - `autouse` fixture resets `_meta_module._breaker_registry` between tests
- `vitalia/backend/tests/modules/vitalia/connections/google_ads/__init__.py`
- `vitalia/backend/tests/modules/vitalia/connections/google_ads/test_google_ads_adapter.py`
  - 8 tests covering: OAuth URL shape (includes `scope` param + `access_type=offline`), token exchange with refresh_token, list_accessible_customers, GAQL fetch_campaign_metrics, timeout, circuit breaker, retry on 5xx
  - Same autouse reset fixture pattern

---

## Files modified

### extensions.py — EP-8 registrations added
- `vitalia/backend/src/modules/vitalia/extensions.py`
  - Added 2 `registry.channel_adapter_register(ChannelAdapterDef(...))` calls after the WhatsApp fidelización loop and before EP-9
  - `channel_slug=_ns("meta_ads")` → `"vitalia.meta_ads"` (CC-4 namespace)
  - `channel_slug=_ns("google_ads")` → `"vitalia.google_ads"` (CC-4 namespace)
  - All callables use `_not_implemented_yet(...)` per EP-8 signature-only contract (v0.1.0)
  - send/receive/format_for_channel/webhook_handler are placeholders until v0.2.x dispatch

---

## Gherkin coverage

### SC-MK-02 (Meta API timeout)
| Test | Status |
|---|---|
| `test_timeout_30s_raises` | PASS |
| `test_circuit_breaker_after_5_consecutive_failures` | PASS |

### Additional coverage
| Test | Scenario |
|---|---|
| `test_fetch_insights_timeout_uses_30s` | Timeout config verification |
| `test_circuit_breaker_isolated_per_tenant` | Cross-tenant isolation |
| `test_circuit_breaker_success_does_not_increment` | Counter reset on success |
| `test_authorize_url_returns_facebook_oauth_url` | OAuth URL shape |
| `test_callback_exchanges_code_for_token` | Token exchange |
| `test_list_ad_accounts_returns_list` | Account listing |
| `test_fetch_insights_returns_list` | Insights fetch |
| `test_fetch_insights_retries_on_server_error` | Retry on 5xx |
| Google Ads equivalents (8 tests) | Same patterns for Google Ads adapter |

---

## Key design decisions

### Circuit breaker implementation
In-memory module-level `_breaker_registry: dict[tuple[str, str], _BreakerState]` (not Redis)
to avoid external dependency while satisfying the 1-h cooldown contract. Per-process isolation
is acceptable for single-pod deployments. Redis upgrade is a lift candidate if multi-pod
scaling is needed.

### EP-8 registration pattern
Consistent with all existing EP-8 registrations in `extensions.py`:
- `registry.channel_adapter_register(ChannelAdapterDef(channel_slug=_ns("meta_ads"), ...))`
- All callables use `_not_implemented_yet(...)` placeholder pattern
- EP-8 is in `_BACKLOG_EPS` (signature-only, dispatch raises NotImplementedError)
  — this is correct: adapters are registered now, dispatch wiring lands in future ticket

### HIPAA-lite enforcement
- Adapters log only `tenant_id` + counts via structlog — never raw token values
- Comments in both adapters explicitly state: "Caller MUST store the returned access_token
  via ChannelSyncStateRepository.save_with_encrypted_token() (pgcrypto)"
- `CircuitBreakerOpenError` message is in Spanish neutro LatAm

### Test isolation
Used `autouse` pytest fixture that clears `_breaker_registry` before/after each test to
prevent shared module-level state from leaking between test cases.

---

## Gate results

| Gate | Result |
|---|---|
| `ruff check` | 0 errors |
| `ruff format --check` | 0 files to reformat |
| `pytest tests/modules/vitalia/connections/meta_ads/` | 10/10 PASS |
| `pytest tests/modules/vitalia/connections/google_ads/` | 8/8 PASS |
| `pytest tests/modules/vitalia/` | 770 passed, 17 skipped (Postgres-gated) |
| `pytest tests/test_extensions.py` | 39/39 PASS |
| `pytest tests/architecture/` | 270/270 PASS |

---

## Next ticket

T-mk-be-5 (FastAPI endpoints /api/v1/vitalia/marketing/*) is now unblocked —
it was blocked by T-mk-be-3 + T-mk-be-4, both now pushed.
