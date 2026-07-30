---
story_id: empleados-ia-auto-extension
surface: backend (package scaffold + uv workspace + migrations)
builder: builder-backend (Sonnet)
auditor: auditor-backend (Opus)
authorization: docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md (accepted)
parent: 03-arch.md
---

# 03-arch-be — Package scaffold + uv workspace + checkpoint migrations (L1)

> Read `03-arch.md` (consolidated) first. This is the backend-surface slice (non-agentic plumbing). The provider/graph LOGIC is `builder-agentic` (see 03-arch-agentic.md).

## 1. New package scaffold (`core/luana-core-flows`)

Mirror `core/luana-core-idempotency` exactly:

```
core/luana-core-flows/
├── pyproject.toml
├── src/luana_core_flows/__init__.py        # public exports (builder-agentic fills checkpointer/)
└── tests/conftest.py
```

`pyproject.toml`:
```toml
[project]
name = "luana-core-flows"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "langgraph",
    "langgraph-checkpoint-postgres>=3.1.0,<4",
    "pydantic>=2.0",
    "structlog>=24.0",
    "luana-core-platform",
]
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_flows"]
```

## 2. uv workspace registration (root pyproject.toml)

- Add `"core/luana-core-flows"` to `[tool.uv.workspace] members` in **strict alphabetical position**. Order check: `luana-core-extraction` < `luana-core-flows` < `luana-core-iam` → insert between `-extraction` and `-iam` (after line for extraction, before iam). Verify against the actual file order (extension-sdk, extraction, iam...). `flows` sorts after `extraction` and after `extension-sdk`, before `iam`.
- Add `luana-core-flows = { workspace = true }` to `[tool.uv.sources]`.
- Run `cd ${WS} && uv sync` (from ROOT — never inside a brand backend) → resolves `langgraph-checkpoint-postgres` + transitives (psycopg, psycopg-pool, orjson; pycryptodome if encryption path needs it) against the ALREADY-locked langgraph 1.2.0 / langgraph-checkpoint 4.1.0. **No version bump expected** (§ L1.5). Commit `uv.lock`.

## 3. Brand backend deps

- `vitalia/backend/pyproject.toml` + `comunify/backend/pyproject.toml`: add `luana-core-flows` to dependencies (the brands consume the provider at their composition roots). Do NOT add `langgraph-checkpoint-postgres` to copilot/sales-agent ENGINE pkgs (they don't construct checkpointers in L1).

## 4. Migrations (idempotent raw SQL)

Decision (hybrid — § L1.6): LangGraph `AsyncPostgresSaver.setup()` OWNS the checkpoint table DDL (called once at lifespan startup). The alembic migration is a THIN prerequisite + namespace record — it does NOT `CREATE TABLE` the checkpoint internals (avoids schema drift with LangGraph's owned schema across versions).

`vitalia/backend/alembic/versions/037_vitalia_durable_flow_checkpoints.py` (next after 036):
```python
"""Durable flow checkpoint namespace (vitalia). LangGraph AsyncPostgresSaver.setup() owns the table DDL."""
def upgrade():
    # Prerequisite only — checkpoint tables (prefix 'vitalia_flows_' / LangGraph default) are
    # created idempotently by AsyncPostgresSaver.setup() at app lifespan startup.
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")  # harmless if unused; supports any column-level PHI need
    # NO op.create_table for checkpoint internals.
def downgrade():
    pass  # checkpoint tables are LangGraph-owned; no destructive downgrade
```

`comunify/backend/alembic/versions/002_comunify_durable_flow_checkpoints.py` (next after 001): same pattern, no `pgcrypto` needed (comunify non-PHI) — or include it harmlessly; builder decides.

- **PROHIBITED:** `op.create_table()`, `sa.Enum(create_type=True)`, non-idempotent DDL.
- **Prod-clone test (per backend-migrations.md + O-2):**
  ```bash
  createdb migration_test
  pg_dump --schema-only $PROD_DB | psql migration_test
  ${WS}/.venv/bin/alembic -c vitalia/backend/alembic.ini upgrade head    # then comunify alembic.ini
  dropdb migration_test
  ```
  Plus a one-shot to confirm `AsyncPostgresSaver.setup()` is idempotent (run twice, no error) on a clean DB — confirms the LangGraph-owned-tables approach (O-2).

## 5. Arch fitness updates

- `core/tests/architecture/test_workspace_members_alphabetical_story8.py`: bump `_EXPECTED_COUNT = 27 → 28` + update the docstring rationale ("+1 luana-core-flows, durable-flows-engine proposal 2026-06-02"). This is the standard "+1 core package" allowlist ratchet (justified in commit body). The alphabetical-order test passes automatically once the member is inserted in the correct position.
- `core/tests/architecture/test_workspace_versions_uniform_at_v0_1_0.py`: new pkg at `0.1.0` keeps it green.
- Brand arch suites must stay green (no new cross-module import; provider imported from `core/` is allowed).

## 6. Tests (TDD)
- Package import smoke: `from luana_core_flows.checkpointer import make_durable_checkpointer, build_flow_thread_id` resolves post `uv sync`.
- Migration idempotency: re-run `alembic upgrade head` twice → no error (prod-clone).
- Workspace integrity: member count + alphabetical (arch test, bumped).
