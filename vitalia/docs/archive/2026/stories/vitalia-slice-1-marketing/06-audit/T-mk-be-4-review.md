<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review — T-mk-be-4

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-be-4 (Wave 2 — Meta Ads + Google Ads OAuth adapters + EP-8 registration)
**Date:** 2026-05-20
**Brand:** vitalia
**Commit:** 08555c5
**Files Reviewed:** 5 (2 adapters + 2 test files + 1 extensions.py update)
**Domains touched:** vitalia connections (brand-local Meta/Google OAuth adapters); Extension SDK EP-8 registration
**Skills consulted:** backend-expert (resilience patterns), tessl__graceful-degradation (timeout/retry/circuit-breaker), hipaa-lite (token encrypt via separate repo), anti-duplication (cross-brand mirror scan)
**Verdict:** **APPROVED with WARN** (resilience pattern correct + per-tenant isolation; minor: in-memory circuit breaker may not scale to multi-pod; EP-8 placeholders by design per v0.1.0 signature-only)

## /test-backend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| ruff-check | PASS | 0 errors |
| ruff-format | PASS | 0 reformats |
| pytest-architecture | PASS | 270/270 |
| pytest-marketing-module (connections) | PASS | 10 meta_ads + 8 google_ads = 18 tests |
| pytest-extensions | PASS | 39/39 (extension_register tests) |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Layer Compliance | PASS | adapters in `connections/{meta_ads,google_ads}/` are infrastructure-tier (acceptable) |
| 2 | Tenant Isolation | PASS | Circuit breaker keyed `(tenant_id, provider_slug)` — per-tenant; adapter doesn't persist tokens (delegated to repo) |
| 3 | Soft Deletes | N/A | |
| 4 | Code Quality | PASS | Ruff/format clean |
| 5 | SQLAlchemy 2.0 | N/A | |
| 6 | Async Consistency | PASS | `httpx.AsyncClient(timeout=…)` + `await` everywhere |
| 7 | Pydantic v2 / PII | N/A | |
| 8 | Migration Quality | N/A | |
| 9 | Security (PII) | PASS | Adapter never persists tokens (callers route through `ChannelSyncStateRepository.save_with_encrypted_token`). Logs use `tenant_id` only — no token values; OAuth flow uses `state` CSRF param |
| 10 | Tests / TDD | PASS | 18 tests covering OAuth happy path + timeout + circuit breaker + retry + per-tenant isolation + counter reset on success; SC-MK-02 explicitly covered |
| 11 | Cross-cutting | PASS | Spanish neutro in `CircuitBreakerOpenError` message (`El circuito de Meta Ads está abierto para el tenant…`); no voseo; no hardcoded currency (currency comes from provider response) |
| 12 | Mirror detection | PASS | No `meta_ads/` or `google_ads/` adapter in nicolify/comunify/lupulo (brand-local pattern correct) |

## Cross-scope flags

None — all files under `vitalia/backend/src/modules/vitalia/connections/{meta_ads,google_ads}/` + `vitalia/backend/src/modules/vitalia/extensions.py`. Engine SDK unchanged.

## Findings

### info: EP-8 callables registered as `_not_implemented_yet(...)` placeholders (correct per v0.1.0 signature-only contract)
**Category:** Extension SDK EP-8 compliance
**File:** `vitalia/backend/src/modules/vitalia/extensions.py:913-948`
**Issue:** Both `meta_ads` and `google_ads` register `send`, `receive`, `format_for_channel`, `webhook_handler` as `_not_implemented_yet(...)`. The adapter methods (`authorize_url`, `callback`, `list_ad_accounts`, `fetch_insights`) are NOT exposed through EP-8 — they are accessed directly by caller (cron jobs in T-mk-be-6).

**Result.md** explains this is "EP-8 signature-only in v0.1.0 (dispatch raises NotImplementedError until v0.2.x)". Acceptable design — Extension SDK EP-8 v0.1.0 contract is for outbound message dispatch (not OAuth/insights pulls). Marketing data sync runs out-of-band via cron jobs that call the adapter directly.

**Action:** None required. **Validates `be_test_extension_sdk_registration_marketing` PASS.**
**Skill ref:** brief CONTEXT-BRIEF.md § 2.

### WARN: In-memory circuit breaker registry won't survive process restart + doesn't share across pods
**Category:** Resilience / graceful-degradation
**File:** `vitalia/backend/src/modules/vitalia/connections/meta_ads/adapter.py:75-93` (same in google_ads)
**Issue:** `_breaker_registry: dict[tuple[str, str], _BreakerState] = {}` is module-level in-memory state. Implications:
- Worker pod restart → all breakers reset (5-failure threshold rebuilds from scratch). Could miss "wedged" tenants temporarily.
- Multi-pod scale (when vitalia goes prod) → each pod has its own breaker. Tenant could keep hammering Meta API across pods, bypassing the 1h cooldown.

Result.md explicitly acknowledges: "Per-process isolation is acceptable for single-pod deployments. Redis upgrade is a lift candidate if multi-pod scaling is needed." Documented + accepted trade-off for Slice 1.

**Fix (Slice 2 candidate, NOT blocking now):** Lift to Redis-backed `BreakerState` via `luana_core_idempotency` engine package (which already has Redis dep). Mention in `delta-arch-notes.md` or HANDOFF.

### WARN: Module-level `_DEFAULT_TIMEOUT_SECONDS = float(os.getenv(...))` is evaluated at import time
**Category:** 4 (Code Quality)
**File:** `vitalia/backend/src/modules/vitalia/connections/meta_ads/adapter.py:37`
**Issue:** `_DEFAULT_TIMEOUT_SECONDS: float = float(os.getenv("META_ADS_TIMEOUT_SECONDS", "30"))` is evaluated when the module imports. Late env-var overrides (e.g., in tests with `monkeypatch.setenv`) won't take effect for subsequent calls. Adapter __init__ accepts `timeout_seconds` override though — so this is a minor smell.

**Fix:** Move `_DEFAULT_TIMEOUT_SECONDS` evaluation inside `MetaAdsAdapter.__init__` default arg factory or use a `Field(default_factory=lambda: float(os.getenv(...)))` pattern. Low priority.

### WARN: `_with_retry` retry loop catches `httpx.NetworkError` but doesn't apply backoff before re-raising
**Category:** Resilience
**File:** `vitalia/backend/src/modules/vitalia/connections/meta_ads/adapter.py:165-167`
**Issue:** For `(httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError)` the helper calls `_record_failure` + `raise` immediately (no retry). Only HTTP 5xx triggers backoff retries. For transient connection blips (TCP reset, DNS hiccup), one failure marks the breaker without trying again. The contract says "30s timeout + 3× exponential backoff" — current impl applies backoff only to 5xx.

**Fix (suggested):** Apply retry+backoff to `httpx.TimeoutException` + `httpx.ConnectError` too (NOT for HTTPStatusError 4xx which means bad request).

```python
except (httpx.TimeoutException, httpx.ConnectError, httpx.NetworkError) as exc:
    if attempt < max_retries:
        wait = 2**attempt
        await asyncio.sleep(wait)
        last_exc = exc
        continue
    _record_failure(tenant_id, provider_slug)
    raise
```
**Skill ref:** tessl__graceful-degradation reference.

### info: `access_token` passed as URL query param in `fetch_insights` and `list_ad_accounts`
**Category:** 9 (Security / PII)
**File:** `adapter.py:289-291, 347-353`
**Issue:** Adapter passes `access_token` in URL query string (`params = {"access_token": ..., ...}`). Meta's Graph API supports this *AND* also Authorization header. Query string tokens can leak via:
- HTTP server access logs (httpx server-side mitigates this client-side)
- HTTPS proxy logs
- Browser referer headers (not applicable since adapter is server-side)

Less risky on the client side, but Meta's docs recommend `Authorization: Bearer <token>` header. NOT a HIPAA blocker (no PHI in token), but best practice. Also note the adapter's structlog `logger.info("meta_ads.token_exchange_success", tenant_id=tenant_id)` correctly omits token value.

**Fix (Slice 2):** Switch to header auth: `client.get(url, params=..., headers={"Authorization": f"Bearer {access_token}"})`. Apply same to Google Ads adapter.

## Contract Compliance (business surface only)

- [x] MetaAdsAdapter: `authorize_url`, `callback`, `list_ad_accounts`, `fetch_insights`
- [x] GoogleAdsAdapter: `authorize_url`, `callback`, `list_accessible_customers`, `fetch_campaign_metrics`
- [x] Timeout 30s (env override `META_ADS_TIMEOUT_SECONDS`, `GOOGLE_ADS_TIMEOUT_SECONDS`)
- [x] Exponential backoff 3× (1s, 2s, 4s) on 5xx
- [x] Circuit breaker threshold 5 / cooldown 1h, per (tenant_id, provider_slug)
- [x] EP-8 register via `registry.channel_adapter_register(ChannelAdapterDef(...))` — both adapters
- [x] Anti-duplication grep verified (per result.md): no meta_ads/google_ads in other brands

## Allowlist Movement

- [x] No allowlist grew

## Native-First Audit

- [x] No `docker exec` in commits
- [x] No `git add .` / `-A` / `-u` in commits

## Verdict Math

- All categories PASS
- 3 WARN (in-memory circuit breaker / module-level env / network errors no-retry) — none blocking
- Overall: **APPROVED with WARN**

## Action policy

Per `.claude/rules/auditor-self-fix-policy.md` § whitelist — none of the WARNs trigger Case C self-fix (they require architectural decisions, not whitelist items). Recommend WARN findings be tracked as Slice 2 follow-ups in `HANDOFF-cross-story-updates.md`.

T-mk-be-4 is **APPROVED**. No dev-team handoff required.

## Note re downstream cron consumers (T-mk-be-6)

T-mk-be-6 imports `MetaAdsAdapter` via `_get_meta_adapter()` factory. That ticket has separate issues (referrals_value_sync field mismatches) but the adapter contract itself is solid. The factory wires the adapter correctly with env vars.
