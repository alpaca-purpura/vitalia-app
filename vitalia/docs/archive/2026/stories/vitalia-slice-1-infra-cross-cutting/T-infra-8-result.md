# T-infra-8 Result — ARQ cron workers scaffold + idempotent base

**Ticket:** T-infra-8  
**Story:** vitalia-slice-1-infra-cross-cutting  
**State:** tests-passing  
**Date:** 2026-05-18  
**Builder:** builder-backend Sonnet (production_code=false)  
**Branch:** wip/vitalia-slice-1-shipping

---

## Summary

Implemented the ARQ cron worker scaffold for Vitalia Slice 1. Deliverables:

1. **`idempotent_cron` decorator** (`_shared/workers/base.py`) — wraps async cron job functions with idempotency key check (luana_core_idempotency), OTel cron_span (T-infra-5), structlog audit on success, Sentry capture + re-raise on exception.

2. **`WorkerSettings`** (`_shared/workers/arq_settings.py`) — ARQ worker config: 11 functions + 11 cron_jobs + `redis_settings` (from `REDIS_URL` env) + `keep_result=3600` + `max_jobs=50` + `health_check_interval=30`.

3. **11 scaffold job functions** (`_shared/workers/jobs/`) — all raise `NotImplementedError` with story citation. Schedules per spec: fidelizacion (1h/6h/12h/1h), agenda (1h/1h/15min), nps (1h), marketing (daily 03:00 UTC), copilot (weekly Mon 04:00 UTC), inbox (15min), retention (monthly 1st 02:00 UTC).

---

## Files Created (19 new files)

```
vitalia/backend/src/modules/vitalia/_shared/workers/
├── __init__.py
├── base.py                          # idempotent_cron decorator
├── arq_settings.py                  # WorkerSettings
└── jobs/
    ├── __init__.py
    ├── followup_24h.py
    ├── reactivation_45d.py
    ├── maintenance_90d.py
    ├── deposit_reminder_24h.py
    ├── appointment_reminder_24h.py
    ├── appointment_reminder_2h.py
    ├── nps_request_24h_post_appointment.py
    ├── brand_studio_audit_30d.py
    ├── lucas_weekly_recommendations.py
    ├── channel_sync_state_15min.py
    └── audit_log_retention_sweep_monthly.py

vitalia/backend/tests/workers/
├── __init__.py
├── test_base.py                     # 8 tests — idempotent_cron decorator
├── test_arq_settings.py             # 9 tests — WorkerSettings struct
└── test_jobs.py                     # 55 parametrized tests — 11 scaffolds × 5 assertions
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `_get_idem_store()` as standalone function | Enables `patch("...base._get_idem_store", return_value=mock_store)` without Redis in unit tests |
| Sentry graceful degradation via `try/except ImportError` + `_SentrySentinel` | Avoids hard dependency on sentry-sdk in dev/test environments |
| `idem_ttl_seconds=600` (10min) | Dedup window covers cron execution burst on retry without blocking next scheduled fire |
| Explicit `name=` on all `arq.cron()` calls | ARQ default name is `cron:{fn_name}` — explicit avoids prefix mismatch in tests and Sentry breadcrumbs |
| All jobs cite implementing story in NotImplementedError | Transparency — operator can trace which story will implement the job body |
| `downstream-regression-na: brand-local` | Workers are Vitalia-specific; no cross-brand consumers of cron scaffold |

---

## Validators

| Gate | Result | Details |
|---|---|---|
| `ruff check` (lint) | PASS | 0 errors, 0 warnings |
| `ruff format --check` | PASS | Applied, 0 would reformat |
| `be_arch_fitness_brand` | PASS | 216/216 arch tests |
| `be_test_workers_cron` | PASS | 73/73 workers tests |
| Full BE suite | PASS | 1198 passed, 54 skipped (integration/Postgres — expected) |

---

## Anti-patterns Avoided

- No silent fallback swallowing exceptions — all exceptions propagate (Sentry captures, then re-raise)
- No hardcoded `tenant_id` — jobs iterate tenants in real implementation (Slice 2+)
- No TZ-naive datetime — UTC is engine default; tenant TZ resolution deferred to impl
- No cross-brand imports
- No `git add .` / `--no-verify`

---

## Remaining Tickets

- T-infra-6: Fidelizacion module scaffold (patient_loyalty, re_engagement tables — Postgres required)
- T-infra-7: Agenda module scaffold (appointments, booking_slots — Postgres required)
