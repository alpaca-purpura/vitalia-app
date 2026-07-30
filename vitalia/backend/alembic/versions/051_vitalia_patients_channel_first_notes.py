# cap: crm.crm-consent-optout
"""Migration 051 — vitalia_patients: add channel_first + notes columns.

Brand: vitalia
Story: vitalia-fase2-mateo-nueva-cita  T-BE-5 (schemafix)
Arch: 03-arch-be.md

ROOT CAUSE (live 500 2026-06-22):
    patient_repository.create_minimal() (INSERT) and search() (SELECT) both
    referenced `channel_first` and `notes` columns that did not exist in
    vitalia_patients. Unit tests all passed via mocking — they never hit the
    real schema. This migration adds the missing columns.

DDL idempotente (raw SQL + IF NOT EXISTS — backend-migrations.md):
    1. ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS channel_first TEXT
       — acquisition channel metadata (not PHI — plaintext OK).
         Examples: 'walk_in', 'phone', 'whatsapp', 'referral'.
    2. ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS notes TEXT
       — optional note nullable.
         HIPAA-lite note: the column is added nullable. In the initial inline
         create flow (T-BE-5), notes is always NULL — the inline form only
         sends name+phone+channel. If a future surface writes a non-null note,
         encrypt it with pgp_sym_encrypt (see ADR-007 D3) and flag the D10
         patient surface story for encryption at write time.
         TODO(D10): encrypt notes if it ever carries PHI.

Design choice (notes encryption):
    OPTION CHOSEN → add column nullable, always NULL for inline create.
    Reasoning: the spec for this ticket (T-BE-5) states the inline form sends
    only name + phone + channel. No PHI is written to `notes` by this code
    path. Adding encryption infrastructure for a column that currently only
    stores NULL would be premature complexity. The TODO(D10) marker in the
    repository ensures the next story that writes to this column will add
    encryption.

Re-run safety:
    Both ADDs use IF NOT EXISTS — re-running upgrade is a strict no-op.

Revision IDs:
  revision: 051_vitalia
  down_revision: 050_vitalia
  branch_labels: None
  depends_on: None
"""

from __future__ import annotations

from alembic import op  # type: ignore[import]

revision = "051_vitalia"
down_revision = "050_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add channel_first (acquisition channel) and notes columns to vitalia_patients."""
    # Acquisition channel: NOT PHI, plaintext, nullable TEXT.
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS channel_first TEXT")
    # Notes: nullable TEXT. Currently always NULL in inline create flow (T-BE-5).
    # TODO(D10): encrypt with pgp_sym_encrypt if future surface writes PHI here.
    op.execute("ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS notes TEXT")


def downgrade() -> None:
    """Reverse: drop channel_first + notes columns.

    Note: DROP COLUMN IF EXISTS is safe but non-idempotent if applied twice.
    Production rollback requires manual validation of dependent queries first.
    """
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS notes")
    op.execute("ALTER TABLE vitalia_patients DROP COLUMN IF EXISTS channel_first")
