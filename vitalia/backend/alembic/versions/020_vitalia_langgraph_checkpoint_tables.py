"""LangGraph checkpoint tables for Vitalia wizard onboarding + Lucas analysis.

Creates the standard LangGraph AsyncPostgresSaver checkpoint tables for two
named prefixes:
  - vitalia_wizard_onboarding_ → Valeria brand onboarding wizard LangGraph state
  - vitalia_lucas_analysis_    → Lucas daily growth analysis LangGraph state

Each prefix creates 3 tables matching the AsyncPostgresSaver schema (LangGraph 0.2+):
  {prefix}checkpoints       — main checkpoint state per thread + config
  {prefix}checkpoint_blobs  — binary blobs for channels (split for large payloads)
  {prefix}checkpoint_writes — pending writes per checkpoint step

Note: We create tables directly via raw DDL (idempotent IF NOT EXISTS) because
`AsyncPostgresSaver.setup()` cannot be called inside an Alembic migration context
(requires an async psycopg3 connection, not available in synchronous migration env).
The schema below matches the canonical AsyncPostgresSaver DDL (langgraph>=0.2).

All DDL idempotent via CREATE TABLE IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.

Revision ID: 020_vitalia
Revises: 019_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "020_vitalia"
down_revision = "019_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create LangGraph checkpoint tables for Vitalia wizard onboarding + Lucas analysis."""

    # ── Wizard onboarding checkpoints (Valeria brand copilot wizard) ──────────

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_wizard_onboarding_checkpoints (
            thread_id            TEXT NOT NULL,
            checkpoint_ns        TEXT NOT NULL DEFAULT '',
            checkpoint_id        TEXT NOT NULL,
            parent_checkpoint_id TEXT,
            type                 TEXT,
            checkpoint           JSONB NOT NULL DEFAULT '{}'::jsonb,
            metadata             JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_wizard_onboarding_checkpoints
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
        )
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_wizard_onboarding_checkpoints_thread"
        " ON vitalia_wizard_onboarding_checkpoints (thread_id, checkpoint_ns)"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_wizard_onboarding_checkpoint_blobs (
            thread_id     TEXT  NOT NULL,
            checkpoint_ns TEXT  NOT NULL DEFAULT '',
            channel       TEXT  NOT NULL,
            version       TEXT  NOT NULL,
            type          TEXT  NOT NULL,
            blob          BYTEA,
            CONSTRAINT pk_vitalia_wizard_onboarding_checkpoint_blobs
                PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_wizard_onboarding_checkpoint_writes (
            thread_id     TEXT    NOT NULL,
            checkpoint_ns TEXT    NOT NULL DEFAULT '',
            checkpoint_id TEXT    NOT NULL,
            task_id       TEXT    NOT NULL,
            idx           INTEGER NOT NULL,
            channel       TEXT    NOT NULL,
            type          TEXT,
            blob          BYTEA   NOT NULL,
            CONSTRAINT pk_vitalia_wizard_onboarding_checkpoint_writes
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
        )
    """)

    # ── Lucas analysis checkpoints (Lucas cron growth analysis) ───────────────

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_lucas_analysis_checkpoints (
            thread_id            TEXT NOT NULL,
            checkpoint_ns        TEXT NOT NULL DEFAULT '',
            checkpoint_id        TEXT NOT NULL,
            parent_checkpoint_id TEXT,
            type                 TEXT,
            checkpoint           JSONB NOT NULL DEFAULT '{}'::jsonb,
            metadata             JSONB NOT NULL DEFAULT '{}'::jsonb,
            created_at           TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_lucas_analysis_checkpoints
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id)
        )
    """)

    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_lucas_analysis_checkpoints_thread"
        " ON vitalia_lucas_analysis_checkpoints (thread_id, checkpoint_ns)"
    )

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_lucas_analysis_checkpoint_blobs (
            thread_id     TEXT  NOT NULL,
            checkpoint_ns TEXT  NOT NULL DEFAULT '',
            channel       TEXT  NOT NULL,
            version       TEXT  NOT NULL,
            type          TEXT  NOT NULL,
            blob          BYTEA,
            CONSTRAINT pk_vitalia_lucas_analysis_checkpoint_blobs
                PRIMARY KEY (thread_id, checkpoint_ns, channel, version)
        )
    """)

    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_lucas_analysis_checkpoint_writes (
            thread_id     TEXT    NOT NULL,
            checkpoint_ns TEXT    NOT NULL DEFAULT '',
            checkpoint_id TEXT    NOT NULL,
            task_id       TEXT    NOT NULL,
            idx           INTEGER NOT NULL,
            channel       TEXT    NOT NULL,
            type          TEXT,
            blob          BYTEA   NOT NULL,
            CONSTRAINT pk_vitalia_lucas_analysis_checkpoint_writes
                PRIMARY KEY (thread_id, checkpoint_ns, checkpoint_id, task_id, idx)
        )
    """)


def downgrade() -> None:
    """Drop LangGraph checkpoint tables for both Vitalia prefixes (dev iteration only)."""
    # Lucas analysis
    op.execute("DROP TABLE IF EXISTS vitalia_lucas_analysis_checkpoint_writes")
    op.execute("DROP TABLE IF EXISTS vitalia_lucas_analysis_checkpoint_blobs")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_lucas_analysis_checkpoints_thread")
    op.execute("DROP TABLE IF EXISTS vitalia_lucas_analysis_checkpoints")
    # Wizard onboarding
    op.execute("DROP TABLE IF EXISTS vitalia_wizard_onboarding_checkpoint_writes")
    op.execute("DROP TABLE IF EXISTS vitalia_wizard_onboarding_checkpoint_blobs")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_wizard_onboarding_checkpoints_thread")
    op.execute("DROP TABLE IF EXISTS vitalia_wizard_onboarding_checkpoints")
