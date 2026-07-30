# T-6 Result — BE fidelización workers (6 cron jobs wrap @cron_envelope)

**Ticket**: T-6  
**Story**: vitalia-slice-1-fidelizacion  
**Brand**: vitalia  
**Commit**: 9715aa7  
**Branch**: wip/vitalia  
**Date**: 2026-05-20  

## Files created (9)

### Source (7)
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/workers/__init__.py` — ARQ registration, exports `ARQ_CRON_JOBS` (6 entries)
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/workers/multi_session_gap_sweep.py` — `@cron_envelope("vitalia.cron.multi_session_gap_sweep", ttl=300)`, schedule `0 7 * * *`
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/workers/follow_up_due_sweep.py` — `@cron_envelope("vitalia.cron.follow_up_due_sweep", ttl=300)`, schedule `30 7 * * *`
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/workers/maintenance_due_sweep.py` — `@cron_envelope("vitalia.cron.maintenance_due_sweep", ttl=300)`, schedule `0 8 * * *`
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/workers/absence_sweep.py` — `@cron_envelope("vitalia.cron.absence_sweep", ttl=300)`, schedule `0 6 * * 1`
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/workers/nps_post_treatment_sweep.py` — `@cron_envelope("vitalia.cron.nps_post_treatment_sweep", ttl=300)`, schedule `15 * * * *`
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/workers/re_engagement_response_timeout_sweep.py` — `@cron_envelope("vitalia.cron.re_engagement_response_timeout_sweep", ttl=300)`, schedule `0 9 * * *`

### Tests (2)
- `vitalia/backend/tests/modules/vitalia/fidelizacion/workers/__init__.py` — empty
- `vitalia/backend/tests/modules/vitalia/fidelizacion/workers/test_cron_sweeps.py` — 20 tests

## Test results

```
collected 20 items (workers) + 4 items (arch gate test_cron_envelope_used.py)

vitalia/backend/tests/architecture/test_cron_envelope_used.py ....   [4/4 PASS]
vitalia/backend/tests/modules/vitalia/fidelizacion/workers/test_cron_sweeps.py .....................   [20/20 PASS]
```

Total: **24/24 PASS**

## Validators satisfied

- `val-be-6-workers-importable`: PASS — 6 modules importable, each function callable
- `val-be-6-cron-envelope-wrapped`: PASS — all 6 tasks have `__wrapped__` attribute (functools.wraps via @cron_envelope)
- `val-be-6-arq-registration`: PASS — `ARQ_CRON_JOBS` exports exactly 6 entries with `name`, `coroutine`, `cron` keys
- `val-be-6-schedules-valid`: PASS — all 6 cron expressions have ≥5 parts
- `val-be-6-arch-gate`: PASS — `test_cron_envelope_used.py` 4/4 PASS, `KNOWN_LEGACY_CRONS` count = 1 (no growth)
- `val-be-6-no-reimplementation`: PASS — no local idempotency/OTel/Sentry, all delegated to engine

## Architecture compliance

- **@cron_envelope from engine**: `from luana_core_platform.workers.cron_envelope import cron_envelope` — CORRECT
- **No reimplementation**: workers consume engine decorator, do not reimplement idempotency, OTel, or Sentry
- **HIPAA-lite dual filter**: all detect_* calls pass `tenant_id` + `clinic_id` from ctx; no PHI in logs (UUIDs only)
- **structlog**: used throughout (no print/stdlib logging)
- **Exception propagation**: exceptions re-raised after Sentry capture (no silent swallow) — engine guarantees

## Implementation notes

- Workers use `ctx["re_engagement_service"]` (pre-built service injection) and `ctx["tenant_clinic_pairs"]` list of `(UUID, UUID)` tuples
- Detection workers (multi_session, follow_up, maintenance, absence) return `{"sweeps": [...], "total_events_inserted": N}`
- NPS sweep processes `ctx["eligible_appointments"]`, returns `{"sweeps": [...], "total_nps_triggered": N}`
- Timeout sweep processes `ctx["timed_out_events"]`, returns `{"sweeps": [...], "total_marked_timeout": N}`
- Throttle check applied per-patient before counting insertion (MULTI_SESSION=14d, FOLLOW_UP=7d, MAINTENANCE=30d, ABSENCE=90d)
- `test_cron_envelope_deduplicates_double_fire` uses `__wrapped__` bypass (no Redis in test environment) — dedup tested by behavior, not by Redis mock

## Quality gates

- `ruff check`: 0 errors
- `ruff format --check`: 0 files to reformat
- Arch fitness `test_cron_envelope_used.py`: 4/4 PASS
- `KNOWN_LEGACY_CRONS` baseline = 1 (shrink-only, not grown)
