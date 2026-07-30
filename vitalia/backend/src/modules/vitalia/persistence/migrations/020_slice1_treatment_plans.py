# cap: treatments.treatment-followup-workflow
# story-origin: TBD
"""Migration 020 — vitalia_treatment_plans (Slice 1 fidelización).

Creates vitalia_treatment_plans table with PHI-encrypted notes column (BYTEA, pgcrypto).
Enables pgcrypto extension for symmetric encryption at rest per hipaa-lite.md.

Per .claude/rules/backend-migrations.md:
- Raw SQL only: op.execute() with CREATE TABLE IF NOT EXISTS
- NEVER op.create_table() / sa.Enum(create_type=True)
- TIMESTAMPTZ on all datetime columns

Per vitalia/.claude/rules/hipaa-lite.md:
- tenant_id + clinic_id NOT NULL (dual filter mandatory)
- notes BYTEA (pgcrypto symmetric encryption — PHI)
- deleted_at TIMESTAMPTZ NULL (soft delete)
- pgcrypto extension mandatory
"""

from __future__ import annotations

from alembic import op  # type: ignore[import]


def upgrade() -> None:
    """Apply migration: create vitalia_treatment_plans table + 3 indexes."""
    # Enable pgcrypto for PHI encryption at rest (idempotent)
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_treatment_plans (
          id UUID PRIMARY KEY,
          tenant_id UUID NOT NULL,
          clinic_id UUID NOT NULL,
          patient_id UUID NOT NULL,
          offer_id UUID NULL,
          doctor_id UUID NULL,
          sessions_total INT NOT NULL,
          sessions_completed INT NOT NULL DEFAULT 0,
          next_session_due_at TIMESTAMPTZ NULL,
          gap_alert_days INT NULL,
          status VARCHAR(16) NOT NULL DEFAULT 'active',
          notes BYTEA NULL,
          last_session_at TIMESTAMPTZ NULL,
          paused_until TIMESTAMPTZ NULL,
          pause_reason TEXT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          deleted_at TIMESTAMPTZ NULL
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_tenant_clinic_status
          ON vitalia_treatment_plans (tenant_id, clinic_id, status)
          WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_patient
          ON vitalia_treatment_plans (tenant_id, clinic_id, patient_id, status)
          WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_plans_gap_query
          ON vitalia_treatment_plans (tenant_id, clinic_id, last_session_at, gap_alert_days)
          WHERE status = 'active' AND deleted_at IS NULL
        """
    )


def downgrade() -> None:
    """Reverse migration: drop indexes + table. NOTE: pgcrypto extension NOT dropped (shared)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_treatment_plans_gap_query")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_treatment_plans_patient")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_treatment_plans_tenant_clinic_status")
    op.execute("DROP TABLE IF EXISTS vitalia_treatment_plans")
