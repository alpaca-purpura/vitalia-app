# T-ag-workflows-2 — Implementation log

> Ticket: vitalia-copilot-tools-impl / T-ag-workflows-2
> Owner: builder-agentic (Opus 4.7 — R23 production_code=true)
> Brand: vitalia
> Surface: agentic (Lucas growth setter LangGraph + cron integration)

## Skills consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Lucas inhabits `agentic/lucas/` (sibling to `copilot/`); same anti-duplication §0 cardinal + observability conventions apply. | Consumed `sanitize_payload` from engine, NO new `Base*` subclass. Validated cache slot architecture matches 3-slot batch-nature layout for Lucas (per 03-arch-agentic § 5.3). Confirmed engine boundary cardinal: NEVER edit `core/luana-core-*/src/`. |
| `sales-agent-expert` | §0 anti-duplication inventory cross-check. Lucas is NOT a sales_agent surface but skill protects same shared abstractions. | Confirmed Lucas does NOT mirror `turn_envelope.py` / `callback_handler.py` — observability traces are emitted by tools (Wave 3) via `_TraceEventRepoLike` Protocol consumed from engine `BaseTraceEventRepoProtocol`. Graph itself only logs via `structlog`. |
| `tessl__langgraph` | LangGraph 2.0 ReAct topology design. | Adopted: TypedDict `LucasAnalysisState` with `tenant_id` + `clinic_id` mandatory; `operator.add` reducer for `stage_recommendations` (parallel-safe defensively); `add_messages` reducer for messages; conditional edges total (no dangling); production checkpointer `AsyncPostgresSaver` MANDATORY but `langgraph.checkpoint.postgres` package NOT installed in workspace — adopted SAME pattern as `treatment_followup_workflow` D10 (CheckpointerProtocol abstract; tests use `InMemorySaver`; production swap = 1-line). Max-iter cap 25 (defensive — never reached in 5-stage happy path = 9 iterations). |
| `tessl__graceful-degradation` | Per-stage / attribution / referrals exceptions wrapped per Rule 5. | Adopted: graph nodes catch tool-side exceptions → synthesize DTO with `status='skipped_timeout'` → continue. Graph-level crash bubbles to cron job which captures per-tenant + isolates from batch (Rule 6). Idempotency soft-fail when engine `luana_core_idempotency` unavailable (Rule 5). |
| `claude-api` | Prompt cache slot architecture validation. | Adopted: 3-slot batch layout (Lucas persona / stage frame / analysis constraints — all cacheable 1h TTL) + variable slot 4 (period + tenant data). `CACHE_BOUNDARY_MARKER` magic string terminates cacheable region. Validation tests guard against silent invalidators: NO timestamps, NO UUIDs, NO conversation_id, NO tenant_name interpolation in cacheable prefix. Per-stage cache partition via `{stage}` interpolation in slot 2 (the only allowed cache-key variant). |

## Step 0.5 — Default-flip detection

No `core/luana-core-platform/src/luana_core_platform/config.py` defaults touched. N/A per `.claude/rules/anti-default-flip-audit.md`.

## Cross-module systems audit (NO-NEW-LAYER)

Pre-write greps performed:

- `find ${WS}/core ${WS}/{nicolify,vitalia,comunify,lupulo}/backend/src -name "lucas_*.py"` → only `vitalia/backend/src/modules/vitalia/agentic/lucas/` matches (NO mirrors elsewhere).
- `grep -rln "build_lucas_daily_analysis_graph\|LucasOrchestratorService" core/` → no engine mirror.
- Existing `vitalia/backend/src/modules/vitalia/_shared/workers/jobs/lucas_weekly_recommendations.py` invokes services DIRECTLY (no graph layer). This ticket ADDS the graph layer + orchestrator + cron entrypoint as a NEW surface — the existing ARQ cron job continues to work unchanged. Switching the cron to invoke the new orchestrator is a Slice 2 follow-up (no contract change at the service layer).
- Engine `luana_core_idempotency.{domain.key.IdempotencyKey,infrastructure.redis_store.RedisIdempotencyStore}` consumed READ-ONLY for per-tenant per-date idempotency (NEVER re-implement). Pattern matches `vitalia/docs/learnings/2026-05-18-idempotent-cron-pattern.md` lift-candidate notes.

## Decisions made during implementation

### D1 — Checkpointer abstraction (production target documented; tests use InMemorySaver)

Per `tessl__langgraph` + arch § 7, production checkpointer is `AsyncPostgresSaver` (`langgraph.checkpoint.postgres.aio`). The package is NOT YET installed in the workspace runtime (verified via `python -c "from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver"` → `ModuleNotFoundError`). This is the SAME situation Wave 2 faced with `RedisSaver` for `treatment_followup_workflow.py` (D10 cement pattern). The factory `build_lucas_daily_analysis_graph(checkpointer=...)` accepts any LangGraph-compatible checkpointer via `CheckpointerProtocol` — tests inject `InMemorySaver` (or `MemorySaver`); production swap is 1-line at composition root when the package install lands. No runtime contract change required.

### D2 — Idempotency at orchestrator vs. cron layer

The existing ARQ cron at `_shared/workers/jobs/lucas_weekly_recommendations.py` is decorated `@idempotent_cron("vitalia.cron.lucas_weekly_recommendations", idem_ttl_seconds=3600)` (engine `luana_core_idempotency` consumed via vitalia-local `_shared/workers/base.py` wrapper). That decorator dedups on `ARQ job_id` (preventing double-fire on retry bursts).

This story adds an ADDITIONAL idempotency layer at the new orchestrator integration entrypoint (`run_lucas_daily_analysis_job`) keyed by `(tenant_id, analysis_date)` — composing `IdempotencyKey(namespace="vitalia.lucas.daily_analysis", key=f"{tenant_id}:{date}")`. This protects against an explicit re-trigger for the SAME tenant on the SAME local date — even if the ARQ wrapper job_id changes (e.g., manual replay). The smoke test `test_smoke_idempotency_prevents_duplicate_work_same_tenant_same_day` verifies the 2nd call has NO stage handler invocation (deduped before graph entry).

Soft-fail: if engine package import fails (test env without engine install), `_build_idempotency_key` returns None and caller proceeds — graceful degradation per `tessl__graceful-degradation` Rule 5.

### D3 — TZ-aware analysis_date computed from TenantLocale.timezone

Per `.claude/rules/master-data.md` cardinal: `analysis_date` MUST come from `TenantLocale.timezone` — NEVER `datetime.utcnow().date()`. The `compute_run_date(tz_name, now_utc=None)` helper in `lucas_orchestrator_service.py` uses `zoneinfo.ZoneInfo` to translate UTC → tenant local date. Smoke test `test_smoke_tz_aware_analysis_date_uses_tenant_timezone` injects `now_utc=2026-05-19 03:00 UTC` for a Lima tenant (UTC-5) and asserts `analysis_date == "2026-05-18"` (tenant-local previous day). Period is derived from the analysis_date (also TZ-aware).

### D4 — Graph topology: ReAct iteration over stages list (NOT supervisor)

Per arch § 3.4 the Lucas graph is "ReAct topology" — but in this domain "ReAct" means "iterate one stage at a time, persist, advance" rather than the classical "reason → act → observe loop". The graph dequeues stages from `state["stages_to_analyze"]` via `stage_loop_router` conditional edge until empty, then single-shot attribution → single-shot referrals → finalize → END. This is bounded by the stage list (5 stages) rather than a recursion-limit. Defensive `MAX_ITERATIONS_HARD_CAP = 25` is set per `tessl__langgraph` recommendation but is NEVER reached in happy path (= 9 iterations: init + 5 stage_analyze + attribution + referrals + finalize).

### D5 — Stage Literal preserved per tool input contract

The tool `compute_stage_recommendation.py` (Wave 3) has Pydantic input `stage: Literal["attraction", "qualification", "reservation", "adoption", "expansion"]`. The `agentic/lucas/domain/enums/stage.py` `StageEnum` uses different names (`attraction/capture/nurture/opportunity/retention` — aligned with analytics engine `STAGE_CHANNEL_MAP`). The graph uses the DESIGN funnel names (matching tool Literal) because:
1. The tool is the integration boundary — its Literal is the public contract.
2. The reasoning frame MD (`lucas_stage_reasoning_frame.md`) documents the 5 design stages.
3. The service layer (`LucasStageRecommendationService`) translates internally if needed.

`Stage` Literal in `lucas_analysis_state.py` matches `tools/compute_stage_recommendation.py` byte-for-byte (kept in sync explicitly).

## Files created (NEW)

### Production code

| Path | LOC | Purpose |
|---|---|---|
| `vitalia/backend/src/modules/vitalia/agentic/lucas/workflows/__init__.py` | 33 | Package exports |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/workflows/lucas_analysis_state.py` | 197 | TypedDict state schema + `initial_state` factory + `Stage` Literal + `MAX_ITERATIONS_HARD_CAP` |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/workflows/lucas_prompt_compiler.py` | 224 | Cacheable slot 1+2+3 + variable slot 4 composer + `CACHE_BOUNDARY_MARKER` |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/workflows/lucas_daily_analysis_graph.py` | 537 | LangGraph ReAct factory + 5 nodes + `_stage_loop_router` + `build_thread_config` + 3 handler Protocols + `CheckpointerProtocol` |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/application/services/lucas_orchestrator_service.py` | 292 | `LucasOrchestratorService.run_daily_analysis` + `AnalysisReport` DTO + `compute_run_date` / `compute_run_period` TZ-aware helpers |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/cron/__init__.py` | 28 | Package exports |
| `vitalia/backend/src/modules/vitalia/agentic/lucas/cron/daily_analysis_job.py` | 326 | `run_lucas_daily_analysis_job` + `TenantRunInput` / `TenantRunResult` / `LucasDailyAnalysisJobInput,Result` DTOs + engine `IdempotencyKey` per-tenant per-date soft-fail wrapping |

### Tests

| Path | LOC | Tests |
|---|---|---|
| `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/workflows/test_lucas_analysis_state.py` | 135 | 8 unit tests — state schema mandatory keys, factory defaults, accumulators empty at start, `DEFAULT_STAGES` ordering, `MAX_ITERATIONS_HARD_CAP=25` |
| `vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/workflows/test_lucas_prompt_compiler.py` | 211 | 12 unit tests — cache prefix byte-equality, no silent invalidators (timestamps / UUIDs / tenant_name / conversation_id), boundary marker placement, slot header order, period validation |
| `vitalia/backend/tests/integration/modules/vitalia/agentic/lucas/workflows/test_lucas_daily_analysis_graph.py` | 431 | 9 integration tests — graph compile, happy path 5 stages, iterations bounded, partial-success on per-stage failure, attribution failure synthesises skipped, period bounds → attribution handler, state schema invariants, public factory signature contract |
| `vitalia/backend/tests/agentic_evals/agentic/lucas/test_lucas_smoke.py` | 419 | 5 smoke tests — 2 tenants complete successfully, idempotency dedup same tenant+date, BudgetGuard exceeded → status='skipped_budget', per-tenant failure isolated from batch, TZ-aware date from locale.timezone |

## Files modified

| Path | Change |
|---|---|
| `vitalia/backend/src/modules/vitalia/extensions.py` | EP-4 registration: added `WorkflowDef(name=_ns("lucas_daily_analysis"), trigger_event="vitalia.lucas.daily.scheduled")` adjacent to existing `treatment_followup_workflow` entry. Total EP-4 workflows now: 3 (treatment + lucas + wizard — wizard added by parallel Wave 4 builder T-ag-workflows-1). |

## Tests run + results

### Ticket-scoped suite (34 tests)

```bash
cd ${WS} && .venv/bin/pytest \
  vitalia/backend/tests/unit/modules/vitalia/agentic/lucas/workflows/ \
  vitalia/backend/tests/integration/modules/vitalia/agentic/lucas/workflows/ \
  vitalia/backend/tests/agentic_evals/agentic/lucas/ \
  --override-ini="addopts=" -v --tb=short
```

Result: **34 passed in 0.49s** (20 unit + 9 integration + 5 smoke).

### Broader regression check (337 tests — Lucas + arch fitness)

```bash
cd ${WS} && .venv/bin/pytest \
  vitalia/backend/tests/unit/modules/vitalia/agentic/ \
  vitalia/backend/tests/integration/modules/vitalia/agentic/ \
  vitalia/backend/tests/agentic_evals/agentic/ \
  vitalia/backend/tests/architecture/ \
  --override-ini="addopts=" -q --tb=line
```

Result: **337 passed in 2.85s** — zero regressions from Wave 3 / 5 (T-ag-tools-3 Lucas tools + arch fitness gates).

### Anti-mirror gates (25 tests)

```bash
cd ${WS} && .venv/bin/pytest \
  vitalia/backend/tests/architecture/test_no_observability_mirror_copilot.py \
  vitalia/backend/tests/architecture/test_no_observability_mirror_sales_agent.py \
  vitalia/backend/tests/architecture/test_no_observability_mirror.py \
  --override-ini="addopts=" -v --tb=short
```

Result: **25 passed in 1.74s** — observability subclass invariants intact (Wave 3 + my additions).

### Cross-brand mirror scan + engine boundary

```bash
# Cross-brand scan
for tool in lucas_daily_analysis_graph lucas_prompt_compiler lucas_analysis_state daily_analysis_job lucas_orchestrator_service; do
  for B in nicolify comunify lupulo; do find $B/backend/src -name "${tool}.py" 2>/dev/null; done
done
```
→ no matches → PASS

```bash
git diff --name-only main...HEAD | grep -E "^core/luana-core-[^/]+/src/"
```
→ empty → PASS (engine src untouched).

### Anti-duplication (.py source files only)

```bash
grep -rln --include="*.py" "class.*\(BaseObservabilityContext\|BaseAgentCallbackHandler\|...\)" \
  vitalia/backend/src/modules/vitalia/{copilot,sales_agent,agentic}/ | \
  xargs grep -L "from luana_core_observability\|..."
```
→ empty (.py only) → PASS. (Note: validator command in 04-validators.yaml grep'd `.pyc` cache files → pre-existing CI infra noise; my surface has zero `.py` violations — same situation as Wave 3 T-ag-tools-3 result.)

### Pre-existing failures (NOT introduced by this ticket)

- `vitalia/backend/tests/test_extensions.py::test_ep3_sales_agent_tools_count_four_post_t_infra_2` — pre-existing fail from Wave 3 (T-ag-tools-1 + T-ag-tools-2 replaced 4 placeholders with 7 real tools, so count assertion 4 → 11 violates). Confirmed via `git stash` rollback test — fails identically without my changes.
- `vitalia/backend/tests/test_extensions.py::test_ep3_tool_handlers_are_placeholders_raising_not_implemented` — same root cause; real tools are now `StructuredTool` not callable placeholders. Pre-existing.

These belong to `vitalia/backend/tests/test_extensions.py` (Story 11 Part A pre-existing scope) — NOT in this ticket's validator scope. Wave 3 already documented as known issue.

## Validator status

| Validator ID | Surface | Status |
|---|---|---|
| `be_lint_ruff_check` | T-ag-workflows-2 files | ✅ PASS (all checks passed after auto-fix import order + format) |
| `be_format_ruff` | T-ag-workflows-2 files | ✅ PASS (68 files already formatted post format pass) |
| `be_arch_fitness_brand_scoped` | full suite | ✅ PASS (245/245 — no regressions) |
| `be_test_integration_lucas_graph` | ★ critical | ✅ PASS (9/9 in `test_lucas_daily_analysis_graph.py`) |
| `ae_lucas_smoke` | ★ critical cron idempotency | ✅ PASS (5/5 in `test_lucas_smoke.py`) |
| `ae_cost_budget_smoke` | Lucas budget cap | ✅ COVERED via `test_smoke_budget_exceeded_yields_skipped_budget_status` (BudgetGuard exceeded → status='skipped_budget' for all 5 stages; attribution + referrals still ran). Production runtime BudgetGuard cap $0.25/tenant/day is enforced INSIDE `LucasStageRecommendationService` (T-be-services-3) — graph respects the service contract. |
| `anti_duplication_cross_module_audit` | T-ag-workflows-2 surfaces | ✅ PASS (.py source files clean; .pyc false positives pre-existing CI noise per Wave 3) |
| `cross_brand_mirror_scan` | Lucas surfaces | ✅ PASS (no matches in nicolify/comunify/lupulo) |
| `engine_boundary_no_modification_audit` | git diff vs main | ✅ PASS (no `core/luana-core-*/src/` modifications) |

## Anti-duplication §0 audit summary

| Pattern | Shared abstraction consumed | Status |
|---|---|---|
| Observability sanitization | `luana_core_observability.recording.sanitization.sanitize_payload` (via Wave 3 tools — graph + orchestrator do not write traces directly) | ✅ READ-ONLY consumed via tools |
| LangGraph base classes | `langgraph.graph.StateGraph`, `END`, `add_messages` | ✅ Engine SSoT — NEVER mirror |
| LangGraph checkpointer | `langgraph.checkpoint.memory.InMemorySaver`/`MemorySaver` (tests); `AsyncPostgresSaver` (prod, package install pending) via `CheckpointerProtocol` abstraction | ✅ Engine SSoT |
| Idempotency primitives | `luana_core_idempotency.domain.key.IdempotencyKey` + `RedisIdempotencyStore` (soft-fail when engine absent) | ✅ Engine SSoT |
| TenantLocale | `luana_core_platform.domain.locale.TenantLocale` (consumed by orchestrator via `TenantLocaleProtocol` for DI flexibility) | ✅ Engine SSoT |
| Stage Literal | `vitalia/agentic/lucas/tools/compute_stage_recommendation.py` (Wave 3) | ✅ Brand-internal SSoT — graph imports same Literal for byte-equal contract |

NEW abstractions introduced this ticket:
- `LucasAnalysisState` (TypedDict) — Lucas-specific. No equivalent in `core/luana-core-*/` (sales_agent / copilot have their own state schemas).
- `LucasAnalysisPromptCompiler` — Lucas-specific (3-slot batch layout differs from Adrián 6-slot + Valeria 5-slot — sibling brand surfaces also brand-specific compilers).
- `LucasOrchestratorService` — Lucas-specific (DI wrapper). Slice 2+ candidate for lift to `core/luana-core-platform/workers/` once 2nd brand reproduces the cron→graph→services pattern.
- `run_lucas_daily_analysis_job` cron entry — Lucas-specific cron entrypoint. Lift-candidate documented in `vitalia/docs/learnings/2026-05-18-idempotent-cron-pattern.md`.

No cross-brand mirror introduced. No engine modification. All anti-duplication §0 invariants honored.

## Notes for auditor

1. The OTHER parallel Wave 4 builder (T-ag-workflows-1 Valeria wizard supervisor) added `wizard_onboarding_supervisor` to EP-4 registry — this is intentional + cross-checked at the `extensions.py` runtime registration test (EP-4 now has 3 workflows: treatment + lucas + wizard).
2. The story checkpoint update is NOT in my scope — story-orchestrator owns checkpoint progression.
3. Production checkpointer swap is a follow-up: install `langgraph-checkpoint-postgres` package + change 1 line at composition root (orchestrator service construction site). The `CheckpointerProtocol` abstraction in `lucas_daily_analysis_graph.py` is the contract surface; no graph code change needed.
