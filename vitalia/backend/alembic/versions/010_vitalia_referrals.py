"""Vitalia referrals table — patient referral tracking for /marketing.

Tracks patient-to-patient referral lifecycle from share through conversion.
referral_code is unique per (tenant_id, clinic_id) for URL-based attribution.

Financial fields (conversion_value_cents, currency) nullable per
master-data.md — currency sourced from payment event at conversion time.

No deleted_at: referral records are marketing attribution data (immutable
for attribution accuracy). Status lifecycle manages state.

All DDL idempotent via IF NOT EXISTS.

Revision ID: 010_vitalia
Revises: 009_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "010_vitalia"
down_revision = "009_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_referrals table idempotent."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_referrals (
            id                      UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID        NOT NULL,
            clinic_id               UUID        NOT NULL,
            referrer_patient_id     UUID        NOT NULL,
            referred_patient_id     UUID,
            referral_code           VARCHAR(16) NOT NULL,
            shared_at               TIMESTAMPTZ,
            signed_up_at            TIMESTAMPTZ,
            converted_at            TIMESTAMPTZ,
            conversion_value_cents  BIGINT,
            currency                CHAR(3),
            status                  VARCHAR(16) NOT NULL DEFAULT 'open',
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_referrals PRIMARY KEY (id)
        );
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_referrals_code
          ON vitalia_referrals (tenant_id, clinic_id, referral_code);
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_referrals_referrer"
        " ON vitalia_referrals (tenant_id, clinic_id, referrer_patient_id, status);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_referrals_tenant_clinic_status"
        " ON vitalia_referrals (tenant_id, clinic_id, status, created_at);"
    )


def downgrade() -> None:
    """Drop vitalia_referrals (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_referrals_tenant_clinic_status;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_referrals_referrer;")
    op.execute("DROP INDEX IF EXISTS uq_vitalia_referrals_code;")
    op.execute("DROP TABLE IF EXISTS vitalia_referrals;")
