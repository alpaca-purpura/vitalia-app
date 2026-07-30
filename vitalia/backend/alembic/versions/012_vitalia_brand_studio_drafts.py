"""Vitalia brand studio drafts table — onboarding extraction staging area.

Stores intermediate extracted brand/personality data during onboarding wizard
before commitment to the canonical brand_settings JSONB on tenants table.
Supports resumable extraction sessions with TTL via expires_at.

draft_kind: 'onboarding_extraction' (Slice 1) | future kinds (Slice 2+).
voice_profile_partial_json: partial PersonalityProfile compilation.
committed_at: null = draft, non-null = committed to brand_settings.

No clinic_id: brand studio is tenant-level config.
No deleted_at: expired drafts purged by cron sweep via expires_at.

All DDL idempotent via IF NOT EXISTS.

Revision ID: 012_vitalia
Revises: 011_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "012_vitalia"
down_revision = "011_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_brand_studio_drafts table idempotent."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_brand_studio_drafts (
            id                          UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id                   UUID        NOT NULL,
            user_id                     UUID        NOT NULL,
            draft_kind                  VARCHAR(32) NOT NULL DEFAULT 'onboarding_extraction',
            draft_payload               JSONB       NOT NULL DEFAULT '{}'::jsonb,
            voice_profile_partial_json  JSONB,
            committed_at                TIMESTAMPTZ,
            expires_at                  TIMESTAMPTZ NOT NULL,
            created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_brand_studio_drafts PRIMARY KEY (id)
        );
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_brand_studio_drafts_tenant_user"
        " ON vitalia_brand_studio_drafts (tenant_id, user_id, committed_at);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_brand_studio_drafts_expires"
        " ON vitalia_brand_studio_drafts (expires_at)"
        " WHERE committed_at IS NULL;"
    )


def downgrade() -> None:
    """Drop vitalia_brand_studio_drafts (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_brand_studio_drafts_expires;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_brand_studio_drafts_tenant_user;")
    op.execute("DROP TABLE IF EXISTS vitalia_brand_studio_drafts;")
