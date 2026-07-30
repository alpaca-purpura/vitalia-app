# T-ag-workflows-1 — Result

> **Brand:** vitalia
> **Ticket:** T-ag-workflows-1 (Wave 4, R23 Opus 4.7 production_code=true)
> **Story:** vitalia-copilot-tools-impl
> **State:** developed → AWAIT_AUDIT (auto-handoff `/auditor` per story-closure-gate)

## Summary

Valeria wizard onboarding LangGraph supervisor topology + deepagents
`extract_subagent` sandbox + checkpointer abstraction + 5-slot prompt cache
compiler. Brand-extension only — engine `core/luana-core-*/` READ-ONLY.

## Surface delivered

NEW (8 files, 1015 LOC source + 555 LOC tests):

- `vitalia/backend/src/modules/vitalia/copilot/workflows/wizard_onboarding_state.py`
  — `WizardOnboardingState` TypedDict + helpers (`required_all_confirmed`,
  `has_pending_extraction`, `build_initial_state`) + cement constants
  (`REQUIRED_SLOT_IDS`, `OPTIONAL_SLOT_IDS`, `MAX_ITERATIONS=25`)
- `vitalia/backend/src/modules/vitalia/copilot/workflows/wizard_prompt_compiler.py`
  — 5-slot prompt compiler (system role + wizard role MD + tools manifest +
  Valeria persona MD + variable session state). `cache_breakpoint_index=3`.
  `as_anthropic_system_blocks()` helper with `cache_control` marker on last
  cacheable slot only.
- `vitalia/backend/src/modules/vitalia/copilot/workflows/extract_subagent.py`
  — `build_extract_subagent_spec()` returning deepagents `SubAgent` TypedDict
  with explicit `tools=[3]` sandbox. `EXTRACT_SUBAGENT_NAME` constant.
- `vitalia/backend/src/modules/vitalia/copilot/workflows/extract_subagent_tools.py`
  — 3 LangChain `@tool` sandbox callables: `scrape_website_tool` +
  `parse_document_tool` + `transcribe_audio_tool`. `EXTRACT_SUBAGENT_TOOLS`
  tuple. Placeholder bodies (production swap = adapter wiring via
  `ExtractTenantContextService` already in T-be-services-1).
- `vitalia/backend/src/modules/vitalia/copilot/workflows/wizard_checkpoint_config.py`
  — `CheckpointerProtocol` structural type + `build_production_checkpointer()`
  deferred-import factory (AsyncPostgresSaver swap surface, package install
  pending per D10 pattern). `WIZARD_CHECKPOINT_TABLE_PREFIX` constant.
- `vitalia/backend/src/modules/vitalia/copilot/workflows/wizard_onboarding_graph.py`
  — LangGraph `StateGraph` factory `build_wizard_onboarding_graph()`. Nodes:
  supervisor + extract_subagent + slot_question_router + live_preview_router
  + completion_router. Pure router `decide_next_node()` (max-iter guard +
  task_complete + extraction-pending + mode-unset + slots-confirmed-complete
  branches). Defense-in-depth: max-iter cap enforced at conditional edge AND
  inside supervisor node.
- `vitalia/backend/src/modules/vitalia/copilot/application/services/wizard_orchestrator_service.py`
  — `WizardOrchestratorService` composition root. `start_wizard()` +
  `stream_wizard()` (async generator over `astream_events` v2 — SSE v2 spec
  per copilot-expert). Thread_id composes (tenant_id, draft_id) for
  multitenant isolation.

MODIFIED (2 files):

- `vitalia/backend/src/modules/vitalia/copilot/workflows/__init__.py` — wire
  Wave 4 surface; preserves Wave 2 (`TreatmentFollowupState` +
  `build_treatment_followup_workflow` + cron handler) unchanged.
- `vitalia/backend/src/modules/vitalia/extensions.py` — add EP-4
  registration `vitalia.wizard_onboarding_supervisor` (`WorkflowDef`, steps
  empty per SDK contract — graph factory is the surface).

Tests (3 files, 555 LOC, 34 cases — all GREEN):

- `vitalia/backend/tests/unit/modules/vitalia/copilot/workflows/test_wizard_onboarding_state.py`
  — 9 cases: shape/tenant-isolation/iterations/slot-machinery/subagent-bridge/
  completion-error/helper-required-all-confirmed/initial-state-factory.
- `vitalia/backend/tests/unit/modules/vitalia/copilot/workflows/test_wizard_prompt_compiler.py`
  — 9 cases: byte-stable slots 0-3 across calls / slot 4 isolated / no
  timestamps / no UUIDs / no `conversation_id` / slot 1 loads
  wizard_role_vitalia.md / slot 3 loads valeria_persona.md /
  `cache_breakpoint_index == 3` / cache_control marker on slot 3 only.
- `vitalia/backend/tests/unit/modules/vitalia/copilot/workflows/test_extract_subagent.py`
  — 8 cases: explicit tools list / brand namespace name / system_prompt from
  extractor_subagent.md / sandbox tool names only (parent leak forbidden) /
  scrape returns dict / parse returns sections / transcribe rejects >60s /
  name constant.
- `vitalia/backend/tests/integration/modules/vitalia/copilot/workflows/test_wizard_onboarding_graph.py`
  — 8 cases: graph compiles / max-iter cap → END / task_complete short-circuit /
  extract branch on subagent input present / completion when required slots
  confirmed / state persists across invocations / tenant_id carried in result /
  subagent isolation no parent state leak.

## Acceptance — validator results

| Validator | Result |
|---|---|
| `be_lint_ruff_check` | PASS (all checks passed — touched files) |
| `be_format_ruff` | PASS (365 files already formatted) |
| `be_arch_fitness_brand_scoped` | PASS (245 / 245) |
| `be_test_integration_wizard_graph` | **PASS (★ critical, 8 / 8)** |
| `ae_cache_hit_rate_smoke` | PASS (4 / 4) |
| `ae_cost_budget_smoke` | PASS (25 / 25) |
| `anti_duplication_cross_module_audit` | PASS (no engine-base mirrors w/o import) |
| `cross_brand_mirror_scan` | PASS (no nicolify/comunify/lupulo mirrors) |
| `engine_boundary_no_modification_audit` | PASS (no `core/luana-core-*/src/` diff) |

Broader smoke:

- Full copilot unit suite: 154 / 154 PASS
- Wizard workflows: 34 / 34 PASS

Pre-existing failures (NOT caused by this ticket — parallel builder T-ag-tools-2):

- `test_extensions.py::test_ep3_sales_agent_tools_count_four_post_t_infra_2`
  — failed before T-ag-workflows-1 began (T-ag-tools-2 added real handlers
  for EP-3 tools; expected-count assertion no longer matches).
- `test_extensions.py::test_ep3_tool_handlers_are_placeholders_raising_not_implemented`
  — same cause; T-ag-tools-2 real handlers are not the placeholder
  `_not_implemented_yet` callables.

Both pre-date my changes. Confirmed via `git log -5 -- test_extensions.py`
(last touched at story `f6e41be` story-11 / 50143d5 squash — pre-Wave 4) +
`git log -5 -- extensions.py` (T-ag-tools-2 commit `6814452` last modified).

## Design decisions

1. **CheckpointerProtocol** — production wires `AsyncPostgresSaver` from
   `langgraph-checkpoint-postgres` (engine-recommended per tessl__langgraph).
   Package install is deferred (same D10 pattern as `RedisSaver` in
   T-workflow-1). `build_production_checkpointer()` factory deferred-imports
   the package; tests use `InMemorySaver` directly. Composition root chooses
   at FastAPI lifespan — 1-line swap when package lands.

2. **5-slot vs 6-slot architecture** — wizard uses 5-slot (engine system +
   wizard role + tools manifest + Valeria persona + variable session state)
   per 03-arch-agentic.md § 5.2. Slots 0-3 cacheable; slot 4 variable. Only
   slot 3 carries `cache_control` ephemeral marker (Anthropic forms cache
   from marker backwards — single marker caches contiguous slots 0-3).
   Adrián 6-slot (sales_agent) is independent; this compiler is brand-extension
   wizard-only.

3. **deepagents `SubAgentMiddleware` API** — the design spec mentioned
   `allowed_keys_to_subagent` / `allowed_keys_from_subagent` constructor args;
   the installed `deepagents` package (version present in workspace `.venv`)
   takes `backend` + `subagents` only. Isolation is enforced by the SubAgent
   spec's explicit `tools=[...]` sandbox (parent toolset NOT inherited per F2
   copilot-expert pattern) + by the supervisor node consuming only
   `extraction_subagent_input` and writing only `extraction_subagent_output`
   (state-level isolation contract). The 3 sandbox tools never touch parent
   state (they take primitive args + return structured dicts).
   `build_extract_subagent_spec()` returns the `SubAgent` TypedDict ready to
   pass into `SubAgentMiddleware(backend=..., subagents=[spec])` at composition
   root.

4. **Slice 1 stub nodes** — the supervisor, slot_question, live_preview,
   completion nodes are deterministic Python routers; the actual LLM
   supervisor binding (which would invoke the 4 wizard tools per
   `decide_next_node`'s decisions) happens at composition root via
   `create_deep_agent(supervisor_model=..., tools=[...], subagents=[...])`.
   This Slice 1 graph is the **topology surface** + state-machine contract —
   sufficient for the integration test (state persistence, max-iter,
   routing semantics) but not yet wired to a real LLM. Production LLM
   binding lands at FastAPI lifespan startup via the orchestrator service.

5. **Anti-duplication compliance** — no `BaseObservabilityContext` /
   `BaseAgentCallbackHandler` / `FXResolver` / `PricingSnapshot` /
   `TenantBillingConfig` / `BaseExtractionOrchestrator` defined in this
   ticket's files (cross-module audit script GREEN). Wizard state + graph +
   compiler are brand-specific (no engine equivalent exists for per-tenant
   onboarding wizard). If a second brand requires the same surface, lift to
   `core/luana-core-copilot/` per `/pm-luana` promotion proposal —
   documented in module docstrings.

## Skills Consulted (R-23 mandatory)

- `copilot-expert` — confirmed F0-F11 topology constraints, supervisor +
  AsyncPostgresSaver patterns, sub-agent tools-explicit cardinal (F2), cache
  slot architecture, anti-duplication §0 (no mirror of engine recording /
  cost / pricing classes), 5-slot Valeria layout per arch § 5.2.
- `sales-agent-expert` — confirmed §3 NO-toca (Adrián consumes engine
  directly — wizard does NOT depend on sales_agent surface). Anti-duplication
  §0 reinforced (callback handlers + turn envelopes subclass from
  `luana_core_observability`).
- `tessl__langgraph` (via session knowledge — package not separately invoked;
  pattern reference embedded in copilot-expert) — `StateGraph` + conditional
  edges total + `AsyncPostgresSaver` (deferred import per package
  unavailability) + reducer (`add_messages`, `operator.add`) for parallel-safe
  state mutations + 6 stream modes via `astream_events`.
- `tessl__deepagents` (via session knowledge) — `SubAgent` TypedDict shape +
  explicit `tools=[...]` sandbox (no parent inherit) + `SubAgentMiddleware`
  backend/subagents constructor signature confirmed by introspecting
  `.venv/lib/python3.12/site-packages/deepagents/middleware/subagents.py`.
- `claude-api` (via session knowledge) — cache prefix invariance contract
  (slots 0-3 byte-stable, no timestamps / UUIDs / conversation_id) + single
  `cache_control` marker on last cacheable block + 5min TTL default for
  wizard active session.

## Tenant + HIPAA-lite compliance

- `tenant_id` cardinal in `WizardOnboardingState` (REQUIRED + verified in
  state schema test + integration test).
- `clinic_id` slot declared optional (may not exist yet — onboarding creates
  it). Wizard does NOT touch PHI (clinic config only — per Valeria persona
  rule § 4).
- Thread_id composes `(tenant_id, draft_id)` for checkpointer isolation
  across multitenant traffic.
- No PHI processing in extract_subagent (subagent system prompt
  `extractor_subagent.md` § Reglas § PHI detection enforces).

## Commit + push

- Commit SHA: d7683db
- Branch: `wip/vitalia`
- Conventional Commits: `feat(vitalia/copilot/workflows): T-ag-workflows-1 …`
- Co-authored: `Claude Opus 4.7 (1M context)`

## Next phase

Per story-closure-gate auto-handoff: `/auditor` reviews this build phase
(state=developed → reviewing). Builder phase output is `tests-passing`
per R30; verdict is auditor's independent contract.

## Test summary

`workflows_unit=26/26 workflows_integration=8/8 cache_smoke=4/4 cost_budget_smoke=25/25 arch_fitness=245/245 full_copilot_unit=154/154`
