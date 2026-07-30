"""Migration 030: slice1_marketing — add utm_medium column to vitalia_appointments.

utm_source and utm_campaign were already added in migration 002.
This migration adds the missing utm_medium column per arch spec §2.5.

UTM fields contain NO PHI — only campaign attribution metadata.

Per vitalia/docs/product/stories/vitalia-slice-1-marketing/03-arch-be.md §2.5
"""

from __future__ import annotations

from alembic import op

# Alembic revision identifiers
revision = "030_vitalia"
down_revision = "029_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add utm_medium to vitalia_appointments (idempotent)."""
    op.execute(
        """
        ALTER TABLE vitalia_appointments
            ADD COLUMN IF NOT EXISTS utm_medium VARCHAR(64) NULL;
        """
    )
    # Add composite UTM index for attribution queries
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_utm
            ON vitalia_appointments (tenant_id, clinic_id, utm_source, utm_campaign)
            WHERE utm_source IS NOT NULL;
        """
    )


def downgrade() -> None:
    """Non-destructive — column removal not supported in prod."""
    pass
