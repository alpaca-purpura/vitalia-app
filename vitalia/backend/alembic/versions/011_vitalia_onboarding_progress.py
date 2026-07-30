"""Vitalia onboarding progress table — wizard agentic slot tracking.

Tracks per-user onboarding wizard progress for the 3-required + 2-optional
+ bonus NLU slot taxonomy. JSONB columns store slot state efficiently
without schema changes as slot taxonomy evolves.

Unique constraint per (tenant_id, user_id) — one active onboarding session
per user.

No clinic_id: onboarding is user-level (pre-clinic-setup), tenant-scoped.
No deleted_at: status 'abandoned' replaces soft delete.

All DDL idempotent via IF NOT EXISTS.

Revision ID: 011_vitalia
Revises: 010_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "011_vitalia"
down_revision = "010_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_onboarding_progress table idempotent."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_onboarding_progress (
            id              UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            user_id         UUID        NOT NULL,
            step            VARCHAR(64) NOT NULL,
            slots_confirmed JSONB       NOT NULL DEFAULT '{}'::jsonb,
            slots_pending   JSONB       NOT NULL DEFAULT '{}'::jsonb,
            mode            VARCHAR(16),
            draft_id        UUID,
            attachments     JSONB       NOT NULL DEFAULT '[]'::jsonb,
            status          VARCHAR(16) NOT NULL DEFAULT 'in_progress',
            completed_at    TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_onboarding_progress PRIMARY KEY (id)
        );
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_onboarding_progress_tenant_user
          ON vitalia_onboarding_progress (tenant_id, user_id);
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_onboarding_progress_tenant_status"
        " ON vitalia_onboarding_progress (tenant_id, status);"
    )


def downgrade() -> None:
    """Drop vitalia_onboarding_progress (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_onboarding_progress_tenant_status;")
    op.execute("DROP INDEX IF EXISTS uq_vitalia_onboarding_progress_tenant_user;")
    op.execute("DROP TABLE IF EXISTS vitalia_onboarding_progress;")
