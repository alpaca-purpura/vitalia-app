# cap: clinics.lisa.doctores
"""Migration 044 — excluded_dates JSONB on vitalia_availability_blocks.

Feature: scoped delete (occurrence | this_and_future) for recurrent availability blocks.
excluded_dates stores a list of ISO date strings ("YYYY-MM-DD") for occurrences
that have been individually excluded without deleting the entire series.

DDL is idempotent: ADD COLUMN IF NOT EXISTS.

Revision ID: 044_vitalia
Revises: 043_vitalia
"""

from alembic import op

revision = "044_vitalia"
down_revision = "043_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE vitalia_availability_blocks
        ADD COLUMN IF NOT EXISTS excluded_dates JSONB;
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE vitalia_availability_blocks
        DROP COLUMN IF EXISTS excluded_dates;
        """
    )
