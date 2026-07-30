"""Migration 026: slice1_marketing — add missing columns to vitalia_channel_sync_state.

Adds columns missing from initial migration 007:
  - enabled BOOLEAN NOT NULL DEFAULT TRUE
  - deleted_at TIMESTAMPTZ NULL

Also recreates the unique index with WHERE deleted_at IS NULL clause
(original index in 007 lacked the partial filter).

Per vitalia/docs/product/stories/vitalia-slice-1-marketing/03-arch-be.md §2.1
"""

from __future__ import annotations

from alembic import op

# Alembic revision identifiers
revision = "026_vitalia"
down_revision = "025_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add missing columns to vitalia_channel_sync_state (idempotent)."""
    op.execute(
        """
        ALTER TABLE vitalia_channel_sync_state
            ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE;
        """
    )
    op.execute(
        """
        ALTER TABLE vitalia_channel_sync_state
            ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMPTZ NULL;
        """
    )
    # Add partial unique index with WHERE deleted_at IS NULL
    # (original 007 index lacked the WHERE clause; drop + recreate if exists)
    op.execute(
        """
        DROP INDEX IF EXISTS uq_vitalia_channel_sync_state_tenant_provider;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_channel_sync_state_tenant_provider
            ON vitalia_channel_sync_state (tenant_id, clinic_id, provider)
            WHERE deleted_at IS NULL;
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_channel_sync_state_status
            ON vitalia_channel_sync_state (tenant_id, clinic_id, status);
        """
    )


def downgrade() -> None:
    """Non-destructive — column removal not supported in prod."""
    pass
