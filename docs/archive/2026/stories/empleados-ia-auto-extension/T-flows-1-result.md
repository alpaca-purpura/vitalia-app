# T-flows-1 Result — Scaffold `core/luana-core-flows` + uv workspace registration

**Ticket:** T-flows-1
**Story:** `empleados-ia-auto-extension` (brand: platform)
**Surface:** backend (engine scaffold)
**Commit SHA:** `4c71af13`
**Branch:** `worktree-agent-ae93e14e203890072`
**Date:** 2026-06-02
**Authorization:** `docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md` (state: accepted, ratified Chris)

---

## Skills Consulted

| Skill | Why | Decision taken |
|---|---|---|
| `backend-expert` | Scaffold pattern for new core package; ruff gates; runtime quality checklist | Mirrored `luana-core-idempotency` pyproject structure exactly per 03-arch-be.md § 1. No legacy patterns introduced. |
| `.claude/rules/anti-duplication.md` | Confirm no existing `luana-core-flows` package (net-new check) | `grep -rn "luana-core-flows"` returned 0 matches — net-new legitimate. Factory cross-brand mirror exists in vitalia/comunify but that's T-flows-3 scope (delete). |

---

## Deliverables Status

| Deliverable | Status | Notes |
|---|---|---|
| `core/luana-core-flows/pyproject.toml` | DONE | v0.1.0, `langgraph-checkpoint-postgres>=3.1.0,<4`, mirror idempotency structure |
| `core/luana-core-flows/src/luana_core_flows/__init__.py` | DONE | Public API skeleton with `# cap: __shared__` header |
| `core/luana-core-flows/tests/conftest.py` | DONE | Mirrors `luana-core-idempotency/tests/conftest.py` |
| Root `pyproject.toml` — member (alphabetical) | DONE | Inserted between `luana-core-extraction` and `luana-core-iam` (verified sort order) |
| Root `pyproject.toml` — `[tool.uv.sources]` entry | DONE | `luana-core-flows = { workspace = true }` added under "durable-flows-engine proposal" comment |
| `uv sync` → `uv.lock` updated, no langgraph bump | DONE | `langgraph` stays 1.2.0, `langgraph-checkpoint` stays 4.1.0, `langgraph-checkpoint-postgres` resolves to 3.1.0 |
| Arch test `_EXPECTED_COUNT` 27→28 + docstring | DONE | `test_workspace_members_alphabetical_story8.py` updated with new count + rationale comment |
| `.release-please-manifest.json` | DONE | Added `core/luana-core-flows: 0.1.0` entry (required by `test_release_please_manifest_all_at_0_1_0`) |

---

## Anti-dup Scan (ESCANEO ANTI-DUP)

```bash
grep -rn "luana-core-flows" ${WS}/core/ ${WS}/vitalia/ ${WS}/comunify/
# Result: 0 matches (net-new confirmed)
```

No existing `luana-core-flows` package existed before this ticket. Confirmed via grep. The factory brand-mirror (`vitalia/wizard_checkpoint_config.py::build_production_checkpointer` + comunify inline equivalents) is in scope for T-flows-3 (delete step) — NOT touched in T-flows-1.

---

## Validators Output (T-flows-1 scope)

### `v_lint_flows_pkg` — PASS
```
ruff check src/ tests/ → All checks passed!
ruff format --check src/ tests/ → 2 files already formatted
```

### `v_workspace_members` — PASS
```
pytest core/tests/architecture/test_workspace_members_alphabetical_story8.py -x -q
4 passed in 0.16s
  - test_python_member_count_is_27 PASS (now checks for 28)
  - test_python_members_alphabetical PASS
  - test_story8_new_members_present PASS
  - test_ts_package_count_is_7 PASS
```

### `v_uv_sync_resolves` — PARTIAL (scaffold portion PASS; checkpointer portion deferred T-flows-2)
- `uv sync` completed cleanly: `langgraph-checkpoint-postgres 3.1.0` + transitives (psycopg, psycopg-pool, orjson) resolved against locked `langgraph 1.2.0` / `langgraph-checkpoint 4.1.0`
- `import luana_core_flows` → OK
- `from luana_core_flows.checkpointer import make_durable_checkpointer, build_flow_thread_id` → NOT YET (T-flows-2 deliverable — checkpointer/ module created by `builder-agentic`)

### Pre-existing failure (NOT introduced by T-flows-1)
```
test_workspace_versions_uniform_at_v0_1_0::test_all_typescript_packages_at_0_1_0
FAIL: ui-kit 0.2.0 (expected 0.1.0)
```
Cause: `core/@luana/ui-kit` was bumped to `0.2.0` in commit `bf86031c` (before this agent session). Zero diff on that file from T-flows-1.

---

## uv.lock — Diff Summary (langgraph section)

| Package | Before | After | Status |
|---|---|---|---|
| `langgraph` | `1.2.0` | `1.2.0` | UNCHANGED |
| `langgraph-checkpoint` | `4.1.0` | `4.1.0` | UNCHANGED |
| `langgraph-checkpoint-postgres` | ABSENT | `3.1.0` | ADDED (expected) |
| `psycopg` | — | added (transitive) | OK |
| `psycopg-pool` | — | added (transitive) | OK |
| `orjson` | — | added (transitive) | OK |

No version bumps — as predicted by 03-arch.md § L1.5.

---

## Files Changed

| File | Change |
|---|---|
| `core/luana-core-flows/pyproject.toml` | NEW |
| `core/luana-core-flows/src/luana_core_flows/__init__.py` | NEW |
| `core/luana-core-flows/tests/conftest.py` | NEW |
| `pyproject.toml` | MODIFIED (+member +source) |
| `uv.lock` | MODIFIED (+langgraph-checkpoint-postgres + transitives) |
| `core/tests/architecture/test_workspace_members_alphabetical_story8.py` | MODIFIED (_EXPECTED_COUNT 27→28) |
| `.release-please-manifest.json` | MODIFIED (+core/luana-core-flows@0.1.0) |

**Total files: 7 (3 new, 4 modified)**

---

## Scope Guardrail Compliance

- frontend/ NOT touched: PASS
- nicolify/ NOT touched: PASS
- lupulo/ NOT touched: PASS
- `core/luana-core-flows/src/luana_core_flows/domain/` NOT created (L2 deferred): PASS
- No provider implementation (T-flows-2 scope): PASS

---

## Next Ticket

**T-flows-2** (`make_durable_checkpointer` provider + `build_flow_thread_id`): requires `builder-agentic` (Opus, R23). Depends on this ticket (T-flows-1). Artifacts: `core/luana-core-flows/src/luana_core_flows/checkpointer/{provider.py, thread_id.py, __init__.py}`.
