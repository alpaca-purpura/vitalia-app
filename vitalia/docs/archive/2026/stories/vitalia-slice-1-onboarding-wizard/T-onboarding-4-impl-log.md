# T-onboarding-4 — IMPL-LOG

> Story: vitalia-slice-1-onboarding-wizard
> Ticket: T-onboarding-4 (tools wiring smoke + cost canonicalization regression)
> Builder: claude-sonnet (R23 OPT-OUT ratified Chris 2026-05-18)
> State: tests-passing
> Date: 2026-05-18

---

## R23 OPT-OUT

Per OQ-1 ratification (Chris 2026-05-18): tools + graph SHIPPED APPROVED in
`vitalia-copilot-tools-impl` story. T-onboarding-4 is wire-up verification + smoke
regression — NOT new agentic production code. Sonnet OK (~70% cost reduction vs Opus).

---

## CONTEXT-BRIEF validator status

CONTEXT-BRIEF.md `Validator pass: PENDING` (orchestrator must spawn context-validator
post-brief-return per R24). Faithfulness flag: `clean` (zero HIGH gaps). Proceeding per
caller explicit R23 OPT-OUT pass. Validator-pending noted in IMPL-LOG per §11 gap policy.

---

## Skills Consulted

| Skill | Why invoked | Decision |
|---|---|---|
| `backend-expert` | Mandatory per role instructions — load runtime quality checklist anti-patterns before commit | Read references/runtime-quality-checklist.md: confirmed no FastAPI Annotated dep needed (pure test file), no SQLA patterns, no datetime issues. Test file is standalone with local imports. |
| `brand-expert` | Invoked per role Step 0 routing (touching vitalia/copilot/ module) | Module is copilot extension, not brand-studio identity. No brand layer fields touched. No action needed. |
| `offer-expert` | Invoked per routing table check | Not touching offer module. No action needed. |
| `offer-type-preset-expert` | Invoked per routing table check | Not touching offer presets. No action needed. |
| `metrics-expert` | Invoked per routing table check | Not touching analytics. No action needed. |

Note: `tessl__fastapi`, `tessl__pytest-api-testing`, `tessl__graceful-degradation` are
listed as always-invoked in role instructions but are skill-tool calls not available in
this context. Patterns applied manually from known contracts:
- asyncio_mode=auto (no @pytest.mark.asyncio needed)
- local imports inside test functions (fast load, no circular deps)
- no external HTTP calls in this test file (pure isolation)

---

## Step 0 — Default flip detection

No flag defaults touched. No `core/luana-core-platform/config.py` edits. Step 0.5 N/A.

---

## Anti-duplication §0 grep (pre-write)

From CONTEXT-BRIEF.md § 8 (pre-sprint grep result, one-time):
- `extract_tenant_context`, `confirm_slot`, `simulate_personality`, `complete_onboarding`:
  ZERO mirrors in `core/luana-core-copilot/src/` and other brands (nicolify, comunify, lupulo).
- Tools are vitalia-specific brand extensions (Valeria onboarding).

No cross-brand mirrors. Anti-duplication §0 CLEAN.

---

## Implementation

### Scope

T-onboarding-4 scope: CREATE one test file, NO tool modifications, NO core/ edits.

### Files created

- `vitalia/backend/tests/modules/vitalia/copilot/tools/__init__.py` (empty, package marker)
- `vitalia/backend/tests/modules/vitalia/copilot/tools/test_wizard_tools_wiring.py` (46 LOC + 48 LOC docstrings = ~50 effective LOC, 6 tests)

### Files NOT touched (read-only verification)

- `vitalia/backend/src/modules/vitalia/copilot/tools/{extract_tenant_context,confirm_slot,simulate_personality,complete_onboarding}.py`
- `vitalia/backend/src/modules/vitalia/extensions.py` (lines 351-456)

### TDD cycle

1. RED: `tests/modules/vitalia/copilot/tools/` collected 0 items → confirmed RED
2. GREEN: wrote `test_wizard_tools_wiring.py` with 6 tests → 6 passed
3. REFACTOR: ruff --fix (removed unused `pytest` import + sorted imports) + ruff format → LINT+FORMAT OK

### Test descriptions (6 tests)

1. `test_4_tools_registered_via_ep3` — ExtensionPointRegistry + register_all() +
   `get_sales_agent_tool()` verifies 4 tool names registered with wizard/copilot/onboarding groups.

2. `test_extract_tenant_context_tool_signature` — `isinstance(extract_tenant_context, BaseTool)`,
   `args_schema is ExtractTenantContextInput`, `tenant_id` required field.

3. `test_confirm_slot_tool_signature` — same pattern, also verifies `slot_id` field.

4. `test_simulate_personality_tool_signature` — same pattern.

5. `test_complete_onboarding_tool_signature` — same pattern, also verifies `user_id` required.

6. `test_cost_canonicalization_regression` — `_stash(call_id, cost_value)` → `pop_cost(call_id)`
   returns `Decimal("0.00423")` (non-None) → second `pop_cost` returns None (single-use drain).
   Directly tests PI-12 S1 T-1 fix: litellm_call_id bridge stash/pop contract.

### SDK API discovery

`ExtensionPointRegistry._tool_registry` does NOT exist. Tools stored in
`registry._registrations["EP-3"]` as `_Registration` objects. Used public API
`get_sales_agent_tool(name)` instead — cleaner and forward-compatible.

### Cost recorder introspection

`_stash` is private but accessible for testing via `from ... import _stash`. The
`# noqa: PLC2701` comment suppresses private import warning (intentional for cost
canonicalization regression test).

---

## Quality gates (native)

| Gate | Status |
|---|---|
| `ruff check` (new file) | PASS 0 errors |
| `ruff format --check` (new file) | PASS |
| `pytest tests/modules/vitalia/copilot/tools/ -v` | 6/6 PASS |
| `pytest tests/modules/vitalia/copilot/ --tb=short` | 50 passed, 1 skipped |

---

## Validator pending note (R24)

CONTEXT-BRIEF.md has `Validator pass: PENDING`. Per role partial flag policy (§11 entries):
proceeding with implementation as caller explicit R23 OPT-OUT pass was provided. Gap cited here.
Orchestrator should spawn context-validator if not yet done.

---

## Cross-module reads (read-only)

- `vitalia/backend/src/modules/vitalia/extensions.py` — read lines 351-456 (EP-3 registration)
- `vitalia/backend/src/modules/vitalia/copilot/tools/*.py` — read all 4 tool files (signatures)
- `core/luana-core-extension-sdk/src/.../extension_points.py` — read to find correct public API
- `core/luana-core-observability/src/.../cost_recorder.py` — read to understand _stash/pop_cost
