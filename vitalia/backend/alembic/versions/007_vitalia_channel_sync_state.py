"""Vitalia channel sync state table — marketing channel OAuth + sync tracking.

Tracks per-tenant per-provider OAuth token and sync lifecycle for Meta Ads
and Google Ads providers. oauth_token_encrypted uses BYTEA with pgcrypto
encryption for at-rest security.

Unique constraint per (tenant_id, clinic_id, provider) — one sync state
per channel per clinic.

No deleted_at: sync state is operational metadata (not PHI, not financial).
Replaced by new row on re-connect.

All DDL idempotent via IF NOT EXISTS.

Revision ID: 007_vitalia
Revises: 006_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "007_vitalia"
down_revision = "006_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_channel_sync_state table idempotent."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_channel_sync_state (
            id                      UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID        NOT NULL,
            clinic_id               UUID        NOT NULL,
            provider                VARCHAR(32) NOT NULL,
            last_sync_at            TIMESTAMPTZ,
            last_success_at         TIMESTAMPTZ,
            last_error              TEXT,
            status                  VARCHAR(16) NOT NULL DEFAULT 'idle',
            oauth_token_encrypted   BYTEA,
            account_id              VARCHAR(128),
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_channel_sync_state PRIMARY KEY (id)
        );
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_channel_sync_state_tenant_provider
          ON vitalia_channel_sync_state (tenant_id, clinic_id, provider);
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_channel_sync_state_tenant_clinic"
        " ON vitalia_channel_sync_state (tenant_id, clinic_id);"
    )


def downgrade() -> None:
    """Drop vitalia_channel_sync_state (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_channel_sync_state_tenant_clinic;")
    op.execute("DROP INDEX IF EXISTS uq_vitalia_channel_sync_state_tenant_provider;")
    op.execute("DROP TABLE IF EXISTS vitalia_channel_sync_state;")
