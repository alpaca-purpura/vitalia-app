"""Vitalia re-engagement events table — /fidelizacion automation patterns (PHI encrypted).

Records proactive outbound messages sent to patients for 4 re-engagement
patterns: multi_session (incomplete course), follow_up (doctor-set),
maintenance (periodic), absence (long absence), nps (satisfaction).

payload_phi uses BYTEA with pgcrypto encryption (PHI per hipaa-lite.md).
throttle index prevents spam per patient+pattern within window.

All DDL idempotent via IF NOT EXISTS.

Revision ID: 006_vitalia
Revises: 005_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "006_vitalia"
down_revision = "005_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_re_engagement_events table with PHI-encrypted payload."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events (
            id              UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            clinic_id       UUID        NOT NULL,
            patient_id      UUID        NOT NULL,
            pattern         VARCHAR(32) NOT NULL,
            trigger_source  VARCHAR(32) NOT NULL,
            template_id     VARCHAR(64),
            sent_at         TIMESTAMPTZ,
            response_at     TIMESTAMPTZ,
            outcome         VARCHAR(32),
            payload_phi     BYTEA,
            audit_log_id    UUID,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at      TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_re_engagement_events PRIMARY KEY (id)
        );
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_pattern_patient"
        " ON vitalia_re_engagement_events (tenant_id, clinic_id, patient_id, pattern);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_throttle"
        " ON vitalia_re_engagement_events (tenant_id, clinic_id, patient_id, pattern, sent_at);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_tenant_clinic"
        " ON vitalia_re_engagement_events (tenant_id, clinic_id, created_at);"
    )


def downgrade() -> None:
    """Drop vitalia_re_engagement_events (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_re_engagement_events_tenant_clinic;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_re_engagement_events_throttle;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_re_engagement_events_pattern_patient;")
    op.execute("DROP TABLE IF EXISTS vitalia_re_engagement_events;")
