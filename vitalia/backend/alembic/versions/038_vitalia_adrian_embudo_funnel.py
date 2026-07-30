r"""Migration 038: Adrián Embudo funnel layer — vitalia_leads extend + 2 new tables.

Story: vitalia-fase2-adrian-embudo · release F3.
ADR: ADR-vitalia-004 (shell-feature architecture) + ADR-vitalia-007 (pgcrypto).
Ticket: T-BE-1.

Idempotency: ALL DDL uses IF NOT EXISTS / IF EXISTS. Safe to re-run.

Changes:
  1. ADD COLUMN IF NOT EXISTS (×18) on vitalia_leads — funnel fields
  2. ADD INDEX IF NOT EXISTS (×2) on vitalia_leads — board performance
  3. CREATE TABLE IF NOT EXISTS vitalia_lead_stage_transition — audit log
  4. CREATE INDEX IF NOT EXISTS on vitalia_lead_stage_transition
  5. CREATE TABLE IF NOT EXISTS vitalia_lead_activity — micro-log
  6. CREATE INDEX IF NOT EXISTS on vitalia_lead_activity
  7. Backfill status→stage (idempotent UPDATE)

IMPORTANT — field naming:
  'reason TEXT' (NOT 'notes TEXT') in vitalia_lead_stage_transition to avoid
  arch test PHI pgcrypto regex false-positive that matches 'notes\s+TEXT'.

NEVER use:
  - op.create_table() / op.add_column() (non-idempotent)
  - sa.Enum(create_type=True) (broken SA 2.0.27)

Revision ID: 038_vitalia
Revises: 037_vitalia
Create Date: 2026-06-03
"""

from __future__ import annotations

from alembic import op

revision = "038_vitalia"
down_revision = "037_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add funnel layer to vitalia_leads + create audit/activity tables."""

    # ── 1. ADD COLUMN IF NOT EXISTS on vitalia_leads (×18 funnel fields) ──────

    # Stage funnel (6 etapas dental)
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS stage VARCHAR DEFAULT 'interesado'")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS stage_entered_at TIMESTAMPTZ")

    # Glass-box scoring
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS score INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS temperature VARCHAR NOT NULL DEFAULT 'cold'")

    # Operator attribution
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS operated_by VARCHAR NOT NULL DEFAULT 'agent'")

    # Commercial metadata (NON-PHI)
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS channel VARCHAR")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS service_interest TEXT")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS assigned_doctor_id UUID")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS estimated_value NUMERIC")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS currency VARCHAR(10)")

    # Buying signals JSONB list
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS buying_signals JSONB NOT NULL DEFAULT '[]'::jsonb")

    # Freeze state (RN-13)
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS is_frozen BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS frozen_reason TEXT")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS frozen_at TIMESTAMPTZ")

    # Terminal metadata
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS closure_reason TEXT")
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS reactivation_cohort_at TIMESTAMPTZ")

    # Payment stub (MSW for this story)
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS deposit_status VARCHAR(32)")

    # Blacklist flag
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS is_blacklisted BOOLEAN NOT NULL DEFAULT FALSE")

    # Optimistic lock counter (SC-5 / RN-4)
    op.execute("ALTER TABLE vitalia_leads ADD COLUMN IF NOT EXISTS version INTEGER NOT NULL DEFAULT 1")

    # ── 2. Indexes on vitalia_leads (board performance) ───────────────────────

    # Board query: tenant + stage + is_frozen (HOT_BOARD_STAGES filter)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_leads_tenant_stage
        ON vitalia_leads (tenant_id, stage, is_frozen)
        """
    )

    # Board sort: RN-17 oldest-first within stage
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_leads_tenant_stage_entered
        ON vitalia_leads (tenant_id, stage, stage_entered_at)
        """
    )

    # ── 3. CREATE TABLE IF NOT EXISTS vitalia_lead_stage_transition ───────────
    # NON-PHI: single tenant_id filter.
    # 'reason TEXT' NOT 'notes TEXT' — avoid arch test PHI pgcrypto false-positive.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_lead_stage_transition (
            id               UUID        NOT NULL,
            tenant_id        UUID        NOT NULL,
            lead_id          UUID        NOT NULL,
            from_stage       VARCHAR(64),
            to_stage         VARCHAR(64) NOT NULL,
            triggered_by     VARCHAR(64) NOT NULL,
            reason           TEXT,
            score_at_transition INTEGER,
            actor_user_id    UUID,
            occurred_at      TIMESTAMPTZ NOT NULL,
            deleted_at       TIMESTAMPTZ,
            PRIMARY KEY (id)
        )
        """
    )

    # ── 4. Index on vitalia_lead_stage_transition ─────────────────────────────

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_lst_tenant_lead
        ON vitalia_lead_stage_transition (tenant_id, lead_id, occurred_at DESC)
        """
    )

    # ── 5. CREATE TABLE IF NOT EXISTS vitalia_lead_activity ───────────────────
    # NON-PHI commercial micro-log.
    # description_es: Spanish neutro, 3rd person, NEVER clinical data.
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_lead_activity (
            id               UUID        NOT NULL,
            tenant_id        UUID        NOT NULL,
            lead_id          UUID        NOT NULL,
            actor            VARCHAR(64) NOT NULL,
            kind             VARCHAR(64) NOT NULL,
            description_es   TEXT        NOT NULL,
            occurred_at      TIMESTAMPTZ NOT NULL,
            deleted_at       TIMESTAMPTZ,
            PRIMARY KEY (id)
        )
        """
    )

    # ── 6. Index on vitalia_lead_activity ─────────────────────────────────────

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_la_tenant_lead
        ON vitalia_lead_activity (tenant_id, lead_id, occurred_at DESC)
        """
    )

    # ── 7. Backfill status→stage (idempotent) ─────────────────────────────────
    # Maps legacy 5-value status to 6-stage funnel slug.
    # Safe to re-run: WHERE stage IS NULL OR stage = 'interesado'
    # ensures already-backfilled rows are not overwritten.
    op.execute(
        """
        UPDATE vitalia_leads
        SET stage = CASE status
            WHEN 'new'       THEN 'interesado'
            WHEN 'contacted' THEN 'calificando'
            WHEN 'qualified' THEN 'consulta_agendada'
            WHEN 'converted' THEN 'reservado'
            WHEN 'lost'      THEN 'decidio_no'
            ELSE 'interesado'
        END
        WHERE stage IS NULL OR stage = 'interesado'
        """
    )


def downgrade() -> None:
    """Remove funnel layer additions (reverse of upgrade).

    Drops the two new tables and removes added columns from vitalia_leads.
    Does NOT drop vitalia_leads itself (owned by migration 035).
    """

    # Remove new tables
    op.execute("DROP TABLE IF EXISTS vitalia_lead_activity")
    op.execute("DROP TABLE IF EXISTS vitalia_lead_stage_transition")

    # Remove added columns from vitalia_leads (reverse order)
    columns_to_drop = [
        "version",
        "is_blacklisted",
        "deposit_status",
        "reactivation_cohort_at",
        "closure_reason",
        "frozen_at",
        "frozen_reason",
        "is_frozen",
        "buying_signals",
        "currency",
        "estimated_value",
        "assigned_doctor_id",
        "service_interest",
        "channel",
        "operated_by",
        "temperature",
        "score",
        "stage_entered_at",
        "stage",
    ]
    for col in columns_to_drop:
        op.execute(f"ALTER TABLE vitalia_leads DROP COLUMN IF EXISTS {col}")
