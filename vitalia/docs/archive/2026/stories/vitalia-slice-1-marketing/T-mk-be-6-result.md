# T-mk-be-6 Result — Marketing Wave 3 ARQ Cron Jobs

**Ticket:** T-mk-be-6
**Story:** vitalia-slice-1-marketing
**SHA:** 8471b25
**Branch:** wip/vitalia
**Date:** 2026-05-20

## Summary

Implemented 4 ARQ cron jobs (Wave 3) per `03-arch-be.md § 8`. All decorated with engine `@cron_envelope` from `luana_core_platform.workers.cron_envelope`. All registered in `arq_settings.py` WorkerSettings (11 → 15 cron jobs).

## Files Created

### New cron job files

| File | Description |
|---|---|
| `vitalia/backend/src/modules/vitalia/marketing/jobs/__init__.py` | Package init |
| `vitalia/backend/src/modules/vitalia/marketing/jobs/channel_metrics_sync_meta.py` | Meta Ads sync every 4h |
| `vitalia/backend/src/modules/vitalia/marketing/jobs/channel_metrics_sync_google.py` | Google Ads sync every 4h (+2min offset) |
| `vitalia/backend/src/modules/vitalia/marketing/jobs/lucas_daily_analysis_sweep.py` | Lucas daily sweep 06:00 UTC |
| `vitalia/backend/src/modules/vitalia/marketing/jobs/referrals_value_sync.py` | Referrals value sync 10:00 UTC |
| `vitalia/backend/tests/workers/test_marketing_crons.py` | 13 tests for all 4 crons |

## Files Modified

| File | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/lucas_recommendation_repository.py` | Added `expire_stale_open()` + `list_recent_rejections_by_kind()` |
| `vitalia/backend/src/modules/vitalia/marketing/infrastructure/repositories/referral_repository.py` | Added `list_active_for_value_sync()` |
| `vitalia/backend/src/modules/vitalia/_shared/workers/arq_settings.py` | Expanded 11 → 15 cron jobs |
| `vitalia/backend/tests/workers/test_arq_settings.py` | Updated allowlists 11 → 15 |

## Cron Job Specs

### channel_metrics_sync_meta
- Decorator: `@cron_envelope("vitalia.cron.channel_metrics_sync_meta", ttl=14400)`
- Schedule: every 4h `{0,4,8,12,16,20}:00 UTC`
- Steps: decrypt token (pgcrypto) → `meta_adapter.fetch_insights()` → `metric_repo.upsert_metric()` per campaign → publish `ChannelSyncSucceeded` or `ChannelSyncFailed`
- HIPAA-lite: raw_payload excludes `access_token`, `token`, `oauth_token`; no PHI in metrics

### channel_metrics_sync_google
- Decorator: `@cron_envelope("vitalia.cron.channel_metrics_sync_google", ttl=14400)`
- Schedule: every 4h `{0,4,8,12,16,20}:02 UTC` (offset to avoid DB contention)
- Steps: same pattern as Meta; cost_micros → cents (`cost_micros // 10000`)
- Currency field from `customer.currency_code` (no hardcoded USD)

### lucas_daily_analysis_sweep
- Decorator: `@cron_envelope("vitalia.cron.lucas_daily_analysis_sweep", ttl=86400)`
- Schedule: daily 06:00 UTC
- Steps: `expire_stale_open()` → `list_recent_rejections_by_kind(since=now-30d)` → build `cooldown_kinds` set → `orchestrator.run_daily_sweep(cooldown_kinds=...)` → publish `LucasRecommendationGenerated` per new rec
- Gherkin SC-MK-02 covered: `test_lucas_daily_analysis_sweep_skips_rejected_30d_cooldown`

### referrals_value_sync
- Decorator: `@cron_envelope("vitalia.cron.referrals_value_sync", ttl=86400)`
- Schedule: daily 10:00 UTC
- Steps: per referral with status `signed_up|converted` → sum appointment values → if changed → update `conversion_value_cents` → if `signed_up` → transition to `converted` + publish `ReferralConverted`
- Uses inline `_AppointmentRepository` with raw SQL on `vitalia_appointments` (no separate model scope)

## Test Results

```
vitalia/backend/tests/workers/test_marketing_crons.py  13/13 PASS
vitalia/backend/tests/workers/test_arq_settings.py     10/10 PASS
vitalia/backend/tests/architecture/                   270/270 PASS
```

**Validator be_test_workers_marketing_crons:** 13/13 GREEN
**Validator be_arch_fitness_brand:** 270/270 GREEN

### Gherkin Coverage SC-MK-02

| Scenario | Test | Status |
|---|---|---|
| SC-MK-02: channel sync fails per tenant without aborting sweep | `test_channel_metrics_sync_meta_soft_fail_per_tenant` | PASS |
| SC-MK-02: ChannelSyncFailed event published on per-tenant error | `test_channel_metrics_sync_meta_publishes_channelsyncfailed_event` | PASS |
| SC-MK-02: Lucas skips recommendation kinds rejected in last 30d | `test_lucas_daily_analysis_sweep_skips_rejected_30d_cooldown` | PASS |

## Quality Gates

- Lint: `ruff check` — 0 errors
- Format: `ruff format --check` — 13 files already formatted
- Architecture fitness: 270 passed (arch tests run in isolation pass deterministically; pre-existing SQLAlchemy polluter from agentic eval tests causes seed-dependent failures when combined — not from T-mk-be-6)

## Notes

- The pre-existing `test_vitalia_no_query_without_tenant_filter.py` flaky behavior when combined with agentic eval tests is a SQLAlchemy model re-registration side-effect from `LucasStageRecommendationModel` (agentic module). Not introduced by T-mk-be-6.
- All 4 crons use injectable factory helpers (`_get_*_repo()`, `_get_*_adapter()`) patchable via `unittest.mock.patch()` without FastAPI DI container.
- Tests call `fn.__wrapped__(ctx)` to bypass the `cron_envelope` idempotency dedup layer.

---

## Auto-fix loop iter 2 — SHA b239e363 (2026-05-20)

Three regressions identified by auditor iteration 2 in `lucas_daily_analysis_sweep.py` fixed.

### F-iter2-1: LucasOrchestratorService() zero-args construction

**Root cause:** `_get_orchestrator()` called `LucasOrchestratorService()` with no args but constructor requires 4 keyword-only args.

**Fix:**
- Added `make_orchestrator()` factory in `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/__init__.py`.
- Factory wires no-op async handlers for stage/attribution/referrals + `MemorySaver` checkpointer.
- `_get_orchestrator()` now calls `make_orchestrator()`.

### F-iter2-2: run_daily_sweep() does not exist + locale missing

**Root cause:** Cron called `orchestrator.run_daily_sweep(tenant_id, clinic_id, cooldown_kinds)` — that method was never on `LucasOrchestratorService`. Real method is `run_daily_analysis(*, tenant_id, clinic_id, locale)` returning `AnalysisReport`.

**Fix:**
- Added `_FallbackLocale` dataclass (UTC/USD) implementing `TenantLocaleProtocol` for cron context.
- Replaced call with `orchestrator.run_daily_analysis(tenant_id=..., clinic_id=..., locale=locale)`.
- Cooldown filtering moved POST-call: `[r for r in report.final_state["stage_recommendations"] if r.get("recommendation_kind") not in cooldown_kinds]`.

### F-iter2-3: BowtieStage string passed to event that expects enum

**Root cause:** Code computed `BowtieStage(rec_stage_raw).value` (a string) and passed it as `stage=` to `LucasRecommendationGenerated`. That constructor calls `stage.value` internally → `AttributeError: 'str' object has no attribute 'value'`.

**Fix:**
- `isinstance` check on `rec_stage_raw` — if already `BowtieStage` use directly.
- Otherwise: `BowtieStage(rec_stage_raw)` (enum, not `.value`).
- Pass enum to event: `LucasRecommendationGenerated(stage=rec_stage, ...)`.
- `rec.get("id")` or `rec.get("recommendation_id")` for UUID extraction from dict.

### Test updates

- `TestLucasDailyAnalysisSweep` class fully rewritten to match new `run_daily_analysis` interface.
- Mock returns real `AnalysisReport` dataclass instances (not fake `run_daily_sweep` results).
- New test `test_lucas_daily_analysis_sweep_event_uses_bowtiestage_enum` validates F-iter2-3 contract explicitly.
- Cooldown test now verifies 0 events published (not "kinds passed to orchestrator").

### Results

```
vitalia/backend/tests/workers/test_marketing_crons.py  14/14 PASS  (+1 new test)
vitalia/backend/tests/workers/test_arq_settings.py     10/10 PASS
vitalia/backend/tests/architecture/                   270/270 PASS
```
