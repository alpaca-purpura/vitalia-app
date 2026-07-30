"""Migration 024b — vitalia_nps_responses (Slice 1 fidelización).

Creates vitalia_nps_responses table in the alembic tree before migration 025
(pgcrypto trigger) can run. Origin: this content was previously in
`vitalia/backend/src/modules/vitalia/persistence/migrations/022_slice1_nps_responses.py`
but that module-local migration was never wired into the alembic tree
(`alembic.ini::script_location = alembic`), so the table never existed when
025 tried to install its encryption trigger → backend crash loop.

F1-S0 (vitalia-fase1-stack-stability) discovered the broken migration chain
during visual goldens setup. Lift to alembic tree to unblock dev stack +
prod deploy. Module-local 022 file kept as deprecated reference until
slice-1-fidelizacion follow-up cleans it.

Per .claude/rules/backend-migrations.md:
- Raw SQL only: op.execute() with CREATE TABLE IF NOT EXISTS
- NEVER op.create_table() / sa.Enum(create_type=True)
- TIMESTAMPTZ on all datetime columns

Per vitalia/.claude/rules/hipaa-lite.md:
- tenant_id + clinic_id NOT NULL (dual filter mandatory)
- comment BYTEA (pgcrypto symmetric encryption — patient free text PHI; trigger applied in 025)
- deleted_at TIMESTAMPTZ NULL (soft delete)

Revision ID: 024b_vitalia
Revises: 024_vitalia
Create Date: 2026-05-22
"""

from __future__ import annotations

from alembic import op  # type: ignore[import]

revision = "024b_vitalia"
down_revision = "024_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_nps_responses table + 2 indexes."""
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
    """Drop indexes + table. NOTE: migration 025 trigger must be downgraded first."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_nps_responses_patient")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_nps_responses_tenant_clinic_band")
    op.execute("DROP TABLE IF EXISTS vitalia_nps_responses")
