# cap: clinics.lisa.doctores
"""Migration 040 — delta v3 D3-B: vitalia_doctor_bio_files.

Creates 1 table (idempotent — all DDL uses IF NOT EXISTS):
  vitalia_doctor_bio_files: registry of private bio material files per doctor
  (binary lives in R2/local storage under storage_key; this table drives
  listing, soft delete, download audit and RN-D3D-4 material-new detection).

Down-revision: 039 (vitalia_config_cuenta_fields)

Idempotency guaranteed per .claude/rules/backend-migrations.md:
  - CREATE TABLE IF NOT EXISTS
  - CREATE INDEX IF NOT EXISTS (2 indexes: scope + tenant)
  - No op.create_table() / op.add_column() (non-idempotent)
  - No Enum types (broken in SA 2.0.27)
  - downgrade: DROP ... IF EXISTS (idempotent both ways)

Columns per 03-arch-delta § 3.1:
  tenant_id + clinic_id = HIPAA-lite dual filter (hipaa-lite.md)
  doctor_id = logical FK -> vitalia_doctors (no hard FK, pattern 036)
  uploaded_at TIMESTAMPTZ drives RN-D3D-4 material-new detection
  deleted_at = soft delete only
"""

from __future__ import annotations

from alembic import op

# revision identifiers, used by Alembic
revision = "040_vitalia"
down_revision = "039_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_doctor_bio_files + 2 indexes (idempotent)."""
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_doctor_bio_files (
            id           UUID        NOT NULL DEFAULT gen_random_uuid() PRIMARY KEY,
            tenant_id    UUID        NOT NULL,
            clinic_id    UUID        NOT NULL,
            doctor_id    UUID        NOT NULL,
            storage_key  TEXT        NOT NULL,
            filename     TEXT        NOT NULL,
            size_bytes   BIGINT      NOT NULL,
            content_type TEXT        NOT NULL,
            uploaded_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            deleted_at   TIMESTAMPTZ
        )
        """
    )

    # Dual-filter + doctor listing path (GET /{doctor_id}/bio-files)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_doctor_bio_files_scope "
        "ON vitalia_doctor_bio_files (tenant_id, clinic_id, doctor_id)"
    )
    # Root tenant isolation scans
    op.execute("CREATE INDEX IF NOT EXISTS ix_doctor_bio_files_tenant ON vitalia_doctor_bio_files (tenant_id)")


def downgrade() -> None:
    """Drop vitalia_doctor_bio_files (IF EXISTS — idempotent)."""
    op.execute("DROP INDEX IF EXISTS ix_doctor_bio_files_scope")
    op.execute("DROP INDEX IF EXISTS ix_doctor_bio_files_tenant")
    op.execute("DROP TABLE IF EXISTS vitalia_doctor_bio_files")
