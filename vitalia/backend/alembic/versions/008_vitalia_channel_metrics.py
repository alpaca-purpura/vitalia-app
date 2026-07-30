"""Vitalia channel metrics table — marketing analytics ETL sink.

Stores per-day per-channel marketing metrics extracted from Meta Ads and
Google Ads providers. Unique constraint prevents duplicate rows for the
same (tenant, clinic, provider, channel, date) tuple — safe for upsert
ETL pattern.

currency column nullable per master-data.md (source currency from provider,
never hardcoded).

All DDL idempotent via IF NOT EXISTS.

Revision ID: 008_vitalia
Revises: 007_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "008_vitalia"
down_revision = "007_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_channel_metrics table idempotent."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_channel_metrics (
            id              UUID    NOT NULL DEFAULT gen_random_uuid(),
            tenant_id       UUID    NOT NULL,
            clinic_id       UUID    NOT NULL,
            provider        VARCHAR(32) NOT NULL,
            channel_slug    VARCHAR(64) NOT NULL,
            metric_date     DATE    NOT NULL,
            impressions     BIGINT,
            clicks          BIGINT,
            conversions     BIGINT,
            spend_cents     BIGINT,
            currency        CHAR(3),
            raw_payload     JSONB   NOT NULL DEFAULT '{}'::jsonb,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_channel_metrics PRIMARY KEY (id)
        );
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_channel_metrics_unique
          ON vitalia_channel_metrics (tenant_id, clinic_id, provider, channel_slug, metric_date);
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_channel_metrics_date"
        " ON vitalia_channel_metrics (tenant_id, clinic_id, metric_date);"
    )


def downgrade() -> None:
    """Drop vitalia_channel_metrics (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_channel_metrics_date;")
    op.execute("DROP INDEX IF EXISTS uq_vitalia_channel_metrics_unique;")
    op.execute("DROP TABLE IF EXISTS vitalia_channel_metrics;")
