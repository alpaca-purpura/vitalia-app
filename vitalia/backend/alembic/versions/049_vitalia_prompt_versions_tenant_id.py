# cap: adrian.inbox
"""Migration 049 — prompt_versions.tenant_id (ESC-6 brand-authored, sales_agent engine lift).

Adopts the hardened engine `core/luana-core-sales-agent` (proposal
2026-06-22-sales-agent-multibrand-graph-runtime, merged ff0b9345). The engine model
`PromptVersion` now carries `tenant_id` (NULL = system default); the graph in HYBRID/DB
mode loads prompts per tenant. `prompt_versions` is not created by any prior vitalia
migration, so this CREATEs the table (idempotent) in addition to the column.

Backfill: no-op — existing rows are system defaults → tenant_id stays NULL, the exact
semantics of the fallback in engine base.py (`PromptVersion.tenant_id.is_(None)`).

Per backend-migrations.md: raw SQL IF NOT EXISTS (idempotent). gen_random_uuid() needs
pgcrypto, enabled in migration 035.
DDL SSoT: docs/product/stories/platform-lift-sales-agent-graph-runtime/migration_notes.md
"""

from alembic import op

revision = "049_vitalia"
down_revision = "048_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Engine sales_agent table — create if missing (idempotent).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key           VARCHAR NOT NULL,
            version       INTEGER NOT NULL,
            content       TEXT NOT NULL,
            is_active     BOOLEAN DEFAULT TRUE,
            change_reason VARCHAR,
            author_id     VARCHAR,
            metadata_info JSONB DEFAULT '{}'::jsonb,
            tenant_id     UUID,
            created_at    TIMESTAMPTZ DEFAULT now()
        );
        """
    )
    # 2. ESC-6 column — for DBs where the table already existed without tenant_id (idempotent).
    op.execute("ALTER TABLE prompt_versions ADD COLUMN IF NOT EXISTS tenant_id UUID")
    # 3. Indexes (idempotent).
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompt_versions_key ON prompt_versions (key)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompt_versions_tenant_id ON prompt_versions (tenant_id)")


def downgrade() -> None:
    # Conservative: drop only the ESC-6 column (not the table — may hold seeded defaults).
    op.execute("DROP INDEX IF EXISTS ix_prompt_versions_tenant_id")
    op.execute("ALTER TABLE prompt_versions DROP COLUMN IF EXISTS tenant_id")
