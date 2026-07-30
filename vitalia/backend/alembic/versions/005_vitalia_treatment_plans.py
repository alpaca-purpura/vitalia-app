"""Vitalia treatment plans table — multi-session adherence tracking (PHI encrypted).

Tracks patient treatment plans for the /fidelizacion multi-session pattern.
notes column uses BYTEA with pgcrypto symmetric encryption (PHI per
hipaa-lite.md § Encryption at rest).

Requires pgcrypto extension (enabled in 013_vitalia_audit_log).
We CREATE EXTENSION IF NOT EXISTS pgcrypto here as well (idempotent).

All DDL idempotent via IF NOT EXISTS.

Revision ID: 005_vitalia
Revises: 004_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "005_vitalia"
down_revision = "004_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_treatment_plans table with PHI-encrypted notes column."""

    # Ensure pgcrypto extension available for BYTEA encryption (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_treatment_plans (
            id                      UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID        NOT NULL,
            clinic_id               UUID        NOT NULL,
            patient_id              UUID        NOT NULL,
            offer_id                UUID,
            doctor_id               UUID,
            sessions_total          INTEGER     NOT NULL,
            sessions_completed      INTEGER     NOT NULL DEFAULT 0,
            next_session_due_at     TIMESTAMPTZ,
            gap_alert_days          INTEGER,
            status                  VARCHAR(16) NOT NULL DEFAULT 'active',
            notes                   BYTEA,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at              TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_treatment_plans PRIMARY KEY (id)
        );
    """)

    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_tenant_clinic_status
          ON vitalia_treatment_plans (tenant_id, clinic_id, status)
          WHERE deleted_at IS NULL;
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_tenant_clinic_patient"
        " ON vitalia_treatment_plans (tenant_id, clinic_id, patient_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_next_session"
        " ON vitalia_treatment_plans (tenant_id, clinic_id, next_session_due_at)"
        " WHERE deleted_at IS NULL;"
    )


def downgrade() -> None:
    """Drop vitalia_treatment_plans (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_treatment_plans_next_session;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_treatment_plans_tenant_clinic_patient;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_treatment_plans_tenant_clinic_status;")
    op.execute("DROP TABLE IF EXISTS vitalia_treatment_plans;")
