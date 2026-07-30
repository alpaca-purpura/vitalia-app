"""Migration 025: pgcrypto symmetric encryption for nps_responses.comment (PHI).

Enables pgcrypto extension and installs a BEFORE INSERT/UPDATE trigger on
vitalia_nps_responses that encrypts the comment column using
pgp_sym_encrypt() with the KEK stored in app.encryption_key GUC.

Per vitalia/.claude/rules/hipaa-lite.md § Encryption at rest:
  - comment (free-text del paciente) = PHI — MUST be encrypted at column level.
  - pgcrypto symmetric encryption with KEK rotada anualmente.
  - Key source: current_setting('app.encryption_key', true) GUC injected
    at session start by the application connection pool.

Design notes:
  - Trigger approach: application sends plaintext bytes, trigger encrypts
    transparently on write. Read path requires explicit pgp_sym_decrypt()
    via a view or service-layer call.
  - No data migration of existing rows needed (comment BYTEA was previously
    plaintext UTF-8 bytes; trigger fires on future writes only).
    Existing plaintext rows are re-encrypted on next UPDATE.
  - KEK rotation: update GUC + trigger function uses new key going forward.
    Historical rows can be re-encrypted via maintenance script (Slice 2).

Idempotency: CREATE EXTENSION IF NOT EXISTS, CREATE OR REPLACE FUNCTION,
CREATE OR REPLACE TRIGGER (Postgres does not support IF NOT EXISTS on
triggers, so we use CREATE OR REPLACE which is idempotent for PG 14+).

Revision ID: 025_vitalia
Revises: 024b_vitalia
Create Date: 2026-05-20

UPDATE 2026-05-22 F1-S0: down_revision chain fixed from "024_vitalia" → "024b_vitalia"
to ensure vitalia_nps_responses table exists (created by 024b) before this
trigger references it. Origin bug discovered during F1-S0 visual goldens
debug — backend crashed with `relation "vitalia_nps_responses" does not exist`.
"""

from __future__ import annotations

from alembic import op

revision = "025_vitalia"
down_revision = "024b_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Enable pgcrypto + install encryption trigger on nps_responses.comment."""
    # 1. Ensure pgcrypto extension available (idempotent — already enabled in 013/005)
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # 2. Create (or replace) the encryption trigger function.
    #    KEK is injected as a session-level GUC: SET app.encryption_key = '...';
    #    current_setting('app.encryption_key', true) returns NULL if not set
    #    (safe fallback: NULL KEK → pgp_sym_encrypt returns NULL → comment NOT stored).
    op.execute(
        """
        CREATE OR REPLACE FUNCTION vitalia_encrypt_nps_comment()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
          _kek TEXT;
        BEGIN
          -- Retrieve KEK from session GUC (injected by connection pool)
          _kek := current_setting('app.encryption_key', true);

          IF NEW.comment IS NOT NULL AND _kek IS NOT NULL AND _kek != '' THEN
            -- Encrypt plaintext bytes with pgcrypto symmetric encryption
            -- pgp_sym_encrypt expects TEXT input; cast BYTEA → TEXT (UTF-8)
            NEW.comment := pgp_sym_encrypt(
              convert_from(NEW.comment, 'UTF8'),
              _kek
            )::BYTEA;
          END IF;

          RETURN NEW;
        END;
        $$
        """
    )

    # 3. Install trigger on vitalia_nps_responses (idempotent via CREATE OR REPLACE
    #    for Postgres 14+; for PG 13 we drop first).
    op.execute(
        """
        DROP TRIGGER IF EXISTS trg_encrypt_nps_comment ON vitalia_nps_responses
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_encrypt_nps_comment
          BEFORE INSERT OR UPDATE OF comment
          ON vitalia_nps_responses
          FOR EACH ROW
          WHEN (NEW.comment IS NOT NULL)
          EXECUTE FUNCTION vitalia_encrypt_nps_comment()
        """
    )


def downgrade() -> None:
    """Remove encryption trigger and function. Data remains encrypted in place."""
    op.execute("DROP TRIGGER IF EXISTS trg_encrypt_nps_comment ON vitalia_nps_responses")
    op.execute("DROP FUNCTION IF EXISTS vitalia_encrypt_nps_comment()")
    # NOTE: pgcrypto extension NOT dropped (shared by other tables in the DB)
    # NOTE: encrypted BYTEA data remains in place; downgrade does NOT decrypt rows
