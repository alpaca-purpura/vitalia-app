"""Migration 031: slice1_marketing — add value tracking columns to vitalia_referrals
and conversion_value_cents to vitalia_appointments.

Referrals value columns (spec § 2.4):
  - conversion_value_cents BIGINT NULL — total appointment value attributed to referral
  - currency CHAR(3) NULL — ISO-4217 code from tenant locale (NEVER hardcoded)
  - shared_at TIMESTAMPTZ NULL — when referrer shared the code with prospect
  - signed_up_at TIMESTAMPTZ NULL — when referred prospect booked first appointment

Appointments column (spec § 2.5):
  - conversion_value_cents BIGINT NULL — appointment monetary value for referral attribution
    (used by referrals_value_sync cron to compute total referral conversion value)

HIPAA-lite:
  - conversion_value_cents stores aggregate monetary value only — no PHI.
  - currency from tenant locale — NEVER hardcoded.

Per vitalia/docs/product/stories/vitalia-slice-1-marketing/03-arch-be.md §2.4, §2.5
"""

from __future__ import annotations

from alembic import op

# Alembic revision identifiers
revision = "031_vitalia"
down_revision = "030_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add value tracking columns to vitalia_referrals and vitalia_appointments (idempotent)."""
    # -- vitalia_referrals: value tracking columns --
    op.execute(
        """
        ALTER TABLE vitalia_referrals
            ADD COLUMN IF NOT EXISTS conversion_value_cents BIGINT NULL,
            ADD COLUMN IF NOT EXISTS currency CHAR(3) NULL,
            ADD COLUMN IF NOT EXISTS shared_at TIMESTAMPTZ NULL,
            ADD COLUMN IF NOT EXISTS signed_up_at TIMESTAMPTZ NULL;
        """
    )

    # Index for referrals_value_sync cron (queries by status signed_up/converted)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_referrals_value_sync
            ON vitalia_referrals (tenant_id, clinic_id, status)
            WHERE status IN ('signed_up', 'converted') AND deleted_at IS NULL;
        """
    )

    # -- vitalia_appointments: conversion value for referral attribution --
    op.execute(
        """
        ALTER TABLE vitalia_appointments
            ADD COLUMN IF NOT EXISTS conversion_value_cents BIGINT NULL;
        """
    )

    # Index for sum queries in referrals_value_sync cron
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_conversion_value
            ON vitalia_appointments (tenant_id, clinic_id, patient_id, status)
            WHERE status = 'completed' AND deleted_at IS NULL;
        """
    )


def downgrade() -> None:
    """Non-destructive — column removal not supported in prod."""
    pass
