# cap: __shared__
# story-origin: TBD
"""Migration 021 — vitalia_re_engagement_events (Slice 1 fidelización).

Creates vitalia_re_engagement_events partitioned table (PARTITION BY RANGE trigger_at).
PHI payload encrypted via pgcrypto (payload_phi BYTEA).
Monthly partitions for HIPAA-lite 10y retention policy.

Per .claude/rules/backend-migrations.md:
- Raw SQL only: op.execute() with CREATE TABLE IF NOT EXISTS
- NEVER op.create_table() / sa.Enum(create_type=True)
- TIMESTAMPTZ on all datetime columns

Per vitalia/.claude/rules/hipaa-lite.md:
- tenant_id + clinic_id NOT NULL (dual filter mandatory)
- payload_phi BYTEA (pgcrypto symmetric encryption — PHI)
- PARTITION BY RANGE (trigger_at) for 10y retention monthly sweep
- deleted_at TIMESTAMPTZ NULL (soft delete)
"""

from __future__ import annotations

from alembic import op  # type: ignore[import]


def upgrade() -> None:
    """Apply migration: create vitalia_re_engagement_events partitioned table + partitions + indexes."""
    # Partitioned parent table
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events (
          id UUID NOT NULL,
          tenant_id UUID NOT NULL,
          clinic_id UUID NOT NULL,
          patient_id UUID NOT NULL,
          pattern VARCHAR(32) NOT NULL,
          trigger_source VARCHAR(64) NOT NULL,
          trigger_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          template_id VARCHAR(64) NULL,
          sent_at TIMESTAMPTZ NULL,
          response_at TIMESTAMPTZ NULL,
          outcome VARCHAR(32) NULL,
          converted_to_appointment_id UUID NULL,
          payload_phi BYTEA NULL,
          audit_log_id UUID NULL,
          notes TEXT NULL,
          retry_count INT NOT NULL DEFAULT 0,
          last_error TEXT NULL,
          idempotency_key VARCHAR(128) NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
          deleted_at TIMESTAMPTZ NULL,
          PRIMARY KEY (id, trigger_at)
        ) PARTITION BY RANGE (trigger_at)
        """
    )

    # Monthly partitions — initial 6 months for HIPAA-lite 10y retention sweep
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_01
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-01-01') TO ('2026-02-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_02
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-02-01') TO ('2026-03-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_03
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-03-01') TO ('2026-04-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_04
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-04-01') TO ('2026-05-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_05
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-05-01') TO ('2026-06-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_06
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-06-01') TO ('2026-07-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_07
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-07-01') TO ('2026-08-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_08
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-08-01') TO ('2026-09-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_09
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-09-01') TO ('2026-10-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_10
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-10-01') TO ('2026-11-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_11
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-11-01') TO ('2026-12-01')
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS vitalia_re_engagement_events_2026_12
          PARTITION OF vitalia_re_engagement_events
          FOR VALUES FROM ('2026-12-01') TO ('2027-01-01')
        """
    )

    # Indexes (applied to partitioned table — propagate to partitions automatically in PG 11+)
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_pattern_patient
          ON vitalia_re_engagement_events (tenant_id, clinic_id, patient_id, pattern, trigger_at DESC)
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_throttle
          ON vitalia_re_engagement_events (tenant_id, clinic_id, patient_id, pattern, sent_at DESC)
          WHERE sent_at IS NOT NULL
        """
    )

    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_vitalia_re_engagement_events_idempotency
          ON vitalia_re_engagement_events (idempotency_key)
          WHERE idempotency_key IS NOT NULL
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_vitalia_re_engagement_events_outcome_status
          ON vitalia_re_engagement_events (tenant_id, clinic_id, outcome, trigger_at DESC)
        """
    )


def downgrade() -> None:
    """Reverse migration: drop indexes + partitions + parent table."""
    op.execute("DROP INDEX IF EXISTS ix_vitalia_re_engagement_events_outcome_status")
    op.execute("DROP INDEX IF EXISTS uq_vitalia_re_engagement_events_idempotency")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_re_engagement_events_throttle")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_re_engagement_events_pattern_patient")
    # Dropping parent table also drops all partitions
    op.execute("DROP TABLE IF EXISTS vitalia_re_engagement_events CASCADE")
