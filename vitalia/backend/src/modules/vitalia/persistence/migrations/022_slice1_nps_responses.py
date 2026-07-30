# cap: patients.nps-tracking
# story-origin: TBD
"""Migration 022 — vitalia_nps_responses (Slice 1 fidelización).

Creates vitalia_nps_responses table. Patient free-text comment encrypted via pgcrypto
(comment BYTEA — PHI per hipaa-lite.md).

Per .claude/rules/backend-migrations.md:
- Raw SQL only: op.execute() with CREATE TABLE IF NOT EXISTS
- NEVER op.create_table() / sa.Enum(create_type=True)
- TIMESTAMPTZ on all datetime columns

Per vitalia/.claude/rules/hipaa-lite.md:
- tenant_id + clinic_id NOT NULL (dual filter mandatory)
- comment BYTEA (pgcrypto symmetric encryption — patient free text PHI)
- deleted_at TIMESTAMPTZ NULL (soft delete)
- NO deleted_at on audit_log table (immutable), but NPS responses CAN be soft-deleted
"""

from __future__ import annotations

from alembic import op  # type: ignore[import]


def upgrade() -> None:
    """Apply migration: create vitalia_nps_responses table + 2 indexes."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_nps_responses (
          id UUID PRIMARY KEY,
          tenant_id UUID NOT NULL,
          clinic_id UUID NOT NULL,
          patient_id UUID NOT NULL,
          appointment_id UUID NULL,
          score INT NOT NULL CHECK (score >= 0 AND score <= 10),
          band VARCHAR(16) NOT NULL,
          comment BYTEA NULL,
          source VARCHAR(32) NOT NULL DEFAULT 'whatsapp_template',
          trigger_re_engagement_event_id UUID NULL,
          responded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          tagged_in_inbox BOOLEAN NOT NULL DEFAULT FALSE,
          audit_log_id UUID NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          deleted_at TIMESTAMPTZ NULL
        )
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_nps_responses_tenant_clinic_band
          ON vitalia_nps_responses (tenant_id, clinic_id, band, responded_at DESC)
          WHERE deleted_at IS NULL
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_nps_responses_patient
          ON vitalia_nps_responses (tenant_id, clinic_id, patient_id, responded_at DESC)
          WHERE deleted_at IS NULL
        """
    )


def downgrade() -> None:
    """Reverse migration: drop indexes + table."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_nps_responses_patient")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_nps_responses_tenant_clinic_band")
    op.execute("DROP TABLE IF EXISTS vitalia_nps_responses")
