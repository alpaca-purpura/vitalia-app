"""Migration 037: durable-flow checkpoint namespace (vitalia).

Story: empleados-ia-auto-extension (platform) · L1 durable-flows-engine.
Proposal: docs/promotion-protocol/proposals/2026-06-02-durable-flows-engine.md (accepted).

The vitalia durable graphs (wizard onboarding, lucas daily analysis, treatment
follow-up) now persist their LangGraph state via the shared engine provider
``luana_core_flows.make_durable_checkpointer`` → ``AsyncPostgresSaver``.

Table ownership (O-2, 03-arch.md § L1.6):
  - ``langgraph-checkpoint-postgres`` 3.1.0 OWNS the checkpoint table DDL and
    creates its FIXED-name tables idempotently at app lifespan startup via
    ``AsyncPostgresSaver.setup()``:
        checkpoints · checkpoint_blobs · checkpoint_writes · checkpoint_migrations
    (3.1.0 has NO ``table_prefix`` knob — names are fixed; brand isolation is the
    vitalia Postgres DB; tenant isolation is the ``thread_id`` tenant segment).
  - This migration therefore does NOT ``CREATE TABLE`` the checkpoint internals
    (that would drift from LangGraph's owned schema across versions). It only
    ensures the ``pgcrypto`` prerequisite + records the durable-flow namespace
    in alembic history.

Legacy note: migration 020 (``020_vitalia_langgraph_checkpoint_tables``) hand-rolled
PREFIXED tables (``vitalia_wizard_onboarding_*`` / ``vitalia_lucas_analysis_*``)
during the pre-lift "D10" attempt, before the package was installed. Those tables
are NOT used by the durable provider (no ``table_prefix`` in 3.1.0) and are now
orphaned; they are left in place (removing them would be a destructive down
migration, out of scope for this story).

Idempotency: ``CREATE EXTENSION IF NOT EXISTS`` is re-runnable. Safe to re-apply
(``alembic upgrade head`` twice = no error — validator ``v_migration_idempotent``).

Revision ID: 037_vitalia
Revises: 036_vitalia
Create Date: 2026-06-02
"""

from __future__ import annotations

from alembic import op

revision = "037_vitalia"
down_revision = "036_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Ensure durable-flow checkpoint prerequisites (idempotent).

    LangGraph's ``AsyncPostgresSaver.setup()`` creates the fixed-name checkpoint
    tables at app startup; this migration only guarantees ``pgcrypto`` (harmless
    if already present — created by 035) for any column-level PHI need and pins
    the durable-flow namespace into alembic history.
    """
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    # NO op.create_table for checkpoint internals — owned by AsyncPostgresSaver.setup().


def downgrade() -> None:
    """No-op — checkpoint tables are LangGraph-owned; pgcrypto is shared."""
    # Intentionally empty: do not drop LangGraph-owned tables nor the shared
    # pgcrypto extension (used by 035 PHI columns).
