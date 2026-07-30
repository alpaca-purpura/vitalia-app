# cap: scheduling.mateo-agenda
"""Migration 052 — vitalia_appointments: add notes_internal column.

Brand: vitalia
Story: vitalia-fase2-mateo-nueva-cita  T-BE-4 (bugfix)
Arch: 03-arch-be.md

ROOT CAUSE (live 500 on 2026-06-22/23):
    POST /api/v1/scheduling/appointments → asyncpg UndefinedColumnError:
        column "notes_internal" of relation "vitalia_appointments" does not exist.
    agenda_grid_repository_impl.create() built the INSERT with notes_internal
    but no migration ever added the column. Unit tests passed via mocking
    and never hit the real schema. This migration adds the missing column.

HIPAA-lite decision (option b — per task spec):
    notes_internal is internal staff notes (e.g. "patient requested early slot").
    The column MAY carry clinical PHI in future surfaces (appointment-notes feature).
    However, the inline nueva-cita flow (the only current write path) ALWAYS sends
    notes_internal=None/null. There is no PHI being written to this column today.

    Encryption option (a) was evaluated:
    - Would require wiring KEKClient into AgendaGridRepositoryImpl (currently not
      injected there — the repo uses raw SQL text() calls).
    - The INSERT in create() would need to become:
        pgp_sym_encrypt(:notes, :kek) returning bytea, column type bytea.
    - The read path (get_detail, get_list) would need pgp_sym_decrypt on reads.
    This is a substantial change for a column that today only stores NULL.

    Decision → option (b): add as nullable TEXT, always NULL in current flow.
    The TODO(PHI) marker ensures the appointment-notes surface story adds
    encryption before any non-null PHI is written.

    The same rationale was applied to migration 051 (notes column on vitalia_patients
    — see that migration's docstring).

    TODO(PHI): when the appointment-notes surface lands, encrypt notes_internal
    with pgp_sym_encrypt(:val, :kek) and change column type to bytea.
    Reference: vitalia/.claude/rules/hipaa-lite.md § Encryption at rest + ADR-007 D3.

Schema mirror:
    vitalia_appointments is managed via raw SQL (no SQLAlchemy model).
    No model mirror needed — the repo reads/writes via text() statements only.

Other columns audited (all present in vitalia_appointments pre-052):
    id, tenant_id, patient_id, doctor_id, slot_iso, duration_minutes,
    status, origin, currency, created_at — all verified via information_schema
    query against vitalia_dev on 2026-06-23. Only notes_internal was missing.

DDL idempotente (raw SQL + IF NOT EXISTS — backend-migrations.md):
    ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS notes_internal TEXT

Re-run safety:
    ADD COLUMN IF NOT EXISTS is a strict no-op if column already exists.

Revision IDs:
  revision: 052_vitalia
  down_revision: 051_vitalia
  branch_labels: None
  depends_on: None
"""

from __future__ import annotations

from alembic import op  # type: ignore[import]

revision = "052_vitalia"
down_revision = "051_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add notes_internal (nullable TEXT) to vitalia_appointments.

    This column stores optional internal staff notes for an appointment.
    Currently always NULL in the inline nueva-cita flow.

    TODO(PHI): encrypt with pgp_sym_encrypt when appointment-notes surface lands.
    """
    op.execute("ALTER TABLE vitalia_appointments ADD COLUMN IF NOT EXISTS notes_internal TEXT")


def downgrade() -> None:
    """Remove notes_internal column from vitalia_appointments.

    Note: DROP COLUMN IF EXISTS is safe but irreversible (data loss).
    Only apply in development rollback scenarios.
    """
    op.execute("ALTER TABLE vitalia_appointments DROP COLUMN IF EXISTS notes_internal")
