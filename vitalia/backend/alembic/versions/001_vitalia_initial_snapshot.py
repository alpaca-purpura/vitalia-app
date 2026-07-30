"""Vitalia initial snapshot — all 11 tables idempotent (Story 11 T-be-1).

Single consolidated migration per Story 10 T-10 cement pattern.
Raw SQL IF NOT EXISTS everywhere — NEVER op.create_table() / sa.Enum(create_type=True).

Tables (11):
  vitalia_bookings                  — tenant-scoped, soft-delete
  vitalia_treatment_followups       — tenant-scoped, soft-delete
  vitalia_consent_records           — tenant-scoped, no deleted_at (legal record)
  vitalia_medical_audit_log         — tenant-scoped, IMMUTABLE (no deleted_at, 7-year retention)
  vitalia_payment_intents           — tenant-scoped, no deleted_at
  vitalia_payment_schedules         — tenant-scoped, no deleted_at
  vitalia_adherence_records         — tenant-scoped, no deleted_at
  vitalia_doctor_extensions         — tenant-scoped, soft-delete
  vitalia_patient_medical_histories — tenant-scoped, soft-delete
  vitalia_patient_dental_histories  — tenant-scoped, soft-delete
  vitalia_plan_tier_configs         — CROSS-TENANT (global catalog, no tenant_id)

Decisions honored: D1 (brand isolation independent chain), D7 (idempotent snapshot).

Revision ID: 001_vitalia
Revises: None  (independent vitalia alembic chain)
Create Date: 2026-05-14
"""
from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic.
revision = "001_vitalia"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all 11 vitalia tables idempotent — IF NOT EXISTS everywhere."""

    # ─────────────────────────────────────────────────────────────────────────
    # ENUM TYPES (idempotent via DO $$ BEGIN ... EXCEPTION WHEN duplicate_object)
    # NEVER sa.Enum(create_type=True) — broken SA 2.0.27
    # ─────────────────────────────────────────────────────────────────────────

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE vitalia_booking_status AS ENUM (
                'pending_payment',
                'awaiting_consent',
                'confirmed_deposit',
                'confirmed_full',
                'cancelled',
                'rescheduled',
                'completed'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE vitalia_payment_status AS ENUM (
                'not_initiated',
                'initiated',
                'processing',
                'succeeded',
                'failed',
                'refunded'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE vitalia_consent_status AS ENUM (
                'pending_signature',
                'signed',
                'expired',
                'revoked'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE vitalia_followup_step AS ENUM (
                'D0_init',
                'D5_check',
                'D14_check',
                'D30_check',
                'D90_check',
                'completed',
                'paused_no_response',
                'paused_safety_escalation',
                'paused_manual_handoff',
                'dropped'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE vitalia_audit_severity AS ENUM (
                'info',
                'medium',
                'high'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE vitalia_payment_gateway AS ENUM (
                'mercadopago',
                'stripe_connect',
                'tokenized_recurring'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TYPE vitalia_payment_schedule_status AS ENUM (
                'scheduled',
                'processing',
                'succeeded',
                'failed',
                'cancelled'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. vitalia_bookings
    #    Aggregate root for the booking flow. Tenant-scoped + soft-delete.
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_bookings (
            id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id           UUID            NOT NULL,
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
            CONSTRAINT pk_vitalia_bookings PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_bookings_tenant_id"
        " ON vitalia_bookings (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_bookings_tenant_doctor_slot"
        " ON vitalia_bookings (tenant_id, doctor_id, slot_iso);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_bookings_patient"
        " ON vitalia_bookings (patient_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_bookings_tenant_status_created"
        " ON vitalia_bookings (tenant_id, status, created_at);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 2. vitalia_treatment_followups
    #    LangGraph workflow state per (booking, patient, doctor). Soft-delete.
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_treatment_followups (
            id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID            NOT NULL,
            booking_id              UUID            NOT NULL,
            patient_id              UUID            NOT NULL,
            doctor_id               UUID            NOT NULL,
            plan_template_slug      VARCHAR(64)     NOT NULL,
            current_step            VARCHAR(32)     NOT NULL,
            started_at              TIMESTAMPTZ     NOT NULL,
            last_response_at        TIMESTAMPTZ,
            next_scheduled_at       TIMESTAMPTZ,
            adherence_score         INTEGER,
            paused_reason           VARCHAR(128),
            langgraph_checkpoint_id VARCHAR(128),
            created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            deleted_at              TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_treatment_followups PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_followups_tenant_id"
        " ON vitalia_treatment_followups (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_followups_booking"
        " ON vitalia_treatment_followups (booking_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_followups_tenant_patient"
        " ON vitalia_treatment_followups (tenant_id, patient_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_treatment_followups_tenant_step"
        " ON vitalia_treatment_followups (tenant_id, current_step);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 3. vitalia_consent_records
    #    Legal consent capture. No deleted_at — legal immutability preserved.
    #    (status=revoked used instead of soft-delete)
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_consent_records (
            id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID            NOT NULL,
            patient_id              UUID            NOT NULL,
            booking_id              UUID,
            consent_template_slug   VARCHAR(64)     NOT NULL,
            template_version        VARCHAR(16)     NOT NULL,
            template_snapshot_md    TEXT            NOT NULL,
            signed_name             VARCHAR(255),
            signed_ip               VARCHAR(45),
            signed_user_agent       VARCHAR(512),
            signed_at               TIMESTAMPTZ,
            signature_method        VARCHAR(32),
            status                  VARCHAR(32)     NOT NULL DEFAULT 'pending_signature',
            expires_at              TIMESTAMPTZ     NOT NULL,
            delivery_channels       JSONB           NOT NULL DEFAULT '[]'::jsonb,
            idempotency_key         VARCHAR(128),
            created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_consent_records PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_consent_records_tenant_id"
        " ON vitalia_consent_records (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_consent_records_tenant_patient"
        " ON vitalia_consent_records (tenant_id, patient_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_consent_records_booking"
        " ON vitalia_consent_records (booking_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_consent_records_tenant_status"
        " ON vitalia_consent_records (tenant_id, status);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 4. vitalia_medical_audit_log
    #    HIPAA-lite 7-year retention. IMMUTABLE — NO deleted_at, NO UPDATE.
    #    append-only; PII sanitized in payload_redacted.
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_medical_audit_log (
            id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id           UUID            NOT NULL,
            event_type          VARCHAR(64)     NOT NULL,
            severity            VARCHAR(16)     NOT NULL,
            patient_id          UUID,
            booking_id          UUID,
            payload_redacted    JSONB           NOT NULL DEFAULT '{}'::jsonb,
            actor_id            UUID,
            actor_type          VARCHAR(32),
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_medical_audit_log PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_medical_audit_log_tenant_id"
        " ON vitalia_medical_audit_log (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_audit_event_type"
        " ON vitalia_medical_audit_log (event_type);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_audit_tenant_event_created"
        " ON vitalia_medical_audit_log (tenant_id, event_type, created_at);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_audit_tenant_severity_created"
        " ON vitalia_medical_audit_log (tenant_id, severity, created_at);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 5. vitalia_payment_intents
    #    Per-booking payment intent. No deleted_at (financial record).
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_payment_intents (
            id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id           UUID            NOT NULL,
            booking_id          UUID            NOT NULL,
            gateway             VARCHAR(32)     NOT NULL,
            gateway_payment_id  VARCHAR(255)    UNIQUE,
            amount              NUMERIC(14, 2)  NOT NULL,
            currency            VARCHAR(3)      NOT NULL,
            status              VARCHAR(32)     NOT NULL,
            failure_reason      VARCHAR(255),
            payment_metadata    JSONB           NOT NULL DEFAULT '{}'::jsonb,
            idempotency_key     VARCHAR(128)    UNIQUE,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_payment_intents PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_payment_intents_tenant_id"
        " ON vitalia_payment_intents (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_payment_intents_booking"
        " ON vitalia_payment_intents (booking_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_payment_intents_tenant_status"
        " ON vitalia_payment_intents (tenant_id, status);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 6. vitalia_payment_schedules
    #    Recurring / installment plan per booking. No deleted_at (financial).
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_payment_schedules (
            id              UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id       UUID            NOT NULL,
            booking_id      UUID            NOT NULL,
            patient_id      UUID            NOT NULL,
            gateway         VARCHAR(32)     NOT NULL,
            installment_n   INTEGER         NOT NULL,
            scheduled_at    TIMESTAMPTZ     NOT NULL,
            amount          NUMERIC(14, 2)  NOT NULL,
            currency        VARCHAR(3)      NOT NULL,
            status          VARCHAR(32)     NOT NULL DEFAULT 'scheduled',
            payment_intent_id UUID,
            schedule_metadata JSONB         NOT NULL DEFAULT '{}'::jsonb,
            processed_at    TIMESTAMPTZ,
            failure_reason  VARCHAR(255),
            created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_payment_schedules PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_payment_schedules_tenant_id"
        " ON vitalia_payment_schedules (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_payment_schedules_booking"
        " ON vitalia_payment_schedules (booking_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_payment_schedules_tenant_status_scheduled"
        " ON vitalia_payment_schedules (tenant_id, status, scheduled_at);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 7. vitalia_adherence_records
    #    Per-step adherence metric for treatment followup. No deleted_at.
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_adherence_records (
            id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID            NOT NULL,
            treatment_followup_id   UUID            NOT NULL,
            patient_id              UUID            NOT NULL,
            step_name               VARCHAR(32)     NOT NULL,
            score                   INTEGER         NOT NULL,
            sentiment               VARCHAR(32),
            classifier_metadata     JSONB           NOT NULL DEFAULT '{}'::jsonb,
            recorded_at             TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_adherence_records PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_adherence_records_tenant_id"
        " ON vitalia_adherence_records (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_adherence_records_followup"
        " ON vitalia_adherence_records (treatment_followup_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_adherence_records_tenant_patient"
        " ON vitalia_adherence_records (tenant_id, patient_id);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 8. vitalia_doctor_extensions
    #    Medical extensions to doctor profile (Q4=A reuse @luana/core/scheduling).
    #    doctor_id unique per tenant. Soft-delete.
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_doctor_extensions (
            id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID            NOT NULL,
            doctor_id               UUID            NOT NULL,
            specialty               VARCHAR(64),
            treatment_room          VARCHAR(64),
            max_concurrent_per_slot INTEGER         NOT NULL DEFAULT 1,
            appointment_types       JSONB           NOT NULL DEFAULT '[]'::jsonb,
            available_offer_ids     JSONB           NOT NULL DEFAULT '[]'::jsonb,
            created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            deleted_at              TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_doctor_extensions PRIMARY KEY (id),
            CONSTRAINT uq_vitalia_doctor_extensions_doctor UNIQUE (tenant_id, doctor_id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_doctor_extensions_tenant_id"
        " ON vitalia_doctor_extensions (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_doctor_extensions_doctor"
        " ON vitalia_doctor_extensions (doctor_id);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 9. vitalia_patient_medical_histories
    #    LLM-extracted historia médica JSONB. Soft-delete.
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_patient_medical_histories (
            id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID            NOT NULL,
            patient_id              UUID            NOT NULL,
            extraction_confidence   NUMERIC(3, 2),
            extracted_payload       JSONB           NOT NULL DEFAULT '{}'::jsonb,
            extractor_version       VARCHAR(32),
            last_extracted_at       TIMESTAMPTZ,
            source_document_ids     JSONB           NOT NULL DEFAULT '[]'::jsonb,
            created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            deleted_at              TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_patient_medical_histories PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_patient_medical_histories_tenant_id"
        " ON vitalia_patient_medical_histories (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_patient_medical_histories_patient"
        " ON vitalia_patient_medical_histories (tenant_id, patient_id);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 10. vitalia_patient_dental_histories
    #     Dental-specific extracted history. Soft-delete.
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_patient_dental_histories (
            id                      UUID            NOT NULL DEFAULT gen_random_uuid(),
            tenant_id               UUID            NOT NULL,
            patient_id              UUID            NOT NULL,
            missing_pieces_fdi      JSONB           NOT NULL DEFAULT '[]'::jsonb,
            restorations            JSONB           NOT NULL DEFAULT '{}'::jsonb,
            extraction_confidence   NUMERIC(3, 2),
            extracted_payload       JSONB           NOT NULL DEFAULT '{}'::jsonb,
            extractor_version       VARCHAR(32),
            last_extracted_at       TIMESTAMPTZ,
            source_document_ids     JSONB           NOT NULL DEFAULT '[]'::jsonb,
            created_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at              TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            deleted_at              TIMESTAMPTZ,
            CONSTRAINT pk_vitalia_patient_dental_histories PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_patient_dental_histories_tenant_id"
        " ON vitalia_patient_dental_histories (tenant_id);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_patient_dental_histories_patient"
        " ON vitalia_patient_dental_histories (tenant_id, patient_id);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # 11. vitalia_plan_tier_configs
    #     CROSS-TENANT global catalog — NO tenant_id, NO deleted_at.
    #     Managed by platform ops; read-only for tenant services.
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_plan_tier_configs (
            id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
            plan_tier_slug      VARCHAR(64)     NOT NULL UNIQUE,
            display_name        VARCHAR(128)    NOT NULL,
            price_usd_monthly   NUMERIC(10, 2)  NOT NULL,
            included_user_count INTEGER         NOT NULL DEFAULT 1,
            max_doctors         INTEGER         NOT NULL DEFAULT 1,
            features_enabled    JSONB           NOT NULL DEFAULT '{}'::jsonb,
            is_active           BOOLEAN         NOT NULL DEFAULT TRUE,
            created_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_plan_tier_configs PRIMARY KEY (id)
        );
    """)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_plan_tier_configs_slug"
        " ON vitalia_plan_tier_configs (plan_tier_slug);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_plan_tier_configs_active"
        " ON vitalia_plan_tier_configs (is_active);"
    )

    # ─────────────────────────────────────────────────────────────────────────
    # Seed plan tier catalog (idempotent via ON CONFLICT DO NOTHING)
    # ─────────────────────────────────────────────────────────────────────────
    # Seed plan tiers as separate idempotent upserts to avoid long lines.
    # Use jsonb_build_object() to avoid `:true` being parsed as a SQLAlchemy
    # named bind parameter when op.execute() wraps the string in text().
    op.execute(
        "INSERT INTO vitalia_plan_tier_configs"
        " (plan_tier_slug, display_name, price_usd_monthly,"
        "  included_user_count, max_doctors, features_enabled)"
        " VALUES ('solo_doctor', 'Solo Doctor', 49.00, 1, 1,"
        "  jsonb_build_object("
        "   'brand_studio_simplified', true,"
        "   'offer_studio_medical', true,"
        "   'booking_prepaid', true,"
        "   'sales_agent_vertical_medical', true"
        "  ))"
        " ON CONFLICT (plan_tier_slug) DO NOTHING"
    )
    op.execute(
        "INSERT INTO vitalia_plan_tier_configs"
        " (plan_tier_slug, display_name, price_usd_monthly,"
        "  included_user_count, max_doctors, features_enabled)"
        " VALUES ('clinic', 'Clinic', 199.00, 10, 10,"
        "  jsonb_build_object("
        "   'brand_studio_simplified', true,"
        "   'offer_studio_medical', true,"
        "   'booking_prepaid', true,"
        "   'sales_agent_vertical_medical', true,"
        "   'copilot_medical_extractors', true,"
        "   'treatment_followup_workflow', true"
        "  ))"
        " ON CONFLICT (plan_tier_slug) DO NOTHING"
    )
    op.execute(
        "INSERT INTO vitalia_plan_tier_configs"
        " (plan_tier_slug, display_name, price_usd_monthly,"
        "  included_user_count, max_doctors, features_enabled)"
        " VALUES ('multi_site', 'Multi Site', 599.00, 50, 50,"
        "  jsonb_build_object("
        "   'all_clinic_features', true,"
        "   'multi_site_backend', true,"
        "   'multi_currency', true"
        "  ))"
        " ON CONFLICT (plan_tier_slug) DO NOTHING"
    )


def downgrade() -> None:
    """Rollback all vitalia tables — for dev iteration only.

    Production uses snapshot rebuild, not downgrade. Enum types dropped after
    tables to avoid FK/dependency errors. Reverse dependency order.
    """
    # Drop tables in reverse dependency order
    op.execute("DROP TABLE IF EXISTS vitalia_plan_tier_configs;")
    op.execute("DROP TABLE IF EXISTS vitalia_patient_dental_histories;")
    op.execute("DROP TABLE IF EXISTS vitalia_patient_medical_histories;")
    op.execute("DROP TABLE IF EXISTS vitalia_doctor_extensions;")
    op.execute("DROP TABLE IF EXISTS vitalia_adherence_records;")
    op.execute("DROP TABLE IF EXISTS vitalia_payment_schedules;")
    op.execute("DROP TABLE IF EXISTS vitalia_payment_intents;")
    op.execute("DROP TABLE IF EXISTS vitalia_medical_audit_log;")
    op.execute("DROP TABLE IF EXISTS vitalia_consent_records;")
    op.execute("DROP TABLE IF EXISTS vitalia_treatment_followups;")
    op.execute("DROP TABLE IF EXISTS vitalia_bookings;")

    # Drop enum types
    op.execute("DROP TYPE IF EXISTS vitalia_payment_schedule_status;")
    op.execute("DROP TYPE IF EXISTS vitalia_payment_gateway;")
    op.execute("DROP TYPE IF EXISTS vitalia_audit_severity;")
    op.execute("DROP TYPE IF EXISTS vitalia_followup_step;")
    op.execute("DROP TYPE IF EXISTS vitalia_consent_status;")
    op.execute("DROP TYPE IF EXISTS vitalia_payment_status;")
    op.execute("DROP TYPE IF EXISTS vitalia_booking_status;")
