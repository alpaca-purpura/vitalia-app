# cap: clinics.lisa.doctores
"""Migration 041 — delta v3 D3-D: doctor public profile columns.

Adds 3 columns to vitalia_doctors (idempotent raw SQL — IF NOT EXISTS):
  public_profile   JSONB        — structured 6-section public profile
  bio_generated_at TIMESTAMPTZ  — timestamp of last profile generation
  public_slug      TEXT         — URL-safe slug for public doctor page

Also adds unique index on (tenant_id, clinic_id, public_slug) for fast slug lookup.

Backfill: sets public_profile = bio_public WHERE bio_public IS NOT NULL AND
public_profile IS NULL (one-time idempotent — WHERE public_profile IS NULL guard).

Down-revision: 040_vitalia (doctor_bio_files).
Note: 042 (block_multi_day_interval) references 040 directly and is independent.
Story: vitalia-fase2-lisa-doctores · T-BE-pagina-publica.

Per .claude/rules/backend-migrations.md:
  - Raw SQL IF NOT EXISTS — NEVER op.add_column() / op.create_table() / sa.Enum(create_type=True)
  - Downgrade: DROP ... IF EXISTS (idempotent both ways)
  - Clone test: re-upgrade must be a no-op

downstream-regression-na: brand-local vitalia migration (no cross-brand consumers).
"""

from __future__ import annotations

from alembic import op

revision = "041_vitalia"
down_revision = "040_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add public_profile, bio_generated_at, public_slug to vitalia_doctors.

    All DDL is idempotent via IF NOT EXISTS.
    """
    # Add public_profile JSONB column
    op.execute(
        """
        ALTER TABLE vitalia_doctors
        ADD COLUMN IF NOT EXISTS public_profile JSONB
        """
    )

    # Add bio_generated_at TIMESTAMPTZ column
    op.execute(
        """
        ALTER TABLE vitalia_doctors
        ADD COLUMN IF NOT EXISTS bio_generated_at TIMESTAMPTZ
        """
    )

    # Add public_slug TEXT column
    op.execute(
        """
        ALTER TABLE vitalia_doctors
        ADD COLUMN IF NOT EXISTS public_slug TEXT
        """
    )

    # Create unique index on (tenant_id, clinic_id, public_slug) — guards slug uniqueness per clinic.
    # Partial index: WHERE public_slug IS NOT NULL (allows NULL slugs before assignment).
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS
          ix_vitalia_doctors_tenant_clinic_slug
        ON vitalia_doctors (tenant_id, clinic_id, public_slug)
        WHERE public_slug IS NOT NULL
        """
    )

    # Backfill: copy bio_public → public_profile for doctors that have bio_public
    # but no public_profile yet. One-time, idempotent (WHERE public_profile IS NULL guard).
    # This preserves legacy bio_public data in the new structured column as a flat blob.
    # The structured sections will be populated on next bio generation (RN-D3B-4).
    op.execute(
        """
        UPDATE vitalia_doctors
        SET public_profile = bio_public
        WHERE bio_public IS NOT NULL
          AND public_profile IS NULL
        """
    )


def downgrade() -> None:
    """Remove public_profile, bio_generated_at, public_slug columns.

    All DDL is idempotent via IF EXISTS.
    """
    # Drop index first (before column)
    op.execute(
        """
        DROP INDEX IF EXISTS ix_vitalia_doctors_tenant_clinic_slug
        """
    )

    op.execute(
        """
        ALTER TABLE vitalia_doctors
        DROP COLUMN IF EXISTS public_slug
        """
    )

    op.execute(
        """
        ALTER TABLE vitalia_doctors
        DROP COLUMN IF EXISTS bio_generated_at
        """
    )

    op.execute(
        """
        ALTER TABLE vitalia_doctors
        DROP COLUMN IF EXISTS public_profile
        """
    )
