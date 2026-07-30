"""Vitalia Lucas recommendations table — AI-driven marketing action cards.

Lucas (the marketing intelligence layer) emits per-tenant per-clinic
recommendations across 5 funnel stages. Includes 5-minute undo window
(undo_until) and expiry (expires_at).

status lifecycle: open -> approved | rejected | expired | undone

Soft-delete supported for approved/rejected records with audit trail.

All DDL idempotent via IF NOT EXISTS.

Revision ID: 009_vitalia
Revises: 008_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "009_vitalia"
down_revision = "008_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_lucas_recommendations table idempotent."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_lucas_recommendations (
            id                      UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID        NOT NULL,
            clinic_id               UUID        NOT NULL,
            stage                   VARCHAR(32) NOT NULL,
            recommendation_kind     VARCHAR(64) NOT NULL,
            title                   TEXT        NOT NULL,
            body                    TEXT        NOT NULL,
            rationale_json          JSONB       NOT NULL DEFAULT '{}'::jsonb,
            priority                INTEGER     NOT NULL DEFAULT 50,
            status                  VARCHAR(16) NOT NULL DEFAULT 'open',
            approved_by_user_id     UUID,
            approved_at             TIMESTAMPTZ,
            undo_until              TIMESTAMPTZ,
            expires_at              TIMESTAMPTZ NOT NULL,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at              TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_lucas_recommendations PRIMARY KEY (id)
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vitalia_lucas_recommendations_stage_status
          ON vitalia_lucas_recommendations (tenant_id, clinic_id, stage, status, priority DESC)
          WHERE deleted_at IS NULL;
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_lucas_recommendations_expires"
        " ON vitalia_lucas_recommendations (tenant_id, clinic_id, expires_at)"
        " WHERE status = 'open';"
    )


def downgrade() -> None:
    """Drop vitalia_lucas_recommendations (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_lucas_recommendations_expires;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_lucas_recommendations_stage_status;")
    op.execute("DROP TABLE IF EXISTS vitalia_lucas_recommendations;")
