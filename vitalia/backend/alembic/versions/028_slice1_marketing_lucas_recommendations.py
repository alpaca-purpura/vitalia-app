"""Migration 028: slice1_marketing — add missing columns to vitalia_lucas_recommendations.

Adds columns missing from initial migration 009:
  - action_payload_json JSONB NULL
  - confidence_pct INT NULL
  - projected_impact_text TEXT NULL
  - rejected_by_user_id UUID NULL
  - rejected_at TIMESTAMPTZ NULL
  - reject_reason VARCHAR(64) NULL

Also adds indexes defined in arch spec §2.3.

Per vitalia/docs/product/stories/vitalia-slice-1-marketing/03-arch-be.md §2.3
"""

from __future__ import annotations

from alembic import op

# Alembic revision identifiers
revision = "028_vitalia"
down_revision = "027_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to vitalia_lucas_recommendations (idempotent)."""
    op.execute(
        """
        ALTER TABLE vitalia_lucas_recommendations
            ADD COLUMN IF NOT EXISTS action_payload_json JSONB NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE vitalia_lucas_recommendations
            ADD COLUMN IF NOT EXISTS confidence_pct INT NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE vitalia_lucas_recommendations
            ADD COLUMN IF NOT EXISTS projected_impact_text TEXT NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE vitalia_lucas_recommendations
            ADD COLUMN IF NOT EXISTS rejected_by_user_id UUID NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE vitalia_lucas_recommendations
            ADD COLUMN IF NOT EXISTS rejected_at TIMESTAMPTZ NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE vitalia_lucas_recommendations
            ADD COLUMN IF NOT EXISTS reject_reason VARCHAR(64) NULL;
        """
    )
    # Add performance indexes
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_lucas_recommendations_stage_status
            ON vitalia_lucas_recommendations (tenant_id, clinic_id, stage, status, priority DESC)
            WHERE deleted_at IS NULL;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_lucas_recommendations_undo_window
            ON vitalia_lucas_recommendations (undo_until)
            WHERE undo_until IS NOT NULL;
        """
    )


def downgrade() -> None:
    """Non-destructive — column removal not supported in prod."""
    pass
