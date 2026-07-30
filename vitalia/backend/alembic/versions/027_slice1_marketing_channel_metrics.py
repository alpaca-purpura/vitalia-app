"""Migration 027: slice1_marketing — add campaign columns to vitalia_channel_metrics.

Adds columns missing from initial migration 008:
  - campaign_id VARCHAR(128) NULL
  - campaign_name VARCHAR(256) NULL

Also recreates the unique index to include campaign_id
(original index in 008 did not include campaign_id per arch spec §2.2).

Per vitalia/docs/product/stories/vitalia-slice-1-marketing/03-arch-be.md §2.2
"""

from __future__ import annotations

from alembic import op

# Alembic revision identifiers
revision = "027_vitalia"
down_revision = "026_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add campaign columns to vitalia_channel_metrics (idempotent)."""
    op.execute(
        """
        ALTER TABLE vitalia_channel_metrics
            ADD COLUMN IF NOT EXISTS campaign_id VARCHAR(128) NULL;
        """
    )
    op.execute(
        """
        ALTER TABLE vitalia_channel_metrics
            ADD COLUMN IF NOT EXISTS campaign_name VARCHAR(256) NULL;
        """
    )
    # Recreate unique index with campaign_id included per arch spec §2.2
    op.execute(
        """
        DROP INDEX IF EXISTS uq_vitalia_channel_metrics_unique;
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_channel_metrics_unique
            ON vitalia_channel_metrics (
                tenant_id, clinic_id, provider, channel_slug, campaign_id, metric_date
            );
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_channel_metrics_date
            ON vitalia_channel_metrics (tenant_id, clinic_id, metric_date DESC);
        """
    )


def downgrade() -> None:
    """Non-destructive — column removal not supported in prod."""
    pass
