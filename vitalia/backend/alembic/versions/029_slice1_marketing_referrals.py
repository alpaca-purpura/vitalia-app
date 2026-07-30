"""Migration 029: slice1_marketing — add deleted_at to vitalia_referrals.

Adds column missing from initial migration 010:
  - deleted_at TIMESTAMPTZ NULL

Also recreates unique index with WHERE deleted_at IS NULL partial filter
and adds referrer index per arch spec §2.4.

Per vitalia/docs/product/stories/vitalia-slice-1-marketing/03-arch-be.md §2.4
"""

from __future__ import annotations

from alembic import op

# Alembic revision identifiers
revision = "029_vitalia"
down_revision = "028_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add deleted_at to vitalia_referrals (idempotent)."""
    op.execute(
        """
        ALTER TABLE vitalia_referrals
            ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ NULL;
        """
    )
    # Recreate partial unique index with WHERE deleted_at IS NULL
    op.execute(
        """
        DROP INDEX IF EXISTS uq_vitalia_referrals_code;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_referrals_code
            ON vitalia_referrals (tenant_id, clinic_id, referral_code)
            WHERE deleted_at IS NULL;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_referrals_referrer
            ON vitalia_referrals (tenant_id, clinic_id, referrer_patient_id, status)
            WHERE deleted_at IS NULL;
        """
    )


def downgrade() -> None:
    """Non-destructive — column removal not supported in prod."""
    pass
