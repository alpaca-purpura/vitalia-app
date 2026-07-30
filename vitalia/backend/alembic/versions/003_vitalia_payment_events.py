"""Vitalia payment events table — Slice 1 agenda payment capture.

Records per-appointment payment events for the 3-layer billing system:
Layer 1 (internal receipt VLT-{year}-{seq}), Layer 2 (fiscal emission),
Layer 3 (PDF window.print). PHI: references vitalia_appointments but the
table itself is financial-immutable (no deleted_at on core records;
soft-delete added for safety during dev iteration).

All DDL idempotent via IF NOT EXISTS.

Revision ID: 003_vitalia
Revises: 002_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "003_vitalia"
down_revision = "002_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_payment_events table idempotent."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_payment_events (
            id                      UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID        NOT NULL,
            clinic_id               UUID        NOT NULL,
            appointment_id          UUID        NOT NULL,
            provider                VARCHAR(32) NOT NULL,
            provider_payment_id     VARCHAR(128),
            amount_cents            BIGINT      NOT NULL,
            currency                CHAR(3)     NOT NULL,
            status                  VARCHAR(16) NOT NULL,
            is_deposit              BOOLEAN     NOT NULL DEFAULT FALSE,
            deposit_percent         INTEGER,
            receipt_number          VARCHAR(64),
            audit_log_id            UUID,
            payload                 JSONB       NOT NULL DEFAULT '{}'::jsonb,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at              TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_payment_events PRIMARY KEY (id)
        );
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_payment_events_tenant_clinic_appt"
        " ON vitalia_payment_events (tenant_id, clinic_id, appointment_id);"
    )
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_payment_events_provider
          ON vitalia_payment_events (provider, provider_payment_id)
          WHERE provider_payment_id IS NOT NULL;
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_payment_events_tenant_clinic_status"
        " ON vitalia_payment_events (tenant_id, clinic_id, status);"
    )


def downgrade() -> None:
    """Drop vitalia_payment_events (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_payment_events_tenant_clinic_status;")
    op.execute("DROP INDEX IF EXISTS uq_vitalia_payment_events_provider;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_payment_events_tenant_clinic_appt;")
    op.execute("DROP TABLE IF EXISTS vitalia_payment_events;")
