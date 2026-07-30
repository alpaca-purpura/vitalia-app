"""Referrals leaderboard snapshots table — Lucas referral analytics.

Stores periodic leaderboard snapshots of top referrers computed by the
LucasReferralTool. Captures ranked referrer data per tenant + clinic
for display in the Growth Studio referrals leaderboard widget.

Columns:
  id               UUID PK
  tenant_id        UUID NOT NULL
  clinic_id        UUID NOT NULL
  period_start     DATE NOT NULL — start of leaderboard period
  period_end       DATE NOT NULL — end of leaderboard period
  top_referrers    JSONB NOT NULL DEFAULT '[]'
                   — [{referrer_id, name, referral_count, converted_count, rank}]
  total_referrals  INTEGER NOT NULL DEFAULT 0 — total referrals in period
  total_converted  INTEGER NOT NULL DEFAULT 0 — total converted in period
  computed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
  deleted_at       TIMESTAMPTZ nullable — soft delete

Indexes:
  ix_referrals_leaderboard_snapshots_tenant_clinic_period
    (tenant_id, clinic_id, period_start, period_end)
  uq_referrals_leaderboard_snapshots_tenant_clinic_period
    UNIQUE (tenant_id, clinic_id, period_start) WHERE deleted_at IS NULL

All DDL idempotent via CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.

Revision ID: 019_vitalia
Revises: 018_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "019_vitalia"
down_revision = "018_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create referrals_leaderboard_snapshots table idempotent."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS referrals_leaderboard_snapshots (
            id              UUID    NOT NULL DEFAULT gen_random_uuid(),
            tenant_id       UUID    NOT NULL,
            clinic_id       UUID    NOT NULL,
            period_start    DATE    NOT NULL,
            period_end      DATE    NOT NULL,
            top_referrers   JSONB   NOT NULL DEFAULT '[]'::jsonb,
            total_referrals INTEGER NOT NULL DEFAULT 0,
            total_converted INTEGER NOT NULL DEFAULT 0,
            computed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            CONSTRAINT pk_referrals_leaderboard_snapshots PRIMARY KEY (id)
        )
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_referrals_leaderboard_snapshots_tenant_clinic_period"
        " ON referrals_leaderboard_snapshots (tenant_id, clinic_id, period_start, period_end)"
    )

    # Unique constraint: one snapshot per (tenant, clinic, period_start)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_referrals_leaderboard_snapshots_tenant_clinic_period"
        " ON referrals_leaderboard_snapshots (tenant_id, clinic_id, period_start)"
        " WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    """Drop referrals_leaderboard_snapshots indexes and table (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS uq_referrals_leaderboard_snapshots_tenant_clinic_period")
    op.execute("DROP INDEX IF EXISTS ix_referrals_leaderboard_snapshots_tenant_clinic_period")
    op.execute("DROP TABLE IF EXISTS referrals_leaderboard_snapshots")
