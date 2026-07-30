<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Gherkin verification matrix — Backend partial (T-mk-be-1..6)

**Story:** vitalia-slice-1-marketing
**Surface:** backend
**Date:** 2026-05-20
**Auditor:** auditor-backend
**Scope:** SC-MK-01, SC-MK-02, SC-MK-04 (backend coverage). SC-MK-03 is FE-only (auditor-frontend handles).

> Per `.claude/rules/story-closure-gate.md` § Phase D, each scenario referenced in `06-tickets.yaml::gherkin_coverage[]` is mapped to the asserted test path + verdict.

## SC-MK-01 — Happy: Owner aprueba recomendación Lucas escalar Meta budget

| Layer | Ticket | Test path | gate-output verdict | Effective state |
|---|---|---|---|---|
| Domain entity | T-mk-be-1 | `tests/modules/vitalia/marketing/domain/test_lucas_recommendation_entity.py::test_approve_transitions_status` | PASS | Effective ✅ — entity state machine OPEN→APPROVED |
| Domain entity | T-mk-be-1 | `…::test_approved_sets_undo_until_5min` | PASS | Effective ✅ — undo_until = approved_at + 5 min |
| Infra repo | T-mk-be-2 | `tests/modules/vitalia/marketing/infrastructure/repositories/test_lucas_recommendation_repository.py::test_approve_updates_status` | PASS | Effective ✅ — repo persistence |
| Infra repo | T-mk-be-2 | `…::test_dual_filter_tenant_and_clinic` | PASS | Effective ✅ — HIPAA-lite dual filter |
| Application service | T-mk-be-3 | `tests/modules/vitalia/marketing/application/services/test_lucas_recommendations_service.py::test_approve_sets_status_audit_outbox` | PASS | **Partially ⚠️ — service contract correct in isolation, but production routes do NOT inject real service (T-mk-be-5 finding)** |
| Application service | T-mk-be-3 | `…::test_approve_undo_within_5min` | PASS | Partial ⚠️ |
| Application service | T-mk-be-3 | `…::test_approve_idempotency_dedup` | PASS | **Partial ⚠️ — test asserts InvalidStateTransitionError on already-approved; NO actual Idempotency-Key dedup is tested or wired (presence-only check)** |
| API endpoint | T-mk-be-5 | `tests/modules/vitalia/marketing/api/test_recommendations_endpoints.py::test_approve_endpoint_happy_path` | PASS | **Partial ⚠️ — route returns 200 but factory injects MagicMock; real wire-up missing** |
| API endpoint | T-mk-be-5 | `…::test_approve_idempotency_key_dedup` | PASS | **Partial ⚠️ — tests presence of Idempotency-Key header only, not actual dedup behavior** |
| API endpoint | T-mk-be-5 | `…::test_undo_endpoint_within_5min` | PASS | Partial ⚠️ |
| API endpoint | T-mk-be-5 | `…::test_undo_endpoint_after_window_410` | PASS | Effective ✅ — 410 mapping correct |

**SC-MK-01 verdict:** PASS at test level. ⚠️ At production runtime FAIL because routes inject MagicMock service factories instead of real services (T-mk-be-5 finding F1+F2). Must resolve before merge.

## SC-MK-02 — Negative: Meta API timeout · sync degraded · UI muestra last_known

| Layer | Ticket | Test path | gate-output verdict | Effective state |
|---|---|---|---|---|
| Adapter (timeout) | T-mk-be-4 | `tests/modules/vitalia/connections/meta_ads/test_meta_ads_adapter.py::test_timeout_30s_raises` | PASS | Effective ✅ — 30s timeout raises `httpx.TimeoutException` |
| Adapter (circuit breaker) | T-mk-be-4 | `…::test_circuit_breaker_after_5_consecutive_failures` | PASS | Effective ✅ — 5-fail threshold |
| Adapter (per-tenant isolation) | T-mk-be-4 | `…::test_circuit_breaker_isolated_per_tenant` | PASS | Effective ✅ |
| Adapter (counter reset) | T-mk-be-4 | `…::test_circuit_breaker_success_does_not_increment` | PASS | Effective ✅ |
| Cron soft-fail | T-mk-be-6 | `tests/workers/test_marketing_crons.py::test_channel_metrics_sync_meta_soft_fail_per_tenant` | PASS | Effective ✅ — one tenant error doesn't abort sweep |
| Cron event publish | T-mk-be-6 | `…::test_channel_metrics_sync_meta_publishes_channelsyncfailed_event` | PASS | Effective ✅ — `ChannelSyncFailed` published on per-tenant error |
| Cron cooldown | T-mk-be-6 | `…::test_lucas_daily_analysis_sweep_skips_rejected_30d_cooldown` | PASS | **Partial ⚠️ — test asserts cooldown SET construction; orchestrator dispatch is MagicMock'd (real `LucasOrchestratorService` not wired per T-mk-be-6 finding F2)** |
| API last-known | T-mk-be-5 | `tests/modules/vitalia/marketing/api/test_channels_endpoints.py::test_channel_detail_shows_last_known_when_sync_failed` | PASS | **Partial ⚠️ — test asserts response shape; service returns empty list via MagicMock** |
| API manual sync | T-mk-be-5 | `…::test_manual_sync_endpoint_triggers_retry` | PASS | **Partial ⚠️ — route → MagicMock sync_service** |

**SC-MK-02 verdict:** Adapter resilience ✅ effective. Cron sync orchestration + API integration ⚠️ partial (depends on T-mk-be-5/T-mk-be-6 fixes).

## SC-MK-03 — Edge: Stage tab change · Lucas recommendations re-render correctly

**Backend coverage:** N/A — this scenario is purely FE (URL state + tab re-render). auditor-frontend reviews `T-mk-fe-*-review.md` for this.

⚠️ **Critical risk inherited from T-mk-be-1 (BowtieStage enum FAIL):** Backend currently ships 3 stages (`attract|convert|retain`), spec requires 5 (`attraction|qualification|reservation|adoption|expansion`). FE cannot render 5 tabs without a backend enum cardinality fix. Auditor-frontend must verify whether FE was built to spec (5 tabs) or to backend wrong enum (3 tabs). Cross-surface impact.

## SC-MK-04 — Adversarial: Lucas recommendation aprobación + permission check

| Layer | Ticket | Test path | gate-output verdict | Effective state |
|---|---|---|---|---|
| Repo cross-clinic | T-mk-be-2 | `tests/modules/vitalia/marketing/infrastructure/repositories/test_lucas_recommendation_repository.py::test_other_clinic_cannot_read` | PASS | Effective ✅ — HIPAA-lite dual filter blocks cross-clinic |
| Repo pgcrypto roundtrip | T-mk-be-2 | `tests/modules/vitalia/marketing/infrastructure/repositories/test_channel_sync_state_repository.py::test_oauth_token_pgcrypto_roundtrip` | SKIP (no `VITALIA_PHI_KEK` env) | ⚠️ Skipped — pgcrypto encrypt/decrypt design verified by code review, runtime untested |
| Service range validation | T-mk-be-3 | `tests/modules/vitalia/marketing/application/services/test_lucas_recommendations_service.py::test_approve_action_payload_out_of_range_rejected` | PASS | Effective ✅ — `_validate_action_payload` raises ValueError on > 100k budget |
| API RBAC denied | T-mk-be-5 | `tests/modules/vitalia/marketing/api/test_recommendations_endpoints.py::test_approve_role_recepcion_returns_403` | PASS | Effective ✅ — role `recepcion` denied with 403 |
| API audit log unauthorized | T-mk-be-5 | `…::test_audit_log_unauthorized_attempt_recorded` | PASS | **Partial ⚠️ — test asserts structlog `marketing_api.role_denied` warning, NOT actual `vitalia_audit_log` DB row write per HIPAA-lite mandate (T-mk-be-5 finding W3)** |

**SC-MK-04 verdict:** ⚠️ Partial. RBAC denial enforced at route layer, but the HIPAA-lite audit_log row write on 403 attempts is missing (only structlog warning). HIPAA-lite Rule § Audit log is CARDINAL: "TODA lectura/modificación de PHI registra row. NO opcional." Must be wired before merge.

## Cross-cutting backend scenario gaps

| Concern | Status | Source |
|---|---|---|
| BowtieStage cardinality (5 stages) | ❌ FAIL (3 shipped) | T-mk-be-1 finding |
| RejectReason enum values | ❌ FAIL (wrong 4 values) | T-mk-be-1 finding |
| ReferralModel `conversion_value_cents` column | ❌ FAIL (missing) | T-mk-be-2 + T-mk-be-6 findings |
| ReferralStatus `SIGNED_UP` value | ❌ FAIL (missing) | T-mk-be-1 finding (consumed by T-mk-be-6) |
| LucasRecommendationsService runtime in routes | ❌ FAIL (MagicMock injection) | T-mk-be-5 finding |
| Service method names (matrix→get_attribution_matrix etc) | ❌ FAIL | T-mk-be-3 + T-mk-be-5 cross-ref |
| LucasOrchestratorService import in lucas_daily cron | ❌ FAIL (wrong class instantiated) | T-mk-be-6 finding |
| Audit log row on 403 attempt (HIPAA-lite) | ⚠️ WARN | T-mk-be-5 finding |
| Idempotency-Key dedup logic | ⚠️ WARN (presence-only check) | T-mk-be-5 finding |
| `referrals_value_sync` runtime correctness | ❌ FAIL (column + status missing) | T-mk-be-6 finding |

## Verdict aggregate

**Backend partial verdict:** CHANGES_REQUESTED.

Effective test-level coverage of gherkin scenarios: PASS (4/4 in CI). Effective runtime/production correctness: FAIL (5/6 tickets have FAIL findings that translate to non-functional production paths once MagicMock factories are removed).

**Action:** Per `.claude/rules/auditor-self-fix-policy.md`, spawn dev-team to address T-mk-be-1, T-mk-be-2, T-mk-be-3, T-mk-be-5, T-mk-be-6 coordinated fix. T-mk-be-4 stands APPROVED (no co-dependency).

After dev-team fix:
1. Add real DI wiring + remove `unittest.mock` from `src/` (T-mk-be-5).
2. Fix BowtieStage + ReferralStatus + RejectReason enums (T-mk-be-1).
3. Add `conversion_value_cents` migration + model (T-mk-be-2).
4. Import real Lucas services + reconcile method names (T-mk-be-3).
5. Fix lucas_daily_analysis_sweep to use `LucasOrchestratorService` (T-mk-be-6).
6. Add `vitalia_audit_log` row on 403 attempts (T-mk-be-5).
7. Replace MagicMock-based test factories with real ORM instances so tests catch schema/contract drift.
8. Re-spawn auditor-backend for re-audit. Cap absoluto 3 audit_iterations (currently iter 1) before ESCALATE Chris.
