"""F2-S1 Vitalia agenda: appointment_payments + fiscal_documents + clinic_map + growth_studio_event.

Story: vitalia-fase2-valeria-agenda
Ticket: T-1 — BE migration

Idempotent — uses IF NOT EXISTS / IF EXISTS. Safe to re-run.

Revision ID: 032_vitalia
Revises: 031_vitalia
Create Date: 2026-05-27

downstream-regression-na: brand-local scheduling tables; no engine modify.

Implementation note:
    03-arch § 3.4 assumes engine table named `appointments` (without brand prefix).
    In this deployment, the appointments table is `vitalia_appointments` (brand-local,
    with clinic_id already present per 030_slice1_marketing_appointments_utm.py).
    FK references adapted to `vitalia_appointments(id)` to match actual schema.
    Reported to /pm-vitalia for arch contract reconciliation.
"""

from __future__ import annotations

from alembic import op

revision = "032_vitalia"
down_revision = "031_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. vitalia_fiscal_documents                                         #
    # ------------------------------------------------------------------ #
    # Created FIRST — vitalia_appointment_payments has FK → fiscal_docs
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_fiscal_documents (
            id              UUID            PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id       UUID            NOT NULL,
            clinic_id       UUID            NOT NULL,
            appointment_payment_id UUID    NOT NULL,
            doc_type        VARCHAR(32)     NOT NULL,
            doc_number      VARCHAR(64),
            doc_url         VARCHAR(512),
            provider        VARCHAR(32)     NOT NULL,
            status          VARCHAR(16)     NOT NULL DEFAULT 'pending',
            error_message   VARCHAR(500),
            deleted_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ
        );
    """)
    # Composite index: tenant_id + clinic_id first (HIPAA-lite dual filter)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_fiscal_tenant_clinic ON vitalia_fiscal_documents (tenant_id, clinic_id);"
    )
    # Secondary index: payment FK lookup
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_fiscal_payment "
        "ON vitalia_fiscal_documents (tenant_id, clinic_id, appointment_payment_id);"
    )
    # Country-scoped lookup (for multi-country fiscal doc queries)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_fiscal_tenant_clinic_type "
        "ON vitalia_fiscal_documents (tenant_id, clinic_id, doc_type);"
    )

    # ------------------------------------------------------------------ #
    # 2. vitalia_appointment_payments (FK → fiscal_documents)             #
    # ------------------------------------------------------------------ #
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_appointment_payments (
            id                   UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id            UUID        NOT NULL,
            clinic_id            UUID        NOT NULL,
            appointment_id       UUID        NOT NULL,
            amount               INTEGER     NOT NULL,
            currency             VARCHAR(3)  NOT NULL,
            method               VARCHAR(32) NOT NULL,
            external_payment_id  VARCHAR(128),
            fiscal_doc_id        UUID        REFERENCES vitalia_fiscal_documents(id)
                                             ON DELETE SET NULL,
            notes                VARCHAR(500),
            balance_version      INTEGER     NOT NULL DEFAULT 1,
            created_by_user_id   UUID,
            deleted_at           TIMESTAMPTZ,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ,
            CONSTRAINT fk_vit_payment_appointment
                FOREIGN KEY (appointment_id)
                REFERENCES vitalia_appointments(id)
                ON DELETE RESTRICT
        );
    """)
    # Primary dual-filter composite index (tenant_id + clinic_id first per HIPAA-lite)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_payment_tenant_clinic_apt "
        "ON vitalia_appointment_payments (tenant_id, clinic_id, appointment_id);"
    )
    # Idempotency lookup: unique on (tenant_id, clinic_id, external_payment_id) where set
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_vit_payment_external "
        "ON vitalia_appointment_payments (tenant_id, clinic_id, external_payment_id) "
        "WHERE external_payment_id IS NOT NULL;"
    )

    # ------------------------------------------------------------------ #
    # 3. vitalia_appointment_clinic_map                                   #
    # ------------------------------------------------------------------ #
    # Brand-local extension for service_label + currency_override per appointment.
    # Note: vitalia_appointments already carries clinic_id; this table stores
    # additional brand-local fields (service_label, origin override, currency_override)
    # without modifying the core appointments record.
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_appointment_clinic_map (
            appointment_id  UUID        PRIMARY KEY
                                        REFERENCES vitalia_appointments(id)
                                        ON DELETE CASCADE,
            tenant_id       UUID        NOT NULL,
            clinic_id       UUID        NOT NULL,
            patient_id      UUID        NOT NULL,
            doctor_id       UUID        NOT NULL,
            service_label   VARCHAR(128) NOT NULL,
            origin          VARCHAR(32) NOT NULL,
            currency_override VARCHAR(3),
            deleted_at      TIMESTAMPTZ,
            created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    # Primary HIPAA-lite dual filter
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_apt_map_tenant_clinic "
        "ON vitalia_appointment_clinic_map (tenant_id, clinic_id);"
    )
    # Secondary indexes for join performance
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_apt_map_patient ON vitalia_appointment_clinic_map (patient_id);")
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_apt_map_doctor ON vitalia_appointment_clinic_map (doctor_id);")
    # Unique constraint: one map entry per appointment per tenant
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_vit_apt_map_tenant_apt "
        "ON vitalia_appointment_clinic_map (tenant_id, appointment_id);"
    )

    # ------------------------------------------------------------------ #
    # 4. vitalia_growth_studio_event (telemetry, brand-local)             #
    # ------------------------------------------------------------------ #
    # Separate from copilot_trace_event (engine, LLM cost concerns).
    # PHI-safe: props sanitized via sanitize_payload('hipaa_lite') before insert.
    # Fire-forget OK (not a mandatory sync write unlike audit_log).
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_growth_studio_event (
            id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id   UUID        NOT NULL,
            clinic_id   UUID,
            user_id     UUID,
            event_name  VARCHAR(64) NOT NULL,
            props       JSONB       NOT NULL DEFAULT '{}'::jsonb,
            occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)
    # Primary composite index: tenant + clinic + event for funnel queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_gse_tenant_clinic_event "
        "ON vitalia_growth_studio_event (tenant_id, clinic_id, event_name);"
    )
    # Time-range index for dashboard queries
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_gse_tenant_clinic_occurred "
        "ON vitalia_growth_studio_event (tenant_id, clinic_id, occurred_at);"
    )
    # Secondary time index for retention sweep
    op.execute("CREATE INDEX IF NOT EXISTS idx_vit_gse_occurred ON vitalia_growth_studio_event (occurred_at);")


def downgrade() -> None:
    # Drop in reverse FK order
    op.execute("DROP TABLE IF EXISTS vitalia_growth_studio_event;")
    op.execute("DROP TABLE IF EXISTS vitalia_appointment_clinic_map;")
    op.execute("DROP TABLE IF EXISTS vitalia_appointment_payments;")
    op.execute("DROP TABLE IF EXISTS vitalia_fiscal_documents;")
