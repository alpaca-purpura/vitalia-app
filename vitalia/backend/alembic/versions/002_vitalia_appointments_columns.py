"""Vitalia appointments columns — extend vitalia_appointments with Slice 1 fields.

Creates vitalia_appointments table (IF NOT EXISTS — may exist from Story 11 as
vitalia_bookings alias or a prior migration). Adds 7 operational columns required
by the /agenda and /fidelizacion modules: origin, balance_status, follow_up_due_at,
follow_up_reason, completed_at, utm_source, utm_campaign.

All DDL idempotent via IF NOT EXISTS / ADD COLUMN IF NOT EXISTS.

Revision ID: 002_vitalia
Revises: 001_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "002_vitalia"
down_revision = "001_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Idempotent appointments table + Slice 1 column extensions."""

    # ─────────────────────────────────────────────────────────────────────────
    # vitalia_appointments — create if not exists (owns the booking aggregate
    # for Slice 1 with clinic_id dual-filter per hipaa-lite.md).
    # Story 11 has vitalia_bookings; Slice 1 introduces vitalia_appointments
    # as the renamed/extended table with clinic_id dual filter.
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_appointments (
            id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id           UUID            NOT NULL,
            clinic_id           UUID            NOT NULL,
            offer_id            UUID            NOT NULL,
            doctor_id           UUID            NOT NULL,
            patient_id          UUID            NOT NULL,
            consent_id          UUID,
            slot_iso            TIMESTAMPTZ     NOT NULL,
            duration_minutes    INTEGER         NOT NULL,
            status              VARCHAR(32)     NOT NULL,
            payment_status      VARCHAR(32)     NOT NULL DEFAULT 'not_initiated',
            amount_paid         NUMERIC(14, 2),
            amount_pending      NUMERIC(14, 2),
            currency            VARCHAR(3),
            deposit_percent     INTEGER,
            booking_metadata    JSONB           NOT NULL DEFAULT '{}'::jsonb,
            idempotency_key     VARCHAR(128)    UNIQUE,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            deleted_at          TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_appointments PRIMARY KEY (id)
        );
    """)

    # Core indexes on base table
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_tenant_clinic"
        " ON vitalia_appointments (tenant_id, clinic_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_tenant_clinic_doctor_slot"
        " ON vitalia_appointments (tenant_id, clinic_id, doctor_id, slot_iso);"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_patient ON vitalia_appointments (patient_id);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_tenant_clinic_status"
        " ON vitalia_appointments (tenant_id, clinic_id, status, created_at);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Slice 1 column additions — idempotent ADD COLUMN IF NOT EXISTS
    # ─────────────────────────────────────────────────────────────────────────

    # origin: sales_agent | walk_in | phone_manual | proactive_outbound
    op.execute(
        "ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS origin VARCHAR(32) NOT NULL DEFAULT 'sales_agent';"
    )

    # balance_status: pending | deposit_paid | full_paid | refunded
    op.execute(
        "ALTER TABLE vitalia_appointments"
        " ADD COLUMN IF NOT EXISTS balance_status VARCHAR(16) NOT NULL DEFAULT 'pending';"
    )

    op.execute("ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS follow_up_due_at TIMESTAMPTZ;")

    op.execute("ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS follow_up_reason TEXT;")

    op.execute("ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;")

    op.execute("ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS utm_source VARCHAR(64);")

    op.execute("ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS utm_campaign VARCHAR(128);")

    # Slice 1 operational indexes
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_tenant_clinic_origin"
        " ON vitalia_appointments (tenant_id, clinic_id, origin);"
    )
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vitalia_appointments_follow_up_due
          ON vitalia_appointments (tenant_id, clinic_id, follow_up_due_at)
          WHERE follow_up_due_at IS NOT NULL AND deleted_at IS NULL;
    """)


def downgrade() -> None:
    """Drop Slice 1 appointment columns and indexes (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_appointments_follow_up_due;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_appointments_tenant_clinic_origin;")
    op.execute("ALTER TABLE vitalia_appointments DROP COLUMN IF EXISTS utm_campaign;")
    op.execute("ALTER TABLE vitalia_appointments DROP COLUMN IF EXISTS utm_source;")
    op.execute("ALTER TABLE vitalia_appointments DROP COLUMN IF EXISTS completed_at;")
    op.execute("ALTER TABLE vitalia_appointments DROP COLUMN IF EXISTS follow_up_reason;")
    op.execute("ALTER TABLE vitalia_appointments DROP COLUMN IF EXISTS follow_up_due_at;")
    op.execute("ALTER TABLE vitalia_appointments DROP COLUMN IF EXISTS balance_status;")
    op.execute("ALTER TABLE vitalia_appointments DROP COLUMN IF EXISTS origin;")
    op.execute("DROP TABLE IF EXISTS vitalia_appointments;")
