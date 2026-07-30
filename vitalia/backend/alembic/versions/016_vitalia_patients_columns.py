"""Vitalia patients columns — marketing consent and opt-out tracking (PHI-related).

Adds 4 columns to the vitalia_patients table for marketing consent management
per LatAm data protection laws (Ley 25.326 AR, LGPD BR, Ley 1581 CO,
Ley 19.628 CL, Ley 29733 PE):

  marketing_opt_in   BOOLEAN NOT NULL DEFAULT FALSE
  opt_out            BOOLEAN NOT NULL DEFAULT FALSE
  opt_out_reason     TEXT NULL
  opt_out_at         TIMESTAMPTZ NULL

Note: vitalia_patients table is assumed to exist (created by a prior
migration or Story 11 equivalent). Uses ADD COLUMN IF NOT EXISTS.

opt_out_at is indexed for GDPR/LatAm right-to-erasure sweep queries.

All DDL idempotent via ADD COLUMN IF NOT EXISTS.

Revision ID: 016_vitalia
Revises: 015_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "016_vitalia"
down_revision = "015_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add marketing consent columns to vitalia_patients idempotent."""

    # Create vitalia_patients table IF NOT EXISTS (guard for fresh environments)
    # In prod, this table was created in Story 11. IF NOT EXISTS ensures
    # idempotency when running on fresh DB.
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_patients (
            id              UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            clinic_id       UUID        NOT NULL,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_patients PRIMARY KEY (id)
        );
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_patients_tenant_clinic ON vitalia_patients (tenant_id, clinic_id);"
    )

    # Marketing consent fields
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS marketing_opt_in BOOLEAN NOT NULL DEFAULT FALSE;")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out BOOLEAN NOT NULL DEFAULT FALSE;")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out_reason TEXT;")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS opt_out_at TIMESTAMPTZ;")

    # Index for erasure sweep queries (right-to-erasure regulatory requirement)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_patients_opt_out"
        " ON vitalia_patients (tenant_id, clinic_id, opt_out_at)"
        " WHERE opt_out = TRUE;"
    )

    # Index for marketing campaigns opt-in filter
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_patients_marketing_opt_in"
        " ON vitalia_patients (tenant_id, clinic_id, marketing_opt_in)"
        " WHERE marketing_opt_in = TRUE AND opt_out = FALSE;"
    )


def downgrade() -> None:
    """Drop marketing consent columns from vitalia_patients (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_patients_marketing_opt_in;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_patients_opt_out;")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS opt_out_at;")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS opt_out_reason;")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS opt_out;")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS marketing_opt_in;")
