"""Migration 035: CRM PHI base tables — vitalia_leads (net-new) + vitalia_patients reconcile.

Story: vitalia-crm-phi-base-tables-migration · service-story · release F2.
ADR: ADR-vitalia-007-phi-pgcrypto-encryption.

Creates vitalia_leads (net-new) and reconciles vitalia_patients by adding PHI
columns (BYTEA, pgcrypto-encrypted at rest) per hipaa-lite.md § Encryption at rest.

Design decisions:
  - Inline pgp_sym_encrypt/decrypt at repo layer (NOT trigger+GUC from 025, which
    is broken at runtime: KEK never injected). KEK bound via :kek param at query time.
  - Columns encrypted: patients.name/date_of_birth/dni/phone/email/address;
    leads.name/email/phone/notes.
  - marketing_opt_out_at is TIMESTAMPTZ (metadata, NOT encrypted — ADR-007 D3).
  - NO indexes on ciphertext columns (ADR-007 D4 — blind index = follow-up).
  - Drift fix: DB dev is stamped at 034 but vitalia_patients does NOT exist
    physically (016 was never applied against the current DB). Therefore this
    migration opens with CREATE TABLE IF NOT EXISTS vitalia_patients (...) with
    the FULL 016 skeleton, then ADD COLUMN IF NOT EXISTS for the PHI BYTEA cols.
    On a clean DB (future), 016 creates the skeleton and 035 only adds PHI — both
    paths converge idempotently via IF NOT EXISTS.

Idempotency: all DDL uses IF NOT EXISTS / IF EXISTS. Safe to re-run.

upgrade() order:
  1. CREATE EXTENSION IF NOT EXISTS pgcrypto
  2. CREATE TABLE IF NOT EXISTS vitalia_patients (full 016 skeleton)
  3. ADD COLUMN IF NOT EXISTS PHI BYTEA cols on vitalia_patients
  4. CREATE TABLE IF NOT EXISTS vitalia_leads (net-new, PHI BYTEA)
  5. CREATE INDEX IF NOT EXISTS (plaintext cols only)

downgrade() (ADR-007 D5):
  - DROP TABLE IF EXISTS vitalia_leads
  - DROP COLUMN IF EXISTS {PHI cols} on vitalia_patients
  - DO NOT drop vitalia_patients (owned by 016)
  - DO NOT drop extension pgcrypto (shared by other tables)

Revision ID: 035_vitalia
Revises: 034_vitalia
Create Date: 2026-05-30
"""

from __future__ import annotations

from alembic import op

revision = "035_vitalia"
down_revision = "034_vitalia"
branch_labels = None
depends_on = None

# PHI columns added to vitalia_patients by this migration (BYTEA, cifrado pgcrypto)
_PATIENTS_PHI_COLS = [
    "name",
    "date_of_birth",
    "dni",
    "phone",
    "email",
    "address",
    "marketing_opt_out_at",  # TIMESTAMPTZ — metadata, NOT BYTEA
]


def upgrade() -> None:
    """Create vitalia_leads + reconcile vitalia_patients with PHI BYTEA columns."""

    # 1. Enable pgcrypto (idempotent — already in 013/005/025)
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # 2. Reconstruct vitalia_patients skeleton (016 pattern) for drifted DBs.
    #    In a clean DB this is a no-op (016 already ran). In the current dev DB
    #    (stamped 034, 016 never applied), this creates the table from scratch.
    #    All columns from 016 + flags are included so both paths converge.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_patients (
            id               UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id        UUID        NOT NULL,
            clinic_id        UUID        NOT NULL,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at       TIMESTAMPTZ,
            marketing_opt_in BOOLEAN     NOT NULL DEFAULT FALSE,
            opt_out          BOOLEAN     NOT NULL DEFAULT FALSE,
            opt_out_reason   TEXT,
            opt_out_at       TIMESTAMPTZ,
            PRIMARY KEY (id)
        )
        """
    )

    # 3a. Add PHI BYTEA columns (encrypted at rest via pgp_sym_encrypt at repo layer)
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS name BYTEA")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS date_of_birth BYTEA")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS dni BYTEA")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS phone BYTEA")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS email BYTEA")
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS address BYTEA")

    # 3b. marketing_opt_out_at — metadata TIMESTAMPTZ (NOT encrypted — ADR-007 D3)
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS marketing_opt_out_at TIMESTAMPTZ")

    # 4. Create vitalia_leads (net-new) with PHI/PII BYTEA columns
    #    PK: id UUID gen_random_uuid()
    #    PHI/PII encrypted: name, email, phone, notes (BYTEA)
    #    Plaintext searchable: source, status, deleted_at, timestamps
    #    marketing_opt_in: BOOLEAN (lead consent flag — plaintext)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_leads (
            id               UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id        UUID        NOT NULL,
            name             BYTEA,
            email            BYTEA,
            phone            BYTEA,
            source           TEXT,
            status           TEXT        NOT NULL DEFAULT 'new',
            notes            BYTEA,
            marketing_opt_in BOOLEAN     NOT NULL DEFAULT FALSE,
            deleted_at       TIMESTAMPTZ,
            created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id)
        )
        """
    )

    # 5. Indexes — ONLY on plaintext columns (ADR-007 D4: NO index on ciphertext)
    # patients: tenant+clinic composite (016 may have created this; IF NOT EXISTS = safe)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_patients_tenant_clinic
        ON vitalia_patients (tenant_id, clinic_id)
        """
    )

    # leads: tenant (single) + tenant+status (partial, active rows)
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_leads_tenant ON vitalia_leads (tenant_id)")
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_leads_tenant_status
        ON vitalia_leads (tenant_id, status)
        WHERE deleted_at IS NULL
        """
    )


def downgrade() -> None:
    """Remove vitalia_leads + PHI BYTEA columns added by this migration.

    Per ADR-007 D5:
      - DROP TABLE IF EXISTS vitalia_leads (net-new by 035)
      - DROP COLUMN IF EXISTS PHI cols on vitalia_patients
      - DO NOT drop vitalia_patients (016 owns it)
      - DO NOT drop extension pgcrypto (shared by nps_responses, other tables)
    """
    # Drop leads table (created by this migration)
    op.execute("DROP TABLE IF EXISTS vitalia_leads")

    # Remove PHI BYTEA columns added by this migration from vitalia_patients
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS marketing_opt_out_at")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS address")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS email")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS phone")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS dni")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS date_of_birth")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS name")

    # NOTE: vitalia_patients is NOT dropped (owned by 016_vitalia_patients_columns.py)
    # NOTE: pgcrypto extension is NOT dropped (shared by nps_responses + other tables)
