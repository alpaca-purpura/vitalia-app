"""Attribution matrix snapshots table — Lucas attribution analytics.

Stores periodic snapshots of the attribution matrix computed by the
LucasAttributionTool. Captures source-to-conversion weight distribution
with revenue attribution for each tenant + clinic combination.
Used by the analytics module to display attribution trends and track
campaign effectiveness per period.

Columns:
  id                       UUID PK
  tenant_id                UUID NOT NULL
  clinic_id                UUID NOT NULL
  period_start             DATE NOT NULL — start of attribution period
  period_end               DATE NOT NULL — end of attribution period
  channel_breakdown        JSONB NOT NULL DEFAULT '{}' — {channel: {leads, converted, revenue}}
  total_attributed_revenue NUMERIC(16,2) NOT NULL DEFAULT 0
  currency                 CHAR(3) — ISO-4217 from tenant locale (never hardcoded)
  computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
  deleted_at               TIMESTAMPTZ nullable — soft delete

Indexes:
  ix_attribution_matrix_snapshots_tenant_clinic_period
    (tenant_id, clinic_id, period_start, period_end)
  uq_attribution_matrix_snapshots_tenant_clinic_period
    UNIQUE (tenant_id, clinic_id, period_start) WHERE deleted_at IS NULL

All DDL idempotent via CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.

Revision ID: 018_vitalia
Revises: 017_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "018_vitalia"
down_revision = "017_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create attribution_matrix_snapshots table idempotent."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS attribution_matrix_snapshots (
            id                       UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id                UUID        NOT NULL,
            clinic_id                UUID        NOT NULL,
            period_start             DATE        NOT NULL,
            period_end               DATE        NOT NULL,
            channel_breakdown        JSONB       NOT NULL DEFAULT '{}'::jsonb,
            total_attributed_revenue NUMERIC(16,2) NOT NULL DEFAULT 0,
            currency                 CHAR(3),
            computed_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at               TIMESTAMPTZ,
            CONSTRAINT pk_attribution_matrix_snapshots PRIMARY KEY (id)
        )
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_attribution_matrix_snapshots_tenant_clinic_period"
        " ON attribution_matrix_snapshots (tenant_id, clinic_id, period_start, period_end)"
    )

    # Unique constraint: one snapshot per (tenant, clinic, period_start)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_attribution_matrix_snapshots_tenant_clinic_period"
        " ON attribution_matrix_snapshots (tenant_id, clinic_id, period_start)"
        " WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    """Drop attribution_matrix_snapshots indexes and table (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS uq_attribution_matrix_snapshots_tenant_clinic_period")
    op.execute("DROP INDEX IF EXISTS ix_attribution_matrix_snapshots_tenant_clinic_period")
    op.execute("DROP TABLE IF EXISTS attribution_matrix_snapshots")
