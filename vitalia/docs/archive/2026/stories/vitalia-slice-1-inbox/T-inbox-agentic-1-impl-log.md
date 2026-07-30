# T-inbox-agentic-1 — Implementation Log

> Story: vitalia-slice-1-inbox · Brand: vitalia · Surface: agentic (R23 Opus 4.7)
> Builder: Claude Opus 4.7 (1M context) · Mandate: R23 production_code=true
> Started: 2026-05-20 UTC · Date captured: `date -u +%Y-%m-%d` → 2026-05-20

## Step 0 — Skills consulted (must_load enforcement v4.1)

Per `05-guidelines.md § 1` + R23 + caller prompt § "MUST LOAD SKILLS". All skills
invoked at session start before any code.

| # | Skill | Why invoked | Decision applied |
|---|---|---|---|
| 1 | `sales-agent-expert` | §3 "NO se toca" surfaces verified — only adding a tool, NOT modifying Closer Studio/SmartBuffer/OutputManager/follow_up_engine/PromptVersionModel. Pattern reference: existing `screening_questions`/`send_payment_link`/`reschedule_appointment` tools (T-ag-tools-2 cement). Tool delegates to service; observability via engine `SalesAgentObservabilityContext` (shipped — NEVER mirror). | Followed canonical 3-tool pattern: `@tool` LangChain decorator + Pydantic v2 args_schema + DI resolver hook + async + service-resolved (no raw repos). `tenant_id` + `clinic_id` mandatory per HIPAA-lite cardinal. Tool surface NEVER logs `reason` verbatim (PII containment). |
| 2 | `copilot-expert` | Tool registration pattern (EP-3 via `extensions.py::register_all`) deferred to T-inbox-be-6 per ticket DAG. Verified anti-duplication §0: tool does NOT mirror engine observability/cost/pricing. Activity Stream consumption (Section 4 of skill) handled by T-inbox-be-3 ActivityEventService, not by this ticket. | No engine modification. Tool stays brand-extension only. EP-3 registration delegated downstream (T-inbox-be-6). |
| 3 | `tessl__langgraph` | Tool definition pattern for LangGraph workflow consumption. `@tool` decorator from `langchain_core.tools` (canonical, used by all 3 sibling tools in vitalia). Async coroutine + Pydantic v2 args_schema = standard LangChain BaseTool surface. | Confirmed pattern. Tool exposes `.ainvoke()` for async dispatch + `.name='retract_last_message'` + `.args_schema=RetractLastMessageInput`. No subagent needed (single-step tool, no LangGraph node added). |
| 4 | `claude-api` | Anthropic prompt caching slot architecture (per 03-arch-agentic § 3). Cache prefix invariant CRITICAL — tool description must NOT include dynamic tenant/conv references; uses placeholders resolved at runtime. TTL 5min default (engine cementado). | Tool description uses Pydantic Field descriptions (resolved at tool registration, not per-turn). NO timestamps/conversation_id/tenant_name in cache prefix. Auditor will verify `cache_read_input_tokens > 0` on iter 2+ (validator `agentic_cache_hit_rate` post-deploy). |
| 5 | `tessl__graceful-degradation` | External calls (channel adapter retract_message_id) wrapped in service layer via T-inbox-be-3 RetractMessageService (timeout 5s + fallback). Tool surface adds defense-in-depth envelope (`try/except Exception` → Spanish summary, never re-raise). | Tool NEVER raises — all 6 exception paths (ActionReceiptExpired/PatientReplied/MessageNotRetractable/RuntimeError resolver/generic Exception/structured failure with fallback_applied) reduce to deterministic Spanish neutral summary strings. |
| 6 | `.claude/rules/copilot-resilience.md` | Best-effort observability — recorder NEVER breaks turn. Tool surface follows: structlog warnings on failure paths, no PII in log statements (only opaque IDs). | Applied: all log lines use `error_type=type(exc).__name__` + `conversation_id=str(...)` + `message_id=str(...)`. NEVER log `reason` (PII). |
| 7 | `.claude/rules/copilot-observability.md` | `copilot_llm_call` + `copilot_trace_event` writes happen at engine level via shipped `SalesAgentObservabilityContext` callback handler. Tool consumes — never mirrors. PII sanitization via engine `sanitize_payload(compliance_level="hipaa_lite")`. | Confirmed: tool does NOT instantiate any observability recorder. Engine `BaseAgentCallbackHandler.on_tool_start`/`on_tool_end` automatically records this tool invocation. |
| 8 | `.claude/rules/sales-agent-brand-voice.md` | Voice fidelity ≥0.85 (validator `agentic_voice_fidelity_adrian`). Tool itself doesn't generate LLM text; it returns deterministic Spanish strings consumed by LLM as system observations. Brand voice exemption applies to AGENT'S OWN response to patient (post-tool), not to internal tool surface returns. | Tool returns are Spanish neutro (LatAm-safe, no voseo) since they're system-internal observations. The agent's subsequent response to the patient (cementado in golden YAML) preserves Aurora-dental-AR voseo voice. |
| 9 | `.claude/rules/anti-duplication.md` | §0 cardinal — CONSUME engine sales_agent runtime + retract_message_id from T-inbox-be-4 (shipped), NEVER mirror. Cross-codebase grep performed: existing engine `core/luana-core-sales-agent/.../application/agents/sales/tools.py` does NOT have retract_last_message (brand-extension specific to vitalia inbox 5min window pattern). | NO mirror created. Tool wraps `RetractMessageService` (brand-local T-inbox-be-3) which transitively consumes engine adapters. Service Layer owns channel dispatch + fallback semantics. Tool surface stays thin (8 imports total, 3 from project root). |
| 10 | `.claude/rules/tenant-isolation.md` | Every query filtered by `tenant_id`. Service-level dual filter (tenant_id + clinic_id via `CompoundScopeRepositoryBase` heredancia, engine shipped). | Input schema MANDATORY: `tenant_id: UUID` + `clinic_id: UUID` (Pydantic `Field(...)`). Service receives both as kwargs → enforces dual filter on all repos (msg_repo, receipt_repo, conv_repo). |
| 11 | `vitalia/.claude/rules/hipaa-lite.md` | PHI cardinal — 4 obligations: (1) tenant+clinic dual filter, (2) audit log sync write pre-response, (3) sanitization in traces, (4) encryption in transit. | All 4 honored: (1) input schema mandate, (2) service writes audit log row before returning (T-inbox-be-3 cement), (3) sanitize_payload runs in service layer before audit persist (engine), (4) transport via engine in-memory dispatch + WA Business API HTTPS. `reason` field max_length=500 contains PII surface; min_length=10 enforces non-trivial justification. PHI containment: tool surface NEVER returns `reason` verbatim. |
| 12 | `.claude/rules/tdd-mandatory.md` | RED → GREEN → REFACTOR. Tests written FIRST. | Confirmed: `test_retract_last_message.py` (12 tests) written BEFORE `retract_last_message.py`. Initial pytest run confirmed RED (`ModuleNotFoundError: No module named 'src.modules.vitalia.sales_agent.tools.retract_last_message'`). After implementation, all 12 GREEN. |
| 13 | `.claude/rules/auditor-self-fix-policy.md` | When tool added → existing golden count gate (`12`) must be bumped to `13`. This is whitelist self-fix territory (1-line const correction in test scaffold). | Applied: bumped `len(goldens) == 12` → `len(goldens) == 13` in `test_pass_k_evaluation.py` (2 sites — count gate + test_adrian_goldens_count_is_12 renamed to test_adrian_goldens_count_is_13). Total: 4 lines modified across 1 file. Within auditor whitelist #9 (default value correction, scope creep guard NOT triggered: pure cement count update mandated by architect package "1 reinforcement golden NEW Slice 1"). |

**Skill enforcement check:** 13/13 declared skills invoked + decisions cited above.
v4.1 builder-agentic-auditor REVIEW.md FAIL avoided.

## Step 1 — Cross-module audit (NO-NEW-LAYER)

```bash
# Engine sales_agent runtime: read-only consult
grep -rn "retract_last_message" core/luana-core-sales-agent/src/ 2>/dev/null | wc -l
# → 0 (engine has NO equivalent — brand-extension specific to vitalia 5min inbox window)

# Cross-brand mirror scan
for OB in nicolify comunify lupulo; do
  find $OB/backend/src -name "retract_last_message.py" 2>/dev/null
done
# → empty (no cross-brand mirror — vitalia-only feature)

# Service consumption (T-inbox-be-3 shipped)
grep -n "class RetractMessageService" vitalia/backend/src/modules/vitalia/inbox/application/services/retract_message_service.py
# → 79: class RetractMessageService:  (CONSUMED via DI resolver)

# Channel adapter consumption (T-inbox-be-4 shipped, transitive via service)
grep -n "retract_message_id" vitalia/backend/src/modules/vitalia/connections/{whatsapp,instagram,email}/adapter.py
# → all 3 have retract_message_id method (T-inbox-be-4 cement)
```

**Verdict NO-NEW-LAYER:** ZERO new infrastructure created. Tool surface is the
1 NEW Python module + 1 test file + 1 YAML golden. All engine/service abstractions
already exist (T-inbox-be-3, T-inbox-be-4, engine SalesAgentObservabilityContext).

## Step 2 — Files in scope (per ticket)

| # | File | Status | Layer |
|---|---|---|---|
| 1 | `vitalia/backend/src/modules/vitalia/sales_agent/tools/retract_last_message.py` | NEW | Tool surface (brand-extension) |
| 2 | `vitalia/backend/tests/modules/vitalia/sales_agent/tools/test_retract_last_message.py` | NEW (RED first) | Unit tests (12 tests) |
| 3 | `vitalia/backend/tests/agentic_evals/sales_agent/goldens/dental/T-inbox-retract-1.yaml` | NEW | Reinforcement golden |
| 4 | `vitalia/backend/tests/modules/vitalia/sales_agent/__init__.py` | NEW (trivial) | pytest discovery scaffold |
| 5 | `vitalia/backend/tests/modules/vitalia/sales_agent/tools/__init__.py` | NEW (trivial) | pytest discovery scaffold |
| 6 | `vitalia/backend/tests/agentic_evals/sales_agent/test_pass_k_evaluation.py` | EDIT (4 lines) | Count gate bump 12→13 (auditor whitelist self-fix #9) |

**Total: 3 in-scope NEW + 2 trivial __init__.py + 1 minimal count gate edit.**
The 2 `__init__.py` files are mandatory for pytest discovery (project pattern —
every test directory has one). The count gate edit is the natural extension
required by adding a golden (sister gates in same file required identical adjustment).

## Step 3 — TDD cycle

| Phase | Action | Result |
|---|---|---|
| RED | Wrote 12 tests covering happy + 5 edges + adversarial + 4 schema gates + 1 surface metadata | `pytest -x` → `ModuleNotFoundError` (expected) |
| GREEN | Implemented tool with 6 deterministic exception paths + DI resolver + structlog | 12/12 PASS in 0.19s |
| REFACTOR | `ruff format` applied (line-length collapses); 0 manual refactor | 12/12 still PASS in 0.19s |

Verbatim test pass output:
```
collected 12 items
test_retract_last_message.py::test_happy_5min_window PASSED
test_retract_last_message.py::test_expired PASSED
test_retract_last_message.py::test_patient_replied PASSED
test_retract_last_message.py::test_channel_unsupported PASSED
test_retract_last_message.py::test_message_not_retractable PASSED
test_retract_last_message.py::test_unexpected_exception_graceful PASSED
test_retract_last_message.py::test_resolver_not_configured_raises_in_handler PASSED
test_retract_last_message.py::test_input_schema_requires_tenant_and_clinic PASSED
test_retract_last_message.py::test_input_schema_reason_min_length PASSED
test_retract_last_message.py::test_input_schema_reason_max_length PASSED
test_retract_last_message.py::test_input_schema_extra_forbid PASSED
test_retract_last_message.py::test_tool_surface_metadata PASSED
12 passed in 0.19s
```

## Step 4 — Validators run (per `04-validators.yaml::T-inbox-agentic-1::acceptance`)

| Validator id | Command | Result |
|---|---|---|
| `be_lint_ruff_check` | `cd vitalia/backend && ruff check src/modules/vitalia/sales_agent/ tests/modules/vitalia/sales_agent/ tests/agentic_evals/sales_agent/ --no-cache` | ✅ All checks passed! |
| `be_format_ruff_check` | `cd vitalia/backend && ruff format --check src/modules/vitalia/sales_agent/ tests/modules/vitalia/sales_agent/ tests/agentic_evals/sales_agent/` | ✅ 42 files already formatted |
| `be_arch_fitness_brand` | `cd vitalia/backend && pytest tests/architecture/ --override-ini="addopts="` | ✅ 265 passed (includes `test_no_observability_mirror_copilot`) |
| `be_test_inbox` | `cd vitalia/backend && pytest tests/modules/vitalia/inbox/ tests/modules/vitalia/sales_agent/` | ✅ 59 passed (47 pre-existing + 12 new) |
| `agentic_pass_k_adrian_goldens` | `cd vitalia/backend && pytest tests/agentic_evals/sales_agent/test_pass_k_evaluation.py` | ✅ 11 passed (3 trials × pass^k + count + schema + persona refs) |
| `agentic_voice_fidelity_adrian` | `cd vitalia/backend && pytest tests/agentic_evals/sales_agent/test_voice_fidelity_vitalia.py` | ✅ 9 passed |
| (full agentic eval surface) | `cd vitalia/backend && pytest tests/agentic_evals/sales_agent/` | ✅ 43 passed |

**Total quality gates: ALL GREEN.** Native pytest, no docker. Workspace venv root.

## Step 5 — Gherkin coverage matrix (per `06-tickets.yaml::T-inbox-agentic-1::gherkin_coverage`)

| Scenario | Test path | Status |
|---|---|---|
| SC-01 happy (Adrián retract action receipt within 5min) | `test_retract_last_message.py::test_happy_5min_window` | ✅ PASS |
| SC-03 edge: 5min expired | `test_retract_last_message.py::test_expired` | ✅ PASS |
| SC-03 edge: patient replied | `test_retract_last_message.py::test_patient_replied` | ✅ PASS |
| SC-03 edge: channel unsupported (email) | `test_retract_last_message.py::test_channel_unsupported` | ✅ PASS |
| Voice fidelity + compliance integration | `goldens/dental/T-inbox-retract-1.yaml` (via `test_pass_k_evaluation.py`) | ✅ PASS (3 trials) |

All 5 gherkin scenarios covered with executing tests.

## Step 6 — Anti-duplication post-check (cross-codebase grep)

| Pattern | Locations | Verdict |
|---|---|---|
| `class.*Observability.*Context` outside engine | only `vitalia/backend/src/modules/vitalia/sales_agent/observability/recording/turn_envelope.py` (existing shipped — subclass of engine `BaseObservabilityContext` per shipped Story 11 sales_agent base) | ✅ INHERITANCE (not mirror) |
| `def retract_message_id` per-channel adapter (cross-brand) | only `vitalia/.../connections/{whatsapp,instagram,email}/adapter.py` (T-inbox-be-4 brand-local) | ✅ no cross-brand mirror (vitalia-only) |
| `retract_last_message` tool definition | only `vitalia/.../sales_agent/tools/retract_last_message.py` (NEW this ticket) | ✅ no engine equivalent + no cross-brand mirror |
| Engine import `from luana_core_sales_agent.tools.*retract*` | not found | ✅ no engine retract tool exists (brand-specific feature) |

## Step 7 — Cost & cache slot architecture notes

- **LLM cost of tool itself:** $0 (deterministic, no LLM call from tool surface — invokes service which makes 0 LLM calls).
- **Total turn cost impact:** ≤$0.001 USD increment (tool description ~120 tokens added to tools manifest slot 3; cache-stable across turns).
- **Cache prefix invariance preserved (per 03-arch-agentic § 3):**
  - Tool description uses Pydantic Field descriptions (resolved at registration time, NOT per-turn).
  - NO timestamps in description.
  - NO `{tenant_id}` / `{clinic_id}` / `{conversation_id}` placeholders interpolated mid-block.
  - All input parameters use LangChain runtime resolution (passed as kwargs at invocation, NOT serialized into prompt).
- **Auditor will verify cache hit rate post-deploy** via validator `agentic_cache_hit_rate` (must_pass:false, observability check).

## Step 8 — Outstanding (handoff downstream)

- **T-inbox-be-6** (separate ticket, blocked_by: T-inbox-agentic-1) — registers this tool via `registry.sales_agent_tool_register(ToolDef(...))` in `vitalia/backend/src/modules/vitalia/extensions.py`. Pattern verbatim from `screening_questions`/`send_payment_link`/`reschedule_appointment` (T-ag-tools-2 cement, lines 469-571 of extensions.py).
- **Tool DI resolver wiring** — engine sales_agent runtime middleware must call `set_retract_message_service_resolver(...)` at orchestrator init. Pattern verbatim from sibling tools (`set_payment_link_service_resolver`/`set_screening_service_resolver`). Bootstrap landed in T-inbox-be-6 alongside `registry.sales_agent_tool_register`.
- **Tools manifest cache slot 3 refresh** — tools description added increments prefix bytes; cache rebuilds on first turn after deploy. Subsequent turns cache-stable.

## Step 9 — Process metrics

- **Tokens spent (estimate):** ~7k Opus input read (CONTEXT-BRIEF + key spec files) + ~25k output (test+tool+golden+log)
- **Skills loaded (must_load v4.1):** 13/13 declared (R23 enforcement complete)
- **TDD discipline:** RED confirmed before GREEN
- **Files written:** 3 in-scope + 2 trivial __init__.py + 1 minimal count-gate edit = 6 total filesystem touches
- **Quality gates passed:** 5/5 in-scope validators + 1 architecture surface (no regression)
- **Cross-brand pollution risk:** ZERO (only `vitalia/` paths touched)
- **Engine modification risk:** ZERO (engine paths only READ during cross-grep)

## Step 10 — Open questions / deferred decisions

| # | Question | Default decision |
|---|---|---|
| 1 | Should tool emit a separate `AdrianSelfRetractTriggered` event distinct from `MessageRetracted`? | **NO Slice 1.** Service already emits `MessageRetracted` with `retract_reason` field — can be filtered by analytics. Slice 2 lift if event analytics need fine-grain. |
| 2 | Should tool description include voice-style examples (e.g., "When to invoke")? | **NO Slice 1.** Description stays factual + cache-stable. Voice cues live in agent persona slot 5 (warm_close_dental.yaml cementado). Adding behavior hints would bloat cache prefix. |
| 3 | Should we add a separate eval rubric for "agent humility post-retract"? | **NO Slice 1.** Reinforcement golden T-inbox-retract-1.yaml asserts `required_in_correction_message_any: [disculpá, perdón, me equivoqué, lo corrijo]` via deterministic regex. Real LLM-judge MAJ-EVAL reserved for production cron weekly (per test_voice_fidelity_vitalia.py `RUN_LLM_JUDGE=1` opt-in). |
