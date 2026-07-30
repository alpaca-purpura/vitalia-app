# T-infra-8 review — APPROVED

> Auditor: Claude Opus 4.7 (orchestrator-direct)
> Date: 2026-05-18
> Surface: BE workers (ARQ + idempotent_cron)
> Commit SHA: 088a7ee

## Scope
19 NEW files: `_shared/workers/__init__.py` + `workers/base.py` (idempotent_cron decorator: idempotency via luana_core_idempotency + cron_span OTel + structlog audit + Sentry capture/re-raise) + `workers/arq_settings.py` (WorkerSettings: 11 functions + 11 cron_jobs + redis_settings + keep_result=3600 + max_jobs=50 + health_check_interval=30) + `workers/jobs/__init__.py` + 11 scaffold job files (ALL raise NotImplementedError con story citations).

Key design decisions:
1. `_get_idem_store()` extracted as mockable function for soft-fail when Redis unavailable
2. Sentry graceful degradation via try/except import + _SentrySentinel no-op fallback
3. All `arq.cron()` calls use explicit `name=` (avoids default `cron:fn_name` prefix breaking test assertions)
4. idem TTL 600s (10min dedup window per cron execution guard)
5. All jobs cite implementing story (fidelizacion / agenda / marketing / copilot / inbox / infra)

Test files: 3 NEW files totalling 73 tests (8 base decorator + 9 arq_settings + 55 parametrized job scaffold).

## Categorías scoring (10 BE categories)
1. **DDD layering** — ✅ `_shared/workers/` es infrastructure-layer puro. Jobs scaffold raise NotImplementedError (no business logic premature)
2. **Tenant isolation** — N/A nivel decorator (jobs futuros consumirán tenant_id via context); idempotent_cron es transversal ✅
3. **HIPAA-lite dual filter** — N/A nivel decorator ✅
4. **HIPAA-lite audit log** — ✅ structlog audit trail por job invocation (info-level antes/después execution + error capture). Cumple "logging audit" pero NO es audit_log table sync (esa responsabilidad es del job specific cuando toque PHI)
5. **HIPAA-lite PII sanitization** — ✅ idempotent_cron NO logs args/result (delegate al job specific via cron_span). Si job loguea PHI debe usar sanitize_phi_payload (responsabilidad del implementador job)
6. **HIPAA-lite RBAC** — N/A (jobs son server-side, no user-scoped RBAC) ✅
7. **Migrations idempotentes** — N/A ✅
8. **Extension SDK contracts** — N/A ✅
9. **Anti-duplication / cross-brand mirror** — ✅ idempotent_cron wraps `luana_core_idempotency.IdempotentStore` (NOT mirrored). Cross-brand grep `idempotent_cron` en nicolify/comunify/lupulo = ZERO matches (vitalia-specific Slice 1 first-mover, lift candidate Slice 2 si segunda brand necesita)
10. **Engine boundary** — ✅ ZERO edits a core/luana-core-*/src/. wraps engine factory

## Findings count
- FAIL: 0
- WARN: 0
- INFO: 11 cron job scaffolds raise NotImplementedError by design (fails loud cuando arq invoca un job no-implementado). Cada job cita implementing story para visibilidad

## Validators acceptance.validator_ids
- be_lint_ruff_check: PASS
- be_format_ruff: PASS
- be_arch_fitness_brand: PASS 216/216
- be_test_workers: PASS 73/73
- be_pytest_full: PASS 1198/1198 (54 SKIP Postgres)

## Downstream regression
- Surface: vitalia/backend/src/modules/vitalia/_shared/workers/ → consumido por sub-stories siguientes (fidelizacion / agenda / marketing / copilot / inbox)
- Engine consumer: luana_core_idempotency (one-way wrap). luana_core_observability (cron_span via T-infra-5)
- Cross-brand mirror: ZERO

## Self-fix log
N/A.

## Verdict
**APPROVED**. T-infra-8 establece workers infrastructure con idempotency + observability + Sentry graceful degradation. 11 job scaffolds son honest about boundaries (fail-loud NotImplementedError no silent no-op). Anti-duplication COMPLIANT (engine wrap, no mirror).
