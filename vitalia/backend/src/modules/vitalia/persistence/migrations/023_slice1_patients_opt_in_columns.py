# cap: patients.nps-tracking
# story-origin: TBD
"""Migration 023 — vitalia_patients opt-in columns (Slice 1 fidelización).

Extends existing vitalia_patients table (Story 11) with 4 marketing consent columns
required for fidelización Ola 1 re-engagement filtering.

Per .claude/rules/backend-migrations.md:
- ALTER TABLE ... ADD COLUMN IF NOT EXISTS (idempotent raw SQL)
- NEVER op.add_column() / op.create_table()
- TIMESTAMPTZ on all datetime columns

Per vitalia/.claude/rules/hipaa-lite.md:
- opt_out_at TIMESTAMPTZ (timezone-aware)
- vitalia_patients already has tenant_id + clinic_id (Story 11 migration)
"""

from __future__ import annotations

from alembic import op  # type: ignore[import]


def upgrade() -> None:
    """Extend vitalia_patients with 4 marketing consent columns + 1 index."""
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS marketing_opt_in BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out_reason TEXT NULL")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out_at TIMESTAMPTZ NULL")

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_patients_opt_in_status
          ON vitalia_patients (tenant_id, clinic_id, marketing_opt_in, opt_out)
          WHERE deleted_at IS NULL
        """
    )


def downgrade() -> None:
    """Reverse migration: drop index + columns."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_patients_opt_in_status")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS opt_out_at")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS opt_out_reason")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS opt_out")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS marketing_opt_in")
