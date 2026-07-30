"""Vitalia fiscal receipts table — Capa 2 fiscal emission (Nubefact PE Slice 1).

Stores fiscal documents emitted per payment event. Supports PE provider
(boleta/factura via Nubefact) in Slice 1; extensible to MX/CO/AR/CL in
Slice 2/3 via provider column.

Status lifecycle: pending -> submitted -> accepted | rejected | retrying.
retry_count + last_error support async retry queue.

All DDL idempotent via IF NOT EXISTS.

Revision ID: 004_vitalia
Revises: 003_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "004_vitalia"
down_revision = "003_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_fiscal_receipts table idempotent."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_fiscal_receipts (
            id                      UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID        NOT NULL,
            clinic_id               UUID        NOT NULL,
            payment_event_id        UUID        NOT NULL,
            provider                VARCHAR(32) NOT NULL,
            fiscal_doc_type         VARCHAR(16) NOT NULL,
            fiscal_serial           VARCHAR(16) NOT NULL,
            fiscal_number           VARCHAR(32) NOT NULL,
            fiscal_url              TEXT,
            cdr_xml_archived_at     TIMESTAMPTZ,
            status                  VARCHAR(16) NOT NULL DEFAULT 'pending',
            retry_count             INTEGER     NOT NULL DEFAULT 0,
            last_error              TEXT,
            submitted_at            TIMESTAMPTZ,
            created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at              TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_fiscal_receipts PRIMARY KEY (id)
        );
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_fiscal_receipts_serial_number
          ON vitalia_fiscal_receipts (tenant_id, clinic_id, fiscal_serial, fiscal_number);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vitalia_fiscal_receipts_status
          ON vitalia_fiscal_receipts (status, retry_count)
          WHERE status IN ('pending', 'retrying');
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_fiscal_receipts_payment_event"
        " ON vitalia_fiscal_receipts (payment_event_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_fiscal_receipts_tenant_clinic"
        " ON vitalia_fiscal_receipts (tenant_id, clinic_id);"
    )


def downgrade() -> None:
    """Drop vitalia_fiscal_receipts (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_fiscal_receipts_tenant_clinic;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_fiscal_receipts_payment_event;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_fiscal_receipts_status;")
    op.execute("DROP INDEX IF EXISTS uq_vitalia_fiscal_receipts_serial_number;")
    op.execute("DROP TABLE IF EXISTS vitalia_fiscal_receipts;")
