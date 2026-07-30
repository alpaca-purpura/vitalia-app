<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->
# Backend Code Review: T-6 BE fideliz workers (6 cron jobs)

**Date:** 2026-05-20
**Brand:** vitalia
**Ticket:** T-6
**Files Reviewed:** 8 (1 `__init__` + 6 sweep workers + 1 test file)
**Verdict:** **PASS**

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Workers en `application/workers/`. Consume `ReEngagementService` via ctx injection. No DB queries directos en workers (delegan a service) |
| 2 | Tenant Isolation | PASS | Workers iteran `ctx["tenant_clinic_pairs"]` lista `(UUID, UUID)`, pasan ambos a `service.detect_*(tenant_id=..., clinic_id=...)` |
| 3 | Soft Deletes | N/A | Workers no eliminan rows |
| 4 | Code Quality | PASS | ruff 0 errors, format clean |
| 5 | SQLAlchemy 2.0 | N/A | Workers no acceden DB direct |
| 6 | Async Consistency | PASS | `async def` en los 6 workers + envelope wrapping correcto |
| 7 | Pydantic v2 / PII | N/A | Workers retornan dicts (return type) — no DTOs requeridos |
| 8 | Migration Quality | N/A | Sin migrations |
| 9 | Security | PASS | NO PHI in logs (UUIDs only), structlog binding |
| 10 | Tests / TDD | PASS | 20 worker smoke tests + 4 arch_envelope gate tests = 24/24 GREEN |
| 11 | Cross-cutting | PASS | structlog, exception propagation correcto (engine envelope re-raise post-Sentry), `@cron_envelope` engine consumido SSoT |
| 12 | Mirror detection | PASS | Cada worker importa `from luana_core_platform.workers.cron_envelope import cron_envelope` — engine SSoT, NO mirror local. Arch test `test_cron_envelope_used.py` enforce |

## Allowlist Movement

- `KNOWN_LEGACY_CRONS` baseline=1 — sin growth. Los 6 workers nuevos usan engine cron_envelope directamente (no allowlist entry needed).

## Gherkin coverage verification

| Scenario | Mapping | Status |
|---|---|---|
| SC-01 Happy multi_session_gap_sweep detects gap | `test_cron_sweeps.py::test_multi_session_gap_sweep_detects_gap_above_alert_days_inserts_event` (subset of 20 worker tests) | EXISTS + PASS |
| SC-03 Edge follow_up_due_sweep T-7d window | `test_cron_sweeps.py::test_follow_up_due_sweep_detects_within_7d_window` | EXISTS + PASS |

## Schedules audit (matches 03-arch-be.md § 4)

| Cron | Spec | Implementation | Status |
|---|---|---|---|
| multi_session_gap_sweep | daily 07:00 UTC | `0 7 * * *` | ✓ |
| follow_up_due_sweep | daily 07:30 UTC | `30 7 * * *` | ✓ |
| maintenance_due_sweep | daily 08:00 UTC | `0 8 * * *` | ✓ |
| absence_sweep | weekly Mon 06:00 UTC | `0 6 * * 1` | ✓ |
| nps_post_treatment_sweep | hourly :15 | `15 * * * *` | ✓ |
| re_engagement_response_timeout_sweep | daily 09:00 UTC | `0 9 * * *` | ✓ |

## Verdict Math

- 12 PASS / 0 WARN / 0 FAIL → **PASS**

## Skills Consulted Trace

✓ backend-expert (runtime-quality-checklist + architectural-fitness ratchet pattern) — per T-6-result.md
