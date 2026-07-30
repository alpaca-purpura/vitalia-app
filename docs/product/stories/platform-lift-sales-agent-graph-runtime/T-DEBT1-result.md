# T-DEBT1-result.md — fix import stale del test de colección

**State:** tests-passing (GREEN). **Builder:** builder-agentic (workhorse-tier ticket; test-only, production_code: false). **Date:** 2026-06-22.

## Diff summary (test-only, zero production code)

`core/luana-core-sales-agent/tests/orchestrator/test_chat_orchestrator_snapshot.py` L27:

```diff
-from tests.modules.sales_agent.orchestrator._chat_flow_snapshot_helpers import (
+from tests.orchestrator._chat_flow_snapshot_helpers import (
     TENANT_ID,
     FlowCapture,
     assert_matches_snapshot,
     build_capturing_channel_adapter,
     install_chat_module_patches,
     render_snapshot,
 )
```

The helper `_chat_flow_snapshot_helpers.py` exists in the SAME dir (`core/luana-core-sales-agent/tests/orchestrator/`) and exposes `TENANT_ID`/`FlowCapture`/etc. (confirmed via `ls`). The old `tests.modules.sales_agent.orchestrator` path is pre-multibrand monolithic layout. `conftest.py` NOT touched (the synthetic `AppointmentModel` is a deliberate Story-8 stub — forbidden_to_touch).

## TDD evidence

- **RED** (before fix): `pytest --collect-only -q` → `ERROR tests/orchestrator/test_chat_orchestrator_snapshot.py` / `ModuleNotFoundError: No module named 'tests.modules'` / `Interrupted: 1 error during collection` (475 tests collected, 1 error).
- **GREEN** (after fix): `476 tests collected in 2.32s` (0 errors — the snapshot test now collects).

## Validator output (literal)

```
════════ VALIDATOR: suite_collects ════════
suite_collects EXIT=0 (0=GREEN)
```

Command (literal from 04-validators.yaml):
```
cd core/luana-core-sales-agent && ${WS}/.venv/bin/pytest --collect-only -q > /dev/null
```

`ruff_check` on the test file: `All checks passed!`

## Skills consulted

- **.claude/rules/tdd-mandatory.md** — bug fix = reproduce first (RED: collection error) → 1-line import-path fix → GREEN (clean collection). Test-housekeeping; the effect = suite collects without error, restoring the full-suite regression gate (`sales_agent_suite_canonical`, advisory in-worktree / HARD in canonical).

## Scope discipline

- Forbidden: `core/**/src/**` (T-DEBT1 is test-only), `conftest.py` (Story-8 stub). Both respected — only the 1 import line changed.
