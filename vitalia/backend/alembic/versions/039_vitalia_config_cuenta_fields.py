r"""Migration 039: vitalia_clinic_branches — account/fiscal identity fields.

Story: vitalia-fase2-config-cuenta · release F3.
Ticket: T-2 (BE config-cuenta: campos cuenta Clinic + fiscal/specialty validators).
cap: configuracion.cuenta

Idempotency: ALL DDL uses IF NOT EXISTS. Safe to re-run.

Changes:
  1. ADD COLUMN IF NOT EXISTS legal_name VARCHAR on vitalia_clinic_branches
  2. ADD COLUMN IF NOT EXISTS fiscal_id VARCHAR on vitalia_clinic_branches
  3. ADD COLUMN IF NOT EXISTS address VARCHAR on vitalia_clinic_branches
  4. ADD COLUMN IF NOT EXISTS phone VARCHAR on vitalia_clinic_branches
  5. ADD COLUMN IF NOT EXISTS email VARCHAR on vitalia_clinic_branches
  6. ADD COLUMN IF NOT EXISTS language VARCHAR DEFAULT 'es-419' on vitalia_clinic_branches
  7. ADD COLUMN IF NOT EXISTS currency VARCHAR(3) on vitalia_clinic_branches

NEVER use:
  - op.create_table() / op.add_column() (non-idempotent)
  - sa.Enum(create_type=True) (broken SA 2.0.27)

Revision ID: 039_vitalia
Revises: 038_vitalia
Create Date: 2026-06-11
"""

from __future__ import annotations

from alembic import op

revision = "039_vitalia"
down_revision = "038_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add fiscal identity + locale fields to vitalia_clinic_branches."""

    # 1. Razón social / nombre legal
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS legal_name VARCHAR")

    # 2. ID fiscal (CUIT/RUC/RFC/NIT/RUT — format varies by country)
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS fiscal_id VARCHAR")

    # 3. Dirección fiscal o de atención
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS address VARCHAR")

    # 4. Teléfono de contacto
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS phone VARCHAR")

    # 5. Email de contacto de la clínica (NOT patient PHI — clinic identity)
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS email VARCHAR")

    # 6. Locale preferido (IETF BCP 47 — default es-419 pan-LatAm neutral)
    op.execute(
        "ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS language VARCHAR NOT NULL DEFAULT 'es-419'"
    )

    # 7. Moneda ISO 4217 preferida (NULL = usa moneda del país del tenant)
    op.execute("ALTER TABLE vitalia_clinic_branches ADD COLUMN IF NOT EXISTS currency VARCHAR(3)")


def downgrade() -> None:
    """Remove account fields from vitalia_clinic_branches (destructive — data loss)."""
    op.execute("ALTER TABLE vitalia_clinic_branches DROP COLUMN IF EXISTS currency")
    op.execute("ALTER TABLE vitalia_clinic_branches DROP COLUMN IF EXISTS language")
    op.execute("ALTER TABLE vitalia_clinic_branches DROP COLUMN IF EXISTS email")
    op.execute("ALTER TABLE vitalia_clinic_branches DROP COLUMN IF EXISTS phone")
    op.execute("ALTER TABLE vitalia_clinic_branches DROP COLUMN IF EXISTS address")
    op.execute("ALTER TABLE vitalia_clinic_branches DROP COLUMN IF EXISTS fiscal_id")
    op.execute("ALTER TABLE vitalia_clinic_branches DROP COLUMN IF EXISTS legal_name")
