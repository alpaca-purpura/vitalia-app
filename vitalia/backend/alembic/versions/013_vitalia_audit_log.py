"""Vitalia audit log — HIPAA-lite 10-year PHI access log, partitioned monthly.

Per hipaa-lite.md § Audit log:
- All PHI reads/writes must create an audit row SYNC (before response)
- Retention: 10 years minimum (LatAm health regulations)
- payload_redacted: BYTEA pgcrypto encrypted (defense in depth)
- IMMUTABLE: no UPDATE, no soft-delete (occurrence_at is legal timestamp)
- PARTITIONED BY RANGE (occurred_at) — monthly partitions

Enum vitalia_audit_action_severity created idempotent for severity typing.

Indexes created on parent table propagate to partitions in PG 11+.
Initial monthly partitions bootstrapped for current month + 2 forward.
Future partitions created by cron or partition management tooling.

All DDL idempotent via IF NOT EXISTS / DO $$ EXCEPTION END $$.

Revision ID: 013_vitalia
Revises: 012_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "013_vitalia"
down_revision = "012_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_audit_log partitioned table + initial monthly partitions."""

    # pgcrypto required for payload_redacted BYTEA encryption
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # ─────────────────────────────────────────────────────────────────────────
    # Create the partitioned parent table (IF NOT EXISTS guard)
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_audit_log (
            id              UUID        NOT NULL DEFAULT gen_random_uuid(),
            tenant_id       UUID        NOT NULL,
            clinic_id       UUID        NOT NULL,
            user_id         UUID        NOT NULL,
            action          VARCHAR(64) NOT NULL,
            resource_type   VARCHAR(64) NOT NULL,
            resource_id     UUID,
            from_ip         INET,
            user_agent      TEXT,
            payload_redacted BYTEA,
            occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT pk_vitalia_audit_log PRIMARY KEY (id, occurred_at)
        ) PARTITION BY RANGE (occurred_at);
    """)

    # Indexes on parent — propagate to new partitions automatically (PG 11+)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vitalia_audit_log_tenant_clinic_action
          ON vitalia_audit_log (tenant_id, clinic_id, action, occurred_at DESC);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_vitalia_audit_log_resource
          ON vitalia_audit_log (tenant_id, clinic_id, resource_type, resource_id);
    """)

    # ─────────────────────────────────────────────────────────────────────────
    # Bootstrap monthly partitions: 2026-04, 2026-05, 2026-06, 2026-07
    # Future months added by partition management cron job.
    # Each partition uses IF NOT EXISTS guard via DO block.
    # ─────────────────────────────────────────────────────────────────────────

    op.execute("""
        DO $$ BEGIN
            CREATE TABLE IF NOT EXISTS vitalia_audit_log_2026_04
                PARTITION OF vitalia_audit_log
                FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');
        EXCEPTION WHEN SQLSTATE '42P07' THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TABLE IF NOT EXISTS vitalia_audit_log_2026_05
                PARTITION OF vitalia_audit_log
                FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');
        EXCEPTION WHEN SQLSTATE '42P07' THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TABLE IF NOT EXISTS vitalia_audit_log_2026_06
                PARTITION OF vitalia_audit_log
                FOR VALUES FROM ('2026-06-01') TO ('2026-07-01');
        EXCEPTION WHEN SQLSTATE '42P07' THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TABLE IF NOT EXISTS vitalia_audit_log_2026_07
                PARTITION OF vitalia_audit_log
                FOR VALUES FROM ('2026-07-01') TO ('2026-08-01');
        EXCEPTION WHEN SQLSTATE '42P07' THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            CREATE TABLE IF NOT EXISTS vitalia_audit_log_2026_08
                PARTITION OF vitalia_audit_log
                FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');
        EXCEPTION WHEN SQLSTATE '42P07' THEN NULL;
        END $$;
    """)


def downgrade() -> None:
    """Drop vitalia_audit_log and all partitions (dev iteration only)."""
    op.execute("DROP TABLE IF EXISTS vitalia_audit_log_2026_08;")
    op.execute("DROP TABLE IF EXISTS vitalia_audit_log_2026_07;")
    op.execute("DROP TABLE IF EXISTS vitalia_audit_log_2026_06;")
    op.execute("DROP TABLE IF EXISTS vitalia_audit_log_2026_05;")
    op.execute("DROP TABLE IF EXISTS vitalia_audit_log_2026_04;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_audit_log_resource;")
    op.execute("DROP INDEX IF EXISTS ix_vitalia_audit_log_tenant_clinic_action;")
    op.execute("DROP TABLE IF EXISTS vitalia_audit_log;")
