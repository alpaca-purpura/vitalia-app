# T-ESC6-result.md — prompt_versions.tenant_id (modelo) + migration_notes brand-authored

**State:** tests-passing (GREEN). **Builder:** builder-agentic (flagship). **Date:** 2026-06-22.

## Diff summary (production code)

`core/luana-core-sales-agent/src/luana_core_sales_agent/infrastructure/models/prompt_version_model.py` (after `metadata_info`):

```diff
     metadata_info = Column(JSONB, default=dict)  # target_node, target_model, etc.

+    # Tenant scoping (ESC-6): NULL = system default (fallback path in PromptLoader._get_from_db).
+    # No FK to tenants (engine model stays decoupled from platform tenants table — matches MessageModel).
+    tenant_id = Column(UUID(as_uuid=True), nullable=True, index=True)
+
     created_at = Column(DateTime(timezone=True), server_default=func.now())
```

`UUID` already imported (`from sqlalchemy.dialects.postgresql import JSONB, UUID`). No FK to `tenants` — engine persistence model stays decoupled (hexagonal; matches `MessageModel.tenant_id` pattern).

## Migration validation (NOT authored — brand-authored)

Per constraint "cero marca en worktree core" + no alembic in `core/`, NO migration authored here. Validated `migration_notes.md` DDL vs final model:

| Final model column | migration_notes.md `CREATE TABLE` |
|---|---|
| `id UUID PK default uuid4` | `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` ✓ |
| `key String` | `key VARCHAR NOT NULL` ✓ |
| `version Integer` | `version INTEGER NOT NULL` ✓ |
| `content Text` | `content TEXT NOT NULL` ✓ |
| `is_active Boolean default True` | `is_active BOOLEAN DEFAULT TRUE` ✓ |
| `change_reason String` | `change_reason VARCHAR` ✓ |
| `author_id String` | `author_id VARCHAR` ✓ |
| `metadata_info JSONB` | `metadata_info JSONB DEFAULT '{}'::jsonb` ✓ |
| `tenant_id UUID nullable index` | `tenant_id UUID` + `ADD COLUMN IF NOT EXISTS tenant_id UUID` + `CREATE INDEX IF NOT EXISTS ix_prompt_versions_tenant_id` ✓ |
| `created_at DateTime(tz) server_default now()` | `created_at TIMESTAMPTZ DEFAULT now()` ✓ |

DDL is idempotent (`CREATE TABLE IF NOT EXISTS` + `ADD COLUMN IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`), raw SQL (no `op.create_table()`/`sa.Enum(create_type=True)`), backfill no-op (NULL = system default). **migration_notes.md DDL matches the final model.** No edit to migration_notes needed.

## Test created (TDD)

- `core/luana-core-sales-agent/tests/architecture/test_esc6_prompt_version_tenant_id.py` (NEW — from `verified-arch-tests.md`; ruff-reformatted to satisfy 120-char line limit, logic identical).

## TDD evidence

- **RED** (test created before diff): `AttributeError: type object 'PromptVersion' has no attribute 'tenant_id'` — matches architect spike + live error. 2 failed.
- **GREEN** (after diff): column present + both query branches (specific-override `== tid`, system-default `IS NULL`) build without error. 2 passed.

## Validator output (literal)

```
════════ VALIDATOR: esc6_prompt_version_tenant_id ════════
core/luana-core-sales-agent/tests/architecture/test_esc6_prompt_version_tenant_id.py::test_prompt_version_has_tenant_id_column PASSED [ 50%]
core/luana-core-sales-agent/tests/architecture/test_esc6_prompt_version_tenant_id.py::test_prompt_load_query_branches_build PASSED [100%]
======================== 2 passed, 9 warnings in 2.40s =========================
```

Command (literal from 04-validators.yaml):
```
PYTHONPATH=${WS}/core/luana-core-sales-agent/src:${WS}/core/luana-core-platform/src \
  ${WS}/.venv/bin/pytest core/luana-core-sales-agent/tests/architecture/test_esc6_prompt_version_tenant_id.py -v -p no:cacheprovider --override-ini='addopts='
```

`ruff_check`: `All checks passed!` · `ruff_format` on prompt_version_model.py: `already formatted`.

## Skills consulted

- **sales-agent-expert** — ★ §3 "NO se toca" lists `PromptVersionModel` as protected: "Sales necesita override DB-backed per tenant." This ESC ADDS exactly that capability (tenant scoping the override path needs), additively (one nullable column, no FK, no removal). This is the sanctioned engine lift (promotion proposal accepted) that makes the §3-protected per-tenant override actually work — `base.py:90,109` already filter `PromptVersion.tenant_id` but the column was missing. Decided: add column as specified; no behavior change to the loader, only making its existing query branches resolvable.
- **backend-expert** (via guidelines) — engine persistence model `tenant_id` WITHOUT FK to `tenants` (decouple from platform schema; matches `MessageModel.tenant_id`). `index=True` for the tenant-scoped lookup.
- **.claude/rules/tdd-mandatory.md** — RED (AttributeError) before GREEN.
- **.claude/rules/backend-migrations.md** — validated migration_notes.md DDL is idempotent (`IF NOT EXISTS`/`ADD COLUMN IF NOT EXISTS`), raw SQL, no `op.create_table()`/`sa.Enum(create_type=True)`. Migration is brand-authored (each brand in its own alembic), not authored here.

## Tenant isolation note

ESC-6 ADDS tenant-awareness to prompts (specific override `tenant_id == tid` + system-default `tenant_id IS NULL`). Reinforces tenant isolation per `.claude/rules/tenant-isolation.md`.
