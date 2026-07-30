"""Lead screening events table — Adrián screening tool PHI table.

Stores per-lead qualification screening outcomes produced by the
LeadScreeningTool (sales_agent). PHI table per HIPAA-lite overlay:
requires dual filter (tenant_id + clinic_id) on every query.

Columns:
  id               UUID PK
  tenant_id        UUID NOT NULL
  clinic_id        UUID NOT NULL
  lead_id          UUID NOT NULL
  vertical         VARCHAR(32) — clinic vertical context for question set
  questions_asked  JSONB NOT NULL DEFAULT '[]'
  response_text    TEXT nullable — raw transcript/summary
  outcome          VARCHAR(32) NOT NULL — screening verdict
  reasoning        TEXT nullable — LLM chain-of-thought (sanitized before store)
  evaluated_at     TIMESTAMPTZ nullable — when screening completed
  created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
  deleted_at       TIMESTAMPTZ nullable — soft delete

Indexes:
  ix_lead_screening_events_tenant_clinic_lead (tenant_id, clinic_id, lead_id)
  ix_lead_screening_events_tenant_vertical_outcome (tenant_id, vertical, outcome)

All DDL idempotent via CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.

Revision ID: 017_vitalia
Revises: 016_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "017_vitalia"
down_revision = "016_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create lead_screening_events table idempotent."""
    op.execute("""
        CREATE TABLE IF NOT EXISTS lead_screening_events (
            id               UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id        UUID        NOT NULL,
            clinic_id        UUID        NOT NULL,
            lead_id          UUID        NOT NULL,
            vertical         VARCHAR(32) NOT NULL,
            questions_asked  JSONB       NOT NULL DEFAULT '[]'::jsonb,
            response_text    TEXT,
            outcome          VARCHAR(32) NOT NULL,
            reasoning        TEXT,
            evaluated_at     TIMESTAMPTZ,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at       TIMESTAMPTZ,
            CONSTRAINT pk_lead_screening_events PRIMARY KEY (id)
        )
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_lead_screening_events_tenant_clinic_lead"
        " ON lead_screening_events (tenant_id, clinic_id, lead_id)"
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_lead_screening_events_tenant_vertical_outcome"
        " ON lead_screening_events (tenant_id, vertical, outcome)"
    )


def downgrade() -> None:
    """Drop lead_screening_events indexes and table (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_lead_screening_events_tenant_vertical_outcome")
    op.execute("DROP INDEX IF EXISTS ix_lead_screening_events_tenant_clinic_lead")
    op.execute("DROP TABLE IF EXISTS lead_screening_events")
