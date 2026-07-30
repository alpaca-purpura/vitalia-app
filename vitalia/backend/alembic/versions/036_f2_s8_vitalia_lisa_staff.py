# cap: clinics.lisa.doctores
"""Migration 036 — F2-S8 vitalia_lisa_staff: doctors + availability.

Creates 3 tables (idempotent — all DDL uses IF NOT EXISTS):
  1. vitalia_doctors: doctor profiles with pgcrypto-encrypted PII columns
  2. vitalia_availability_blocks: recurrence blocks per doctor
  3. vitalia_availability_slots: materialized slots from block expansion

Down-revision: 035 (vitalia_crm_phi_base_tables)

Idempotency guaranteed per .claude/rules/backend-migrations.md:
  - All CREATE TABLE use IF NOT EXISTS
  - All ALTER TABLE ADD COLUMN use IF NOT EXISTS
  - All CREATE INDEX use IF NOT EXISTS
  - No op.create_table() / op.add_column() (non-idempotent)
  - No sa.Enum(create_type=True) (broken in SA 2.0.27)
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic
revision = "036_vitalia"
down_revision = "035_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_doctors + vitalia_availability_blocks + vitalia_availability_slots."""

    # ── 1. vitalia_doctors ────────────────────────────────────────────────────
    # PII columns: dni_encrypted, email_encrypted, phone_encrypted, credential_encrypted
    # stored as BYTEA (pgcrypto pgp_sym_encrypt output).
    # dni_hash: HMAC-SHA256(dni, KEK) — for unique constraint (not reversible plaintext).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_doctors (
            id                   UUID         NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
            tenant_id            UUID         NOT NULL,
            clinic_id            UUID         NOT NULL,
            first_name           VARCHAR(128) NOT NULL,
            last_name            VARCHAR(128) NOT NULL,
            dni_encrypted        BYTEA,
            email_encrypted      BYTEA,
            phone_encrypted      BYTEA,
            credential_encrypted BYTEA,
            dni_hash             VARCHAR(64),
            specialty            VARCHAR(128),
            credential_country   VARCHAR(2)   NOT NULL,
            years_experience     INTEGER,
            languages            JSONB        NOT NULL DEFAULT '[]'::jsonb,
            bio_inputs_notes     TEXT,
            bio_links            JSONB        NOT NULL DEFAULT '[]'::jsonb,
            bio_public           JSONB,
            avatar_key           VARCHAR(512),
            visible_en_landing   BOOLEAN      NOT NULL DEFAULT FALSE,
            active               BOOLEAN      NOT NULL DEFAULT TRUE,
            created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
            updated_at           TIMESTAMPTZ,
            deleted_at           TIMESTAMPTZ
        )
        """
    )

    # Unique constraint: one DNI hash per tenant (prevents DNI duplication across clinics)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'uq_vitalia_doctors_tenant_dni'
            ) THEN
                ALTER TABLE vitalia_doctors
                    ADD CONSTRAINT uq_vitalia_doctors_tenant_dni
                    UNIQUE (tenant_id, dni_hash);
            END IF;
        END;
        $$;
        """
    )

    # Indexes for common query patterns
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_doctors_tenant_id ON vitalia_doctors (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_doctors_clinic_id ON vitalia_doctors (clinic_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_doctors_tenant_clinic ON vitalia_doctors (tenant_id, clinic_id)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_doctors_tenant_specialty ON vitalia_doctors (tenant_id, specialty)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_doctors_tenant_active ON vitalia_doctors (tenant_id, active)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_doctors_tenant_visible_active "
        "ON vitalia_doctors (tenant_id, visible_en_landing, active)"
    )

    # ── 2. vitalia_availability_blocks ────────────────────────────────────────
    # Recurrence pattern (weekly/biweekly) or one-off date.
    # end_condition_kind: 'end_date' | 'occurrences' | 'open_ended'
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_availability_blocks (
            id                  UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
            tenant_id           UUID        NOT NULL,
            clinic_id           UUID        NOT NULL,
            doctor_id           UUID        NOT NULL,
            kind                VARCHAR(16) NOT NULL,
            day_of_week         INTEGER,
            start_time          TIME        NOT NULL,
            end_time            TIME        NOT NULL,
            freq                VARCHAR(16),
            end_condition_kind  VARCHAR(16),
            end_date            DATE,
            occurrences         INTEGER,
            specific_date       DATE,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ,
            deleted_at          TIMESTAMPTZ
        )
        """
    )

    # FK doctor_id → vitalia_doctors.id (add only if not exists)
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_availability_blocks_doctor_id'
            ) THEN
                ALTER TABLE vitalia_availability_blocks
                    ADD CONSTRAINT fk_availability_blocks_doctor_id
                    FOREIGN KEY (doctor_id) REFERENCES vitalia_doctors(id);
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_availability_blocks_tenant_id ON vitalia_availability_blocks (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_availability_blocks_clinic_id ON vitalia_availability_blocks (clinic_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_availability_blocks_doctor_id ON vitalia_availability_blocks (doctor_id)"
    )

    # ── 3. vitalia_availability_slots ─────────────────────────────────────────
    # Materialized slots projected from blocks via AvailabilityProjectionService.
    # has_confirmed_appointment: TRUE prevents deletion (preserve SC-3b, SC-1d).
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_availability_slots (
            id                        UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
            tenant_id                 UUID        NOT NULL,
            clinic_id                 UUID        NOT NULL,
            doctor_id                 UUID        NOT NULL,
            block_id                  UUID,
            slot_date                 DATE        NOT NULL,
            start_ts                  TIMESTAMPTZ NOT NULL,
            end_ts                    TIMESTAMPTZ NOT NULL,
            has_confirmed_appointment BOOLEAN     NOT NULL DEFAULT FALSE,
            created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at                TIMESTAMPTZ,
            deleted_at                TIMESTAMPTZ
        )
        """
    )

    # FK block_id → vitalia_availability_blocks.id ON DELETE CASCADE
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'fk_availability_slots_block_id'
            ) THEN
                ALTER TABLE vitalia_availability_slots
                    ADD CONSTRAINT fk_availability_slots_block_id
                    FOREIGN KEY (block_id)
                    REFERENCES vitalia_availability_blocks(id)
                    ON DELETE CASCADE;
            END IF;
        END;
        $$;
        """
    )

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_availability_slots_tenant_id ON vitalia_availability_slots (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_availability_slots_clinic_id ON vitalia_availability_slots (clinic_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_availability_slots_doctor_id ON vitalia_availability_slots (doctor_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_availability_slots_block_id ON vitalia_availability_slots (block_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_availability_slots_tenant_doctor_date "
        "ON vitalia_availability_slots (tenant_id, doctor_id, slot_date)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_availability_slots_slot_date ON vitalia_availability_slots (slot_date)"
    )


def downgrade() -> None:
    """Drop tables in reverse dependency order."""
    op.execute("DROP TABLE IF EXISTS vitalia_availability_slots CASCADE")
    op.execute("DROP TABLE IF EXISTS vitalia_availability_blocks CASCADE")
    op.execute("DROP TABLE IF EXISTS vitalia_doctors CASCADE")
