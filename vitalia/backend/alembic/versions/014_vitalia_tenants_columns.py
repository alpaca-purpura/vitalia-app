"""Vitalia tenants location columns — TenantLocationContract implementation.

Adds 4 columns to the tenants table per the promotion proposal
docs/promotion-protocol/proposals/2026-05-17-platform-tenants-location-columns.md
(state=migrated, commit 5ca61019).

TenantLocationContract (from core/luana-core-platform 0.2.0):
  is_onboarded       BOOLEAN NOT NULL DEFAULT FALSE
  location_country   VARCHAR(2) NULL (ISO 3166-1 alpha-2)
  location_city      VARCHAR(255) NULL
  timezone           VARCHAR(64) NULL (IANA TZ database)

Backfill: tenants created before 2026-05-17 are treated as onboarded
(they completed setup in previous brand versions).

All DDL idempotent via ADD COLUMN IF NOT EXISTS.

Revision ID: 014_vitalia
Revises: 013_vitalia
Create Date: 2026-05-18
"""

from __future__ import annotations

from alembic import op

revision = "014_vitalia"
down_revision = "013_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add TenantLocationContract columns to tenants table idempotent.

    Guard: if tenants table does not exist yet (i.e. migration 022 has not run
    and brand is being bootstrapped fresh), this migration safely skips.
    Migration 022 includes all 4 columns inline in CREATE TABLE IF NOT EXISTS,
    so a fresh install will have them without needing this ALTER TABLE path.
    """
    op.execute("""
        DO $migration_014$
        BEGIN
            IF EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name = 'tenants'
            ) THEN
                -- is_onboarded — tracks wizard completion. Mandatory NOT NULL + DEFAULT FALSE.
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS is_onboarded BOOLEAN NOT NULL DEFAULT FALSE;

                -- location_country — ISO 3166-1 alpha-2 (AR, PE, MX, CO, CL, BR, US, ES, ...)
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS location_country VARCHAR(2);

                -- location_city — disambiguation + analytics regional
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS location_city VARCHAR(255);

                -- timezone — IANA TZ database string
                ALTER TABLE tenants ADD COLUMN IF NOT EXISTS timezone VARCHAR(64);

                -- Backfill: tenants created before 2026-05-17 are treated as onboarded
                UPDATE tenants
                   SET is_onboarded = TRUE
                 WHERE created_at < '2026-05-17'
                   AND is_onboarded IS FALSE;

                -- Index for onboarding funnel queries
                CREATE INDEX IF NOT EXISTS ix_tenants_is_onboarded ON tenants (is_onboarded);

                RAISE NOTICE 'Migration 014: TenantLocationContract columns added/verified on existing tenants table.';
            ELSE
                RAISE NOTICE 'Migration 014 skipped: tenants created by 022 with all columns inline.';
            END IF;
        END $migration_014$;
    """)


def downgrade() -> None:
    """Drop TenantLocationContract columns from tenants (dev iteration only)."""
    op.execute("DROP INDEX IF EXISTS ix_tenants_is_onboarded;")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS timezone;")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS location_city;")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS location_country;")
    op.execute("ALTER TABLE tenants DROP COLUMN IF EXISTS is_onboarded;")
