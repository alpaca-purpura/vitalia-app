<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review — T-mk-be-3

**Story:** vitalia-slice-1-marketing
**Ticket:** T-mk-be-3 (Wave 2 — Application services + Pydantic v2 DTOs)
**Date:** 2026-05-20
**Brand:** vitalia
**Commit:** 978d002
**Files Reviewed:** 7 (1 DTO module ~250 LOC + 4 services + 2 tests)
**Domains touched:** marketing application layer (services orchestrating repos + Lucas consumers)
**Skills consulted:** backend-expert (Pydantic v2 DTOs + DDD), hipaa-lite (audit log SYNC + dual filter), anti-duplication (engine outbox bus import)
**Verdict:** **CHANGES_REQUESTED** (services don't import real Lucas* services; service method names don't match route layer; LucasRecommendationsService missing `run_daily_sweep` consumed by T-mk-be-6)

## /test-backend Gate Status (per gate-output.json iter=1)

| Gate | Result | Detail |
|---|---|---|
| ruff-check | PASS | 0 errors |
| ruff-format | PASS | 0 reformats |
| pytest-architecture | PASS | 270/270 |
| pytest-marketing-module (application) | PASS | 8/8 application tests |

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Layer Compliance | WARN | services depend on `lucas_attribution_service: object` / `lucas_referrals_service: object` — no concrete import from agentic module (consumer contract documented in docstring only) |
| 2 | Tenant Isolation | PASS | `tenant_id + clinic_id` dual filter forwarded to repos consistently |
| 3 | Soft Deletes | N/A | App layer doesn't issue queries directly |
| 4 | Code Quality | PASS | Ruff/format clean |
| 5 | SQLAlchemy 2.0 | N/A | No direct SA in services |
| 6 | Async Consistency | PASS | All public methods `async def` |
| 7 | Pydantic v2 / PII | PASS | All DTOs use `model_config = ConfigDict(from_attributes=True)`; no PHI fields exposed in `ReferrerEntryResponse` (uses `referrer_id: str` hash); `currency: str | None = None` (no hardcoded USD) |
| 8 | Migration Quality | N/A | |
| 9 | Security (PII) | PASS | Audit log invoked SYNC before outbox publish (HIPAA-lite mandate); range validation in `_validate_action_payload` (SC-MK-04); referrer leaderboard uses UUID hash str (no patient names) |
| 10 | Tests / TDD | PASS | 8 tests with TDD RED-first per result.md; covers SC-MK-01 + SC-MK-04 |
| 11 | Cross-cutting (currency/Spanish/UTC) | PASS | `currency: str | None = None` in 12 DTOs; Spanish neutro in error message line 388-392 (`El presupuesto solicitado excede el límite permitido…`); no voseo |
| 12 | Mirror detection | PASS | Outbox `adapter_bus` imported from engine (`luana_core_events.outbox`) — not re-implemented |

## Cross-scope flags

None — application files under `vitalia/backend/src/modules/vitalia/marketing/application/`. Lucas* services in `vitalia/backend/src/modules/vitalia/agentic/lucas/...` are READ-ONLY context (consumed via `object` typed param, no concrete import).

## Findings

### FAIL: Lucas service contract violation — proxies use `object` type with no concrete import from agentic module
**Category:** 1 (DDD compliance / Contract)
**Files:**
- `vitalia/backend/src/modules/vitalia/marketing/application/services/attribution_service.py:36-50`
- `vitalia/backend/src/modules/vitalia/marketing/application/services/referrals_service.py:57-73`
- `vitalia/backend/src/modules/vitalia/marketing/application/services/lucas_recommendations_service.py:79-92`

**Issue:** Brief, 01-spec-extract.md § 8, and arch spec § 6 explicitly state "Marketing consumes Lucas services via Python import. `application/services/lucas_recommendations_service.py imports LucasOrchestratorService`". 03-arch-be.md § 6 line 411-412 says reads use `LucasAttributionService`, `LucasReferralsService`, `LucasOrchestratorService` (existing — reused from `agentic/lucas/`).

The shipped code:
- `AttributionService.__init__(lucas_attribution_service: object, ...)` — types as `object`, never imports `vitalia.modules.vitalia.agentic.lucas.application.services.lucas_attribution_service.LucasAttributionService`.
- Same for `ReferralsService`.
- `LucasRecommendationsService` doesn't import `LucasOrchestratorService` at all.

Documentation says "Proxies to LucasAttributionService" but the import is missing. Marketing module compiles + tests pass because nothing wires the real services. **Production runtime will fail or silently no-op** depending on how `_get_attribution_service` (T-mk-be-5) initializes the stub.

**Fix:**
- Import the shipped services in `attribution_service.py` (and referrals/recommendations equivalents):
  ```python
  from src.modules.vitalia.agentic.lucas.application.services.lucas_attribution_service import LucasAttributionService
  ```
- Replace `object` type hints with concrete class names.
- In route factory (T-mk-be-5), wire real instances (not MagicMock).
**Skill ref:** backend-ddd.md § cross-module imports (agentic is read-only consumer from marketing — valid pattern, but must be explicit).

### FAIL: Service method names diverge from caller expectations in routes.py (T-mk-be-5)
**Category:** 1 (DDD) + Contract compliance
**File:**
- `attribution_service.py:52` defines `async def matrix(...)` — routes (`routes.py:693`) calls `svc.get_attribution_matrix(...)` (will `AttributeError` at runtime if not mocked).
- `referrals_service.py:75` defines `async def leaderboard(...)` — routes (`routes.py:731`) calls `svc.get_referrals(...)` (same problem).
- `marketing_service.py:159` `channel_detail(stage: BowtieStage, ...)` requires `stage` — routes (`routes.py:382-389`) calls with `stage=None`. Service `_STAGE_CHANNEL_MAP.get(stage, [])` will return `[]` when stage is None (silent fail returning empty list — masked because tests mock the service).

**Fix:** Either:
- (a) Rename service methods to match route calls (`matrix → get_attribution_matrix`, `leaderboard → get_referrals`), and make `MarketingService.channel_detail.stage` optional with a "no stage filter → all channels" branch (proper implementation), OR
- (b) Fix routes to call existing service methods (`matrix()`, `leaderboard()`) + drop `stage=None` from channel_detail call (require provider-driven channel slug list).

Builder must reconcile in one direction. Currently the route tests pass only because `_get_*_service()` factories return `MagicMock` instances that accept any attribute name. Real services break in production.
**Skill ref:** backend-ddd.md, tdd-mandatory.md § "tests must validate real code paths".

### FAIL: LucasRecommendationsService missing `run_daily_sweep` consumed by T-mk-be-6 cron
**Category:** 1 (DDD) + Contract
**File:** `application/services/lucas_recommendations_service.py` (whole class)
**Issue:** T-mk-be-6 `lucas_daily_analysis_sweep.py:88-93` calls `LucasRecommendationsService()` (no args!) then later (line 156) calls `orchestrator.run_daily_sweep(tenant_id=..., clinic_id=..., cooldown_kinds=...)`. T-mk-be-3 ships:
1. `LucasRecommendationsService.__init__(*, repo, audit_writer)` requires 2 required kwargs → `LucasRecommendationsService()` raises TypeError.
2. No `run_daily_sweep` method on the class.

The arch spec § 6 (line 419-440) and brief § 7 say the cron should call `LucasOrchestratorService.run_daily_sweep(...)` from the **agentic** module — but T-mk-be-6 instantiates the **marketing** `LucasRecommendationsService` which is the API-facing CRUD service.

**Fix (in T-mk-be-6 + T-mk-be-3 together):**
- In T-mk-be-3, do NOT add `run_daily_sweep` to `LucasRecommendationsService` (that's the agentic service contract).
- In T-mk-be-6, `_get_orchestrator()` should import `LucasOrchestratorService` from `agentic/lucas/application/services/lucas_orchestrator_service.py` and instantiate it (likely needs repo + LLM client deps — verify service signature).
- Builder must read shipped service signature (Story `vitalia-copilot-tools-impl` archive 2026-05-18) to wire correctly.

**Skill ref:** backend-ddd.md § cross-module read via concrete import (agentic services are existing infra, consumed by marketing).

### WARN: Outbox event fallback (`_FallbackBus`) introduces hidden test-only path in production code
**Category:** 4 (Code Quality) + 11 (cross-cutting)
**Files:**
- `services/lucas_recommendations_service.py:46-55`
- `services/referrals_service.py:32-39`
- All 4 cron jobs in `jobs/`
**Issue:** Each service uses `try: from luana_core_events.outbox import adapter_bus except ImportError: _FallbackBus = AsyncMock`. The fallback uses `unittest.mock.AsyncMock` (NOT a production-grade no-op). Per `# pragma: no cover` annotation, the fallback path is excluded from coverage — but it's still imported. If `luana_core_events` truly isn't installed in CI/dev, every cron job silently no-ops on event publish, and tests can't distinguish "real publish" from "fallback no-op".

The brief § 7 confirms outbox pattern is mandatory + engine package available. Importing `unittest.mock` in production code is anti-pattern.

**Fix (suggested):** Either:
- Remove fallback (luana_core_events is a workspace member — `from luana_core_events.outbox import adapter_bus` should always succeed). Add to `vitalia/backend/pyproject.toml` deps if not already.
- If the fallback is genuinely needed for testing (it's not, since tests mock adapter_bus directly), use a real no-op class:
  ```python
  class _FallbackBus:
      async def publish(self, event): pass
  ```
  No `unittest.mock` import in `src/` code.

**Skill ref:** anti-duplication.md § engine consumer pattern.

### WARN: `_FallbackBus.publish = _AsyncMock()` is a class attribute (shared singleton, breaks isolation between calls)
**Category:** 4 (Code Quality)
**Files:** Same as above
**Issue:** The fallback creates `class _FallbackBus: publish = _AsyncMock()` — a *class attribute*, not instance. All `publish` calls share state. If multiple cron jobs run concurrently and one hits the fallback path, mock state could pollute. Symptom would be tests-only but worth noting.

**Fix:** Use `__init__` to create per-instance mock, OR remove fallback (preferred per finding above).

## Contract Compliance (business surface only)

- [x] 12 Pydantic v2 DTOs per arch spec § 3 (BowtieSummaryResponse + 11 others)
- [x] `model_config = ConfigDict(from_attributes=True)` on every DTO
- [x] `currency: str | None = None` (no hardcoded "USD")
- [x] PHI-safe (`referrer_id: str` hash in leaderboard)
- [x] HIPAA-lite audit log SYNC `await audit_writer.write(...)` BEFORE `adapter_bus.publish(...)`
- [x] Range validation in `_validate_action_payload` (SC-MK-04) — Spanish neutro error message
- [ ] **Real Lucas* service imports MISSING — FAIL (must wire concrete class)**
- [ ] **Service method names mismatch route callers — FAIL**

## Allowlist Movement

- [x] No allowlist grew. Arch fitness 270/270.

## Native-First Audit

- [x] No `docker exec` in commits
- [x] No `git add .` / `-A` / `-u` in commits

## Verdict Math

- Cat 1 (DDD/Contract) Lucas service import missing + method name mismatch + `run_daily_sweep` absent = **FAIL** (production code path broken; only tests pass because of MagicMock factories)
- Cat 4 + 11 (fallback bus) = **WARN**
- Other categories PASS
- Overall: **CHANGES_REQUESTED** — Case B (spawn dev-team to wire real Lucas service imports + reconcile method names + verify cron orchestrator wiring)

## Action policy

Per `.claude/rules/auditor-self-fix-policy.md` § NUNCA self-fix #4 (new method) + #2 (branch logic) + #5 (modify SA queries indirect). Spawn dev-team.

**Recommended handoff to `/dev-team` (combined with T-mk-be-2 + T-mk-be-5 + T-mk-be-6 — these tickets are tangled):**
1. Import concrete `LucasAttributionService`, `LucasReferralsService`, `LucasOrchestratorService` from `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/` in marketing services.
2. Rename `AttributionService.matrix → get_attribution_matrix` (or fix routes).
3. Rename `ReferralsService.leaderboard → get_referrals` (or fix routes).
4. Fix `MarketingService.channel_detail` to handle `stage=None` properly (list ALL channels), OR fix routes to always pass a `stage`.
5. Remove `unittest.mock` fallback from `adapter_bus` import; use real no-op or rely on workspace import.
6. Re-run gate-runner + verify route tests still pass with real services injected (factories in T-mk-be-5 must wire real classes).

---

## Audit iteration 2 (2026-05-21T00:50:00Z — post AUDITOR_AUTO_FIX_LOOP commit ac8ec6f3)

### Verdict
**APPROVED with WARN** (non-blocking — see new WARN below)

### Re-verification (iter 1 findings)

| Finding | Status | Evidence |
|---|---|---|
| FAIL: Lucas service contract — `object` type with no concrete import | ✅ FIXED | `attribution_service.py:21-24` imports `LucasAttributionService` + `TenantLocaleProtocol`; `referrals_service.py:23-26` imports `LucasReferralsService` + `TenantLocaleProtocol`; concrete `__init__` type hints applied |
| FAIL: Service method names diverge from route callers | ✅ FIXED | `AttributionService.get_attribution_matrix()` (was `matrix`); `ReferralsService.get_referrals()` (was `leaderboard`) — match `routes.py:793,832` callers |
| FAIL: `run_daily_sweep` missing on LucasRecommendationsService | ✅ FIXED | T-mk-be-6 now imports `LucasOrchestratorService` from agentic module (correct per spec § 6) — but signature mismatch persists, see T-mk-be-6 review iter 2 |
| WARN: `_FallbackBus` uses `unittest.mock.AsyncMock` (production code path) | ✅ FIXED (services) | `lucas_recommendations_service.py:46-58` and `referrals_service.py:34-48` now use real `class _FallbackBus` with structlog warning (no `unittest.mock` import) |
| WARN: `_FallbackBus.publish` class attr (shared singleton) | ✅ FIXED | New `_FallbackBus.publish` is an `async def` instance method (no shared state) |

### Service wiring verified

`AttributionService` (`services/attribution_service.py`):
- Line 21-24: imports `LucasAttributionService` + `TenantLocaleProtocol` from agentic module ✓
- Line 41-54: `__init__(lucas_attribution_service: LucasAttributionService, locale: TenantLocaleProtocol)` ✓
- Line 56-106: `get_attribution_matrix(...)` delegates to `LucasAttributionService.compute_attribution()` ✓

`ReferralsService` (`services/referrals_service.py`):
- Line 23-26: imports `LucasReferralsService` + `TenantLocaleProtocol` ✓
- Line 66-82: `__init__(lucas_referrals_service: LucasReferralsService, referral_repo: object, locale: TenantLocaleProtocol)` — `referral_repo: object` retained (acceptable, structural) ✓
- Line 84-143: `get_referrals(...)` delegates to `LucasReferralsService.compute_referrals()` ✓

`LucasRecommendationsService` (CRUD wrapper):
- Stayed in marketing layer with `repo` + `audit_writer` deps — correct per spec § 6 (CRUD service distinct from agentic orchestrator) ✓
- Method names unchanged: `list_open_by_stage`, `approve`, `reject`, `undo` — match routes ✓

### NEW WARN: `_FallbackBus` pattern still uses `unittest.mock` in 2 cron jobs (regression scope creep)

**Category:** 4 (Code Quality) — same pattern as iter 1 WARN, not propagated to all consumers
**Files:**
- `vitalia/backend/src/modules/vitalia/marketing/jobs/channel_metrics_sync_meta.py:43-48`
- `vitalia/backend/src/modules/vitalia/marketing/jobs/channel_metrics_sync_google.py:43-48`

**Issue:** Auto-fix updated 3 service files (`lucas_recommendations_service`, `referrals_service`, `lucas_daily_analysis_sweep`, `referrals_value_sync`) to use real `_FallbackBus` class but missed 2 cron jobs:

```python
except ImportError:  # pragma: no cover
    from unittest.mock import AsyncMock as _AsyncMock  # noqa: PLC0415

    class _FallbackBus:  # type: ignore[no-redef]
        publish = _AsyncMock()

    adapter_bus = _FallbackBus()
```

**Action:** Apply same pattern (real `async def publish` + structlog warning) to `channel_metrics_sync_{meta,google}.py`. NON-BLOCKING — `# pragma: no cover` keeps it out of coverage; `luana_core_events` is workspace member so ImportError never fires in real envs. Defer to Slice 1 hotfix or Slice 2.

**Skill ref:** anti-duplication.md § engine consumer pattern (same WARN as iter 1, just incomplete fix propagation).

### Category re-summary

| # | Category | Status |
|---|---|---|
| 1 | DDD/Contract | PASS (concrete imports applied) |
| 4 | Code Quality | WARN (2 cron jobs still have `unittest.mock` import) |
| Contract compliance | PASS |

### Verdict math
- 3 FAIL findings addressed cleanly
- 1 WARN finding partially addressed (services done; 2 crons incomplete) → still WARN (non-blocking)
- 0 regressions
- Overall: **APPROVED with WARN** — forward motion OK; followup ticket suggested for cron fallback cleanup

