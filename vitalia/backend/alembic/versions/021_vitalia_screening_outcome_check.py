"""Screening outcome CHECK constraint on lead_screening_events.

Adds a CHECK constraint to `lead_screening_events.outcome` limiting values to
the canonical ScreeningOutcome enum:
  ('booking_ready', 'objection_handle', 'disqualified', 'manual_review')

Outcome stored as VARCHAR (never sa.Enum with create_type=True — broken SA 2.0.27
per .claude/rules/backend-migrations.md).

Idempotency: uses DO $$...EXCEPTION WHEN duplicate_object THEN NULL END$$ pattern
so re-running upgrade is a no-op even if constraint already exists.

Revision ID: 021_vitalia
Revises: 020_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "021_vitalia"
down_revision = "020_vitalia"
branch_labels = None
depends_on = None

_CONSTRAINT_NAME = "screening_outcome_chk"
_VALID_OUTCOMES = "('booking_ready','objection_handle','disqualified','manual_review')"


def upgrade() -> None:
    """Add CHECK constraint on lead_screening_events.outcome — idempotent."""
    op.execute(f"""
        DO $$
        BEGIN
            ALTER TABLE lead_screening_events
                ADD CONSTRAINT {_CONSTRAINT_NAME}
                CHECK (outcome IN {_VALID_OUTCOMES});
        EXCEPTION
            WHEN duplicate_object THEN
                NULL;  -- constraint already exists, no-op
        END
        $$
    """)


def downgrade() -> None:
    """Drop CHECK constraint on lead_screening_events.outcome (dev iteration only)."""
    op.execute(f"ALTER TABLE lead_screening_events DROP CONSTRAINT IF EXISTS {_CONSTRAINT_NAME}")
