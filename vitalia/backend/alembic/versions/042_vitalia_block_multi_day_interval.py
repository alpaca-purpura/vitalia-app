# cap: clinics.lisa.doctores
"""Migration 042 — delta v3 D3-F: multi-day + interval recurrence on availability blocks.

Adds 2 columns to vitalia_availability_blocks (idempotent raw SQL — IF NOT EXISTS):
  days_of_week  JSONB     — list of weekday ints [0..6] (primary D3-F field)
  "interval"    INTEGER   — recurrence interval in weeks (⚠️ quoted: SQL reserved word)

Backfill from legacy columns (one-time, idempotent WHERE days_of_week IS NULL):
  days_of_week = jsonb_build_array(day_of_week)
  "interval"   = CASE WHEN freq = 'biweekly' THEN 2 ELSE 1 END

Down-revision: 041_vitalia (re-chain lineal 8130249c — cadena 039→040→041→042→043).
Story: vitalia-fase2-lisa-doctores · T-BE-recurrencia-domain.

Per .claude/rules/backend-migrations.md: raw SQL IF NOT EXISTS; NEVER op.add_column
or sa.Enum(create_type=True). ⚠️ "interval" is a PostgreSQL reserved word — always
quoted in DDL and DML.

downstream-regression-na: brand-local vitalia migration (no cross-brand consumers).
"""

from __future__ import annotations

from alembic import op

revision = "042_vitalia"
down_revision = "041_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add days_of_week + "interval" columns + backfill from legacy fields (idempotent)."""
    # ── 1. Add days_of_week JSONB (idempotent) ─────────────────────────────────
    op.execute("""
        ALTER TABLE vitalia_availability_blocks
        ADD COLUMN IF NOT EXISTS days_of_week JSONB
    """)

    # ── 2. Add "interval" INTEGER (idempotent — quoted reserved word) ──────────
    op.execute("""
        ALTER TABLE vitalia_availability_blocks
        ADD COLUMN IF NOT EXISTS "interval" INTEGER
    """)

    # ── 3. Backfill from legacy columns (idempotent via WHERE days_of_week IS NULL)
    # Only rows not yet migrated (days_of_week IS NULL) are touched.
    # day_of_week NULLable (one_off blocks have NULL) — skip those rows.
    # freq NULLable — default interval=1 (weekly) when freq is NULL or unknown.
    op.execute("""
        UPDATE vitalia_availability_blocks
        SET
            days_of_week = jsonb_build_array(day_of_week),
            "interval" = CASE
                WHEN freq = 'biweekly' THEN 2
                ELSE 1
            END
        WHERE
            days_of_week IS NULL
            AND day_of_week IS NOT NULL
    """)


def downgrade() -> None:
    """Remove days_of_week and "interval" columns (idempotent via IF EXISTS)."""
    op.execute("""
        ALTER TABLE vitalia_availability_blocks
        DROP COLUMN IF EXISTS days_of_week
    """)
    op.execute("""
        ALTER TABLE vitalia_availability_blocks
        DROP COLUMN IF EXISTS "interval"
    """)
