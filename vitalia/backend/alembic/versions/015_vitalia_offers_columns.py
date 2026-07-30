"""Vitalia offers columns — OfferAdherenceContract implementation.

Adds 5 columns to the offers table per the promotion proposal
docs/promotion-protocol/proposals/2026-05-17-offer-studio-multi-session-maintenance.md
(state=migrated, commit 5ca61019).

OfferAdherenceContract (from core/luana-core-offer-studio 0.2.0):
  requires_multi_session BOOLEAN NOT NULL DEFAULT FALSE
  sessions_expected      INTEGER NULL (>= 1 if requires_multi_session)
  gap_alert_days         INTEGER NULL (cron threshold days)
  maintenance_schedule   maintenance_schedule_enum NOT NULL DEFAULT 'NONE'
  maintenance_custom_days INTEGER NULL (required if CUSTOM)

Enum: maintenance_schedule_enum with values:
  NONE | MONTHLY | QUARTERLY | BIANNUAL | ANNUAL | CUSTOM

Check constraints per OfferAdherenceContract:
  chk_offer_sessions_expected_positive
  chk_offer_maintenance_custom_days_valid

All DDL idempotent. Enum via DO $$ EXCEPTION WHEN duplicate_object END $$.
Check constraints use DO block to avoid duplicate_object error.

Revision ID: 015_vitalia
Revises: 014_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "015_vitalia"
down_revision = "014_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add OfferAdherenceContract columns + enum + check constraints idempotent."""

    # ─────────────────────────────────────────────────────────────────────────
    # Enum type — canonical values per MaintenanceScheduleEnum engine contract
    # NEVER sa.Enum(create_type=True) — use raw SQL DO $$ block
    # ─────────────────────────────────────────────────────────────────────────
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE maintenance_schedule_enum AS ENUM (
                'NONE',
                'MONTHLY',
                'QUARTERLY',
                'BIANNUAL',
                'ANNUAL',
                'CUSTOM'
            );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # ─────────────────────────────────────────────────────────────────────────
    # Column additions — idempotent ADD COLUMN IF NOT EXISTS
    # ─────────────────────────────────────────────────────────────────────────

    op.execute("ALTER TABLE offers ADD COLUMN IF NOT EXISTS requires_multi_session BOOLEAN NOT NULL DEFAULT FALSE;")
    op.execute("ALTER TABLE offers ADD COLUMN IF NOT EXISTS sessions_expected INTEGER;")
    op.execute("ALTER TABLE offers ADD COLUMN IF NOT EXISTS gap_alert_days INTEGER;")
    op.execute(
        "ALTER TABLE offers"
        " ADD COLUMN IF NOT EXISTS maintenance_schedule"
        " maintenance_schedule_enum NOT NULL DEFAULT 'NONE';"
    )
    op.execute("ALTER TABLE offers ADD COLUMN IF NOT EXISTS maintenance_custom_days INTEGER;")

    # ─────────────────────────────────────────────────────────────────────────
    # Check constraints — per OfferAdherenceContract invariants
    # Use DO block for idempotency (duplicate_object = constraint exists)
    # ─────────────────────────────────────────────────────────────────────────

    op.execute("""
        DO $$ BEGIN
            ALTER TABLE offers
                ADD CONSTRAINT chk_offer_sessions_expected_positive
                    CHECK (sessions_expected IS NULL OR sessions_expected >= 1);
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    op.execute("""
        DO $$ BEGIN
            ALTER TABLE offers
                ADD CONSTRAINT chk_offer_maintenance_custom_days_valid
                    CHECK (
                        (maintenance_schedule = 'CUSTOM' AND maintenance_custom_days >= 1)
                        OR (maintenance_schedule <> 'CUSTOM' AND maintenance_custom_days IS NULL)
                    );
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # Operational index for cron queries (multi-session gap sweep)
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offers_requires_multi_session"
        " ON offers (requires_multi_session)"
        " WHERE requires_multi_session = TRUE;"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offers_maintenance_schedule"
        " ON offers (maintenance_schedule)"
        " WHERE maintenance_schedule <> 'NONE';"
    )


def downgrade() -> None:
    """Drop OfferAdherenceContract columns + constraints from offers (dev only)."""
    op.execute("DROP INDEX IF EXISTS ix_offers_maintenance_schedule;")
    op.execute("DROP INDEX IF EXISTS ix_offers_requires_multi_session;")
    op.execute("""
        ALTER TABLE offers
            DROP CONSTRAINT IF EXISTS chk_offer_maintenance_custom_days_valid,
            DROP CONSTRAINT IF EXISTS chk_offer_sessions_expected_positive,
            DROP COLUMN IF EXISTS maintenance_custom_days,
            DROP COLUMN IF EXISTS maintenance_schedule,
            DROP COLUMN IF EXISTS gap_alert_days,
            DROP COLUMN IF EXISTS sessions_expected,
            DROP COLUMN IF EXISTS requires_multi_session;
    """)
    op.execute("DROP TYPE IF EXISTS maintenance_schedule_enum;")
