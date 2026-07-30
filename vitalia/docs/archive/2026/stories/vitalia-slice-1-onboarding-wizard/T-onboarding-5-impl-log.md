# T-onboarding-5 Implementation Log

> Story: vitalia-slice-1-onboarding-wizard
> Ticket: T-onboarding-5 — Wizard graph e2e integration regression
> Surface: backend (integration tests only)
> R23 OPT-OUT: Sonnet OK (`production_code=false`, ratified Chris 2026-05-18)
> Depends-on: T-onboarding-4 (DONE 615a252 — tools wiring smoke)

## § Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` (runtime-quality-checklist) | ALWAYS-required per impl flow | Verified: Pydantic v2 ConfigDict, response_model=, tenant_id in every state, async/sync patterns |
| `tessl__pytest-api-testing` | Integration test fixture scoping + factory patterns | Used function-scoped fixtures; InMemorySaver as drop-in for AsyncPostgresSaver |
| `tessl__fastapi` | Confirm no new routes or production code added | N/A — test-only ticket, no FastAPI surfaces modified |

Note: `CONTEXT-BRIEF.md` header shows `Validator pass: PENDING` (Haiku cannot spawn sub-agents). Proceeding per caller's explicit override in prompt (R23 OPT-OUT ratification inline + all context provided).

## § Scope

**Files created (tests only — no production code):**
- `vitalia/backend/tests/integration/copilot/__init__.py` — empty init (new directory)
- `vitalia/backend/tests/integration/copilot/test_wizard_onboarding_graph_e2e.py` — 5 integration regression tests

**Files NOT modified (read-only constraint):**
- `wizard_onboarding_graph.py` — SHIPPED APPROVED
- `wizard_onboarding_state.py` — SHIPPED APPROVED
- `wizard_prompt_compiler.py` — SHIPPED APPROVED
- `wizard_checkpoint_config.py` — SHIPPED APPROVED

## § Implementation Notes

### Key finding: compiler API mismatch
`wizard_prompt_compiler.py` exports `compile_wizard_prompt(*, session_state_summary: str) -> CompiledWizardPrompt` (function API), not a `WizardPromptCompiler` class as initially drafted. Fixed test 3 to use the actual function + `CompiledWizardPrompt` dataclass.

### Test 1 — Happy path
Seeds all 3 `REQUIRED_SLOT_IDS` (`tenant.name`, `tenant.vertical`, `tenant.location`) confirmed with `mode="guiado"`. Asserts: `task_complete=True`, `iterations > 0`, `iterations ≤ 25`, `tenant_id` preserved.

### Test 2 — Max-iter guard
Seeds `iterations=26` (`> MAX_ITERATIONS=25`). Asserts: graph terminates (`task_complete=True` OR `iterations >= 25`). Cements `MAX_ITERATIONS == 25`. Verifies `last_error.kind == "max_iter_exceeded"` if node-level guard fired.

### Test 3 — Cache hit rate
Uses actual `compile_wizard_prompt()` twice with different `session_state_summary` values. Asserts `slots[:4]` (invariant cache prefix) are byte-identical across calls while `slot[4]` (variable) differs. Synthetic token model proves `cache_read_input_tokens > 0` on turn 2+.

### Test 4 — Cost target
Deterministic model: 10-turn worst-case session with `claude-sonnet-4-5` pricing. Turn 1 writes cache prefix (850 tokens at cache_write rate); Turns 2-10 read it (0.30/M). Total ≤ $0.10 USD. No live LLM required.

### Test 5 — Checkpointer resume
`InMemorySaver` (same `CheckpointerProtocol` as `AsyncPostgresSaver`). Two-invoke pattern: Turn 1 with `mode=None`, verify `graph.get_state()` snapshot preserved; Turn 2 with all required slots → `task_complete=True`, `iterations > iterations_after_t1`.

## § HIPAA-lite Compliance
- No PHI in any fixture: clinic names (`Clínica Salud Total`, `Clínica Dental Lima`), verticals (`dental`), locations (`Lima, Perú`) are brand configuration — NOT medical records or patient identifiers per `vitalia/.claude/rules/hipaa-lite.md`
- `tenant_id` and `draft_id` are synthetic UUIDs
- No real patient data anywhere in tests

## § Anti-duplication
- No new production patterns introduced — tests only
- `compile_wizard_prompt` imported read-only (not re-implemented)
- `InMemorySaver` from `langgraph.checkpoint.memory` (engine library, not re-implemented)

## § Default-flip pre-audit
Not applicable — no feature flags modified.

## § Gate results

| Suite | Result |
|---|---|
| `test_wizard_onboarding_graph_e2e.py` (5 tests) | 5 PASS ✓ |
| `test_wizard_pass_k_evaluation.py` (10 tests) | 10 PASS ✓ |
| Broader `integration/ + agentic_evals/` (566+32) | 566 passed, 32 skipped ✓ |
| `ruff check` | 0 errors ✓ |
| `ruff format --check` | 0 files to reformat ✓ |
