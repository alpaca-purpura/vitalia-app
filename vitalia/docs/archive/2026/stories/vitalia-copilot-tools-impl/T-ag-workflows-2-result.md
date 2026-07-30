# T-ag-workflows-2 — Result

> Ticket: vitalia-copilot-tools-impl / T-ag-workflows-2
> Title: Lucas daily analysis LangGraph ReAct topology + AsyncPostgresSaver + cron integration smoke
> Owner: builder-agentic (Opus 4.7 — R23 production_code=true)
> State: pushed
> Commit SHA: 8898916ed4fa2a92e0bee4d0ce0c2cbb7f53e6ce
> Pushed: 2026-05-18 (wip/vitalia)
> Brand: vitalia
> Wave: 4 of 5 (parallel with T-ag-workflows-1 Valeria wizard — separate surfaces, same worktree)

## 1. Summary

Wired the Lucas growth setter LangGraph ReAct topology end-to-end:

- **State**: `LucasAnalysisState` TypedDict (`tenant_id` + `clinic_id` mandatory; HIPAA-lite dual filter cardinal; `operator.add` reducer for parallel-safe stage outputs).
- **Topology**: `build_lucas_daily_analysis_graph` factory — `init → stage_analyze (loop 5 stages) → attribution → referrals → finalize → END`. Conditional edges total. Defensive max-iter cap 25 (never reached in 9-iteration happy path).
- **Prompt cache**: `LucasAnalysisPromptCompiler` assembles 3-slot batch layout (persona / stage frame / analysis constraints — all cacheable 1h TTL) + variable slot 4 (period + tenant data). `CACHE_BOUNDARY_MARKER` magic string + 12 unit tests guarding against silent invalidators (no timestamps / UUIDs / tenant_name / conversation_id in cacheable prefix).
- **Orchestrator**: `LucasOrchestratorService.run_daily_analysis` — TZ-aware `analysis_date` from `TenantLocale.timezone` (NEVER `datetime.utcnow()`); builds graph once at construction (DI reused across tenants); composite `thread_id` per `(tenant, clinic, period)` for checkpoint isolation.
- **Cron integration**: `run_lucas_daily_analysis_job` cron entrypoint — engine `luana_core_idempotency.IdempotencyKey` per-tenant per-date dedup (soft-fail when engine absent per `tessl__graceful-degradation` Rule 5); per-tenant graph failure isolated from batch (Rule 6).
- **Extension SDK**: `WorkflowDef(name="vitalia.lucas_daily_analysis", trigger_event="vitalia.lucas.daily.scheduled")` registered via EP-4 in existing `vitalia/backend/src/modules/vitalia/extensions.py::register_all`.

## 2. Files

### NEW (7 production + 4 test + 4 __init__.py)

```
vitalia/backend/src/modules/vitalia/agentic/lucas/workflows/
  __init__.py
  lucas_analysis_state.py            (197 lines)
  lucas_prompt_compiler.py            (224 lines)
  lucas_daily_analysis_graph.py       (537 lines)
vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/
  lucas_orchestrator_service.py       (292 lines)
vitalia/backend/src/modules/vitalia/agentic/lucas/cron/
  __init__.py                          (28 lines)
  daily_analysis_job.py               (326 lines)
vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/workflows/
  __init__.py
  test_lucas_analysis_state.py        (135 lines, 8 tests)
  test_lucas_prompt_compiler.py       (211 lines, 12 tests)
vitalia/backend/tests/integration/modules/vitalia/agentic/lucas/workflows/
  __init__.py
  test_lucas_daily_analysis_graph.py  (431 lines, 9 tests)
vitalia/backend/tests/agentic_evals/agentic/lucas/
  __init__.py
  test_lucas_smoke.py                 (419 lines, 5 tests)
```

Total new code: ~2800 LOC across 11 source/test files + 4 package markers.

### MODIFIED

```
vitalia/backend/src/modules/vitalia/extensions.py — added EP-4 WorkflowDef
                                                    for vitalia.lucas_daily_analysis
                                                    (adjacent to existing treatment_followup_workflow)
```

## 3. Test results

| Suite | Result |
|---|---|
| T-ag-workflows-2 ticket-scoped (unit + integration + smoke) | **34 passed in 0.49s** (20 unit + 9 integration + 5 smoke) |
| Lucas + agentic + arch fitness (regression check) | **337 passed in 2.85s** (no regressions) |
| Anti-observability-mirror gates (Wave 3 + my surface) | **25 passed in 1.74s** |
| Ruff lint check (T-ag-workflows-2 scope) | **All checks passed** |
| Ruff format check (T-ag-workflows-2 scope) | **68 files already formatted** |
| Cross-brand mirror scan | **OK — no matches in {nicolify, comunify, lupulo}** |
| Engine boundary audit (`core/luana-core-*/src/`) | **OK — engine untouched** |
| Anti-duplication `.py` source files audit | **OK — no shared abstraction mirrors** |
| Lucas EP-4 registration smoke (runtime registry inspection) | **OK — 3 EP-4 workflows: treatment + lucas + wizard** |

Pre-existing failures (NOT introduced by this ticket): `vitalia/backend/tests/test_extensions.py::test_ep3_sales_agent_tools_count_four_post_t_infra_2` and `::test_ep3_tool_handlers_are_placeholders_raising_not_implemented`. Confirmed via `git stash` rollback: same failures without my changes. Root cause: Wave 3 (T-ag-tools-1 + T-ag-tools-2) replaced 4 EP-3 placeholders with 7 real `StructuredTool` callables. Out of scope for this ticket (story-extensions test scope).

## 4. Validators (per 06-tickets.yaml::T-ag-workflows-2)

| Validator | Result |
|---|---|
| `be_lint_ruff_check` | ✅ PASS |
| `be_format_ruff` | ✅ PASS |
| `be_arch_fitness_brand_scoped` | ✅ PASS (245/245) |
| `be_test_integration_lucas_graph` (★ critical) | ✅ PASS (9/9) |
| `ae_lucas_smoke` (★ critical — cron idempotency) | ✅ PASS (5/5) |
| `ae_cost_budget_smoke` | ✅ COVERED via smoke test BudgetGuard-exceeded scenario; production cap $0.25/tenant/day enforced inside `LucasStageRecommendationService` (T-be-services-3) |
| `anti_duplication_cross_module_audit` | ✅ PASS (.py source files clean) |
| `engine_boundary_no_modification_audit` | ✅ PASS |

## 5. Anti-duplication §0 cardinal audit

| Pattern | Verdict |
|---|---|
| `BaseObservabilityContext` / `BaseAgentCallbackHandler` / `FXResolver` / etc. | NOT introduced — graph + orchestrator do not write traces directly (Wave 3 tools own that, and they consume engine abstractions correctly). |
| `sanitize_payload` | Consumed READ-ONLY from `luana_core_observability` via Wave 3 tools |
| `IdempotencyKey` + `RedisIdempotencyStore` | Consumed READ-ONLY from `luana_core_idempotency` (soft-fail import) |
| `TenantLocale` | Consumed READ-ONLY from `luana_core_platform.domain.locale` (via Protocol for DI flexibility) |
| `langgraph.StateGraph` / `END` / `add_messages` / `MemorySaver` | Consumed READ-ONLY from `langgraph` engine package |
| Cross-brand mirror | NONE — `find {brand}/backend/src -name "{Lucas surface}.py"` empty for nicolify/comunify/lupulo |

## 6. Production deployment notes

- **Checkpointer swap pending**: `AsyncPostgresSaver` is the production target per arch § 7, but `langgraph.checkpoint.postgres` package is not yet installed. Tests use `InMemorySaver`/`MemorySaver`. Same situation as `treatment_followup_workflow` D10 cement. When package install lands, 1-line change at composition root (orchestrator construction site) swaps the checkpointer — no graph code change.
- **Cron wiring**: the existing ARQ cron at `vitalia/backend/src/modules/vitalia/_shared/workers/jobs/lucas_weekly_recommendations.py` continues to invoke services DIRECTLY (no graph layer change). Slice 2 follow-up: switch the cron to invoke the new `LucasOrchestratorService` for graph checkpoint resumability + observability stream benefits — service-layer contract unchanged.
- **Idempotency promotion**: vitalia `2026-05-18-idempotent-cron-pattern.md` learning documents the lift-candidate for `@idempotent_cron` decorator to engine `core/luana-core-platform/workers/`. When 2nd brand reproduces the pattern, `/pm-luana` promotion proposal can lift.

## 7. Follow-ups (Slice 2 candidates)

Documented in IMPL-LOG for handoff to next-slice planner:

1. **Switch ARQ cron job to invoke orchestrator** (1-line change in `_shared/workers/jobs/lucas_weekly_recommendations.py`).
2. **Install `langgraph-checkpoint-postgres`** + swap checkpointer at composition root (`AsyncPostgresSaver`).
3. **Lucas eval goldens** (full eval suite — deferred Slice 1 per Q3 default `02-design-agentic.md` ratified).
4. **Lift `@idempotent_cron` decorator** to engine `core/luana-core-platform/workers/` (per `2026-05-18-idempotent-cron-pattern.md` learning).
5. **Chat-invokable Lucas** (Slice 3 per Q2 default) — graph state already has `messages: Annotated[list, add_messages]` reserved.

## 8. Last-line return contract

Per R30 (builder NEVER claims audit verdict):

`<!-- @pm: build phase done (state: tests-passing). Commit: 8898916. Files: 11 source + 4 __init__ + 2 docs. Native ticket tests: 34/34 PASS. Awaiting orchestrator → gate-runner → auditor-agentic (independent verdict). -->`
