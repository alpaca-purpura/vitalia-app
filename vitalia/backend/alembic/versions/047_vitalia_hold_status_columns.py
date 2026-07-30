# cap: scheduling.mateo-agenda
"""Migration 047 — hold-status + TTL columns on vitalia_appointment_clinic_map.

Adds 3 columns (idempotent raw SQL — IF NOT EXISTS) + 1 partial index:
  hold_status          VARCHAR(24)     — None|hold_pending_payment|confirmed|expired
  hold_expires_at      TIMESTAMPTZ     — UTC expiry of the hold
  hold_created_by_agent BOOLEAN        — True if hold created by Adrián agent

Index (partial, for sweep performance):
  ix_clinic_map_hold_expiry ON (tenant_id, hold_status, hold_expires_at)
  WHERE hold_status = 'hold_pending_payment'

Story: vitalia-fase2-adrian-canal-inbound T-BE-2.

Per .claude/rules/backend-migrations.md: raw SQL IF NOT EXISTS; NEVER op.add_column
or sa.Enum(create_type=True). Down-revision: 046_vitalia.

downstream-regression-na: brand-local vitalia migration (no cross-brand consumers).
"""

from __future__ import annotations

from alembic import op

revision = "047_vitalia"
down_revision = "046_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add hold_status, hold_expires_at, hold_created_by_agent columns + sweep index."""
    # ── 1. hold_status VARCHAR(24) nullable ─────────────────────────────────────
    op.execute("""
        ALTER TABLE vitalia_appointment_clinic_map
        ADD COLUMN IF NOT EXISTS hold_status VARCHAR(24)
    """)

    # ── 2. hold_expires_at TIMESTAMPTZ nullable ──────────────────────────────────
    op.execute("""
        ALTER TABLE vitalia_appointment_clinic_map
        ADD COLUMN IF NOT EXISTS hold_expires_at TIMESTAMPTZ
    """)

    # ── 3. hold_created_by_agent BOOLEAN NOT NULL DEFAULT FALSE ──────────────────
    op.execute("""
        ALTER TABLE vitalia_appointment_clinic_map
        ADD COLUMN IF NOT EXISTS hold_created_by_agent BOOLEAN NOT NULL DEFAULT FALSE
    """)

    # ── 4. Partial index for sweep job performance ───────────────────────────────
    # Only indexes rows where hold_status = 'hold_pending_payment' (active holds)
    # Keeps the index small and the sweep query fast.
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_clinic_map_hold_expiry
        ON vitalia_appointment_clinic_map (tenant_id, hold_status, hold_expires_at)
        WHERE hold_status = 'hold_pending_payment'
    """)


def downgrade() -> None:
    """Remove hold columns and index (idempotent via IF EXISTS)."""
    op.execute("""
        DROP INDEX IF EXISTS ix_clinic_map_hold_expiry
    """)
    op.execute("""
        ALTER TABLE vitalia_appointment_clinic_map
        DROP COLUMN IF EXISTS hold_created_by_agent
    """)
    op.execute("""
        ALTER TABLE vitalia_appointment_clinic_map
        DROP COLUMN IF EXISTS hold_expires_at
    """)
    op.execute("""
        ALTER TABLE vitalia_appointment_clinic_map
        DROP COLUMN IF EXISTS hold_status
    """)
