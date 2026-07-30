# cap: scheduling.mateo-agenda
"""Migration 050 — EXCLUDE constraint anti-solape (btree_gist) en clinic_map.

Brand: vitalia
Story: vitalia-fase2-mateo-nueva-cita  T-BE-2
Arch:  03-arch-be.md § 7

DDL idempotente (raw SQL + IF NOT EXISTS):
  1. CREATE EXTENSION IF NOT EXISTS btree_gist
  2. ADD COLUMN IF NOT EXISTS start_time / end_time / status
  3. Backfill desde vitalia_appointments
  4. CREATE INDEX IF NOT EXISTS ix_acm_doctor_range
  5. DO $$ BEGIN IF NOT EXISTS pg_constraint ... THEN ADD CONSTRAINT EXCLUDE USING gist END IF END $$

EXCLUDE semantics (RN-2): tstzrange(start_time, end_time, '[)') — half-open.
Back-to-back slots coexist (10:00-10:30 ∩ 10:30-11:00 = empty).
Partial WHERE: status <> 'CANCELLED' AND start_time IS NOT NULL (RN-6).

Engine boundary D-A: constraint lives in BRAND table (has doctor_id).
Core appointments table NOT touched (no doctor_id there).

Revision IDs:
  revision: 050_vitalia
  down_revision: 049_vitalia
  branch_labels: None
  depends_on: None
"""

from alembic import op

revision = "050_vitalia"
down_revision = "049_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Apply migration 050 — idempotent (safe to re-run)."""
    # 1. Enable btree_gist for GIST exclusion on equality operators (UUID columns)
    op.execute("CREATE EXTENSION IF NOT EXISTS btree_gist;")

    # 2. Mirror columns: start_time / end_time / status
    op.execute("ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS start_time timestamptz;")
    op.execute("ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS end_time timestamptz;")
    op.execute("ALTER TABLE vitalia_appointment_clinic_map ADD COLUMN IF NOT EXISTS status varchar(32);")

    # 3. Backfill start_time / end_time / status from the engine appointments table.
    #    vitalia_appointments stores slot_iso (start) + duration_minutes (length).
    #    end_time = slot_iso + duration_minutes * interval '1 minute'.
    #    Only rows where start_time IS NULL (idempotent — skip already-backfilled rows).
    op.execute(
        """
        UPDATE vitalia_appointment_clinic_map m
           SET start_time = a.slot_iso,
               end_time   = a.slot_iso + (a.duration_minutes * interval '1 minute'),
               status     = a.status
          FROM vitalia_appointments a
         WHERE m.appointment_id = a.id
           AND m.start_time IS NULL;
        """
    )

    # 3b. Deduplicate pre-existing overlapping rows (dev-seed data cleanup).
    #     Before adding the EXCLUDE constraint, mark the older duplicate rows as CANCELLED
    #     in the mirror status column so the constraint can be created without error.
    #     This only affects the clinic_map mirror status — the source vitalia_appointments
    #     rows are NOT touched (non-destructive for prod data archaeology).
    #     Logic: for each group (tenant_id, clinic_id, doctor_id, slot_iso+duration) with
    #     more than one non-CANCELLED row, keep the NEWEST (by appointment_id ctid) and
    #     mark older ones CANCELLED in the mirror column.
    op.execute(
        """
        UPDATE vitalia_appointment_clinic_map m
           SET status = 'CANCELLED'
         WHERE m.status <> 'CANCELLED'
           AND m.start_time IS NOT NULL
           AND EXISTS (
             SELECT 1
               FROM vitalia_appointment_clinic_map m2
              WHERE m2.tenant_id  = m.tenant_id
                AND m2.clinic_id  = m.clinic_id
                AND m2.doctor_id  = m.doctor_id
                AND m2.start_time = m.start_time
                AND m2.end_time   = m.end_time
                AND m2.status    <> 'CANCELLED'
                AND m2.appointment_id > m.appointment_id
           );
        """
    )

    # 4. Supporting index for range queries (doctor × date lookups)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_acm_doctor_range ON vitalia_appointment_clinic_map (doctor_id, start_time);"
    )

    # 5. EXCLUDE constraint — half-open '[)' tstzrange, partial WHERE (CANCELLED excluded)
    #    PostgreSQL has no ADD CONSTRAINT IF NOT EXISTS; guard via pg_constraint lookup.
    op.execute(
        """
        DO $$ BEGIN
          IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'no_overlap_per_doctor'
          ) THEN
            ALTER TABLE vitalia_appointment_clinic_map
              ADD CONSTRAINT no_overlap_per_doctor
              EXCLUDE USING gist (
                tenant_id WITH =,
                clinic_id WITH =,
                doctor_id WITH =,
                tstzrange(start_time, end_time, '[)') WITH &&
              ) WHERE (status <> 'CANCELLED' AND start_time IS NOT NULL);
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    """Remove migration 050 artifacts (idempotent — IF EXISTS guards)."""
    # Drop constraint first (before dropping columns it references)
    op.execute(
        """
        DO $$ BEGIN
          IF EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'no_overlap_per_doctor'
          ) THEN
            ALTER TABLE vitalia_appointment_clinic_map
              DROP CONSTRAINT no_overlap_per_doctor;
          END IF;
        END $$;
        """
    )
    op.execute("DROP INDEX IF EXISTS ix_acm_doctor_range;")
    op.execute("ALTER TABLE vitalia_appointment_clinic_map DROP COLUMN IF EXISTS start_time;")
    op.execute("ALTER TABLE vitalia_appointment_clinic_map DROP COLUMN IF EXISTS end_time;")
    op.execute("ALTER TABLE vitalia_appointment_clinic_map DROP COLUMN IF EXISTS status;")
    # Note: btree_gist extension NOT dropped (may be used by other constraints)
