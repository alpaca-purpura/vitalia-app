"""Vitalia — schema-mirror of luana-core-iam engine tables.

Schema-mirror exception (per backend-ddd.md): builder-backend MAY create
these tables to mirror the engine's TenantModel / UserModel / UserTenantModel
DDL. No promotion proposal needed for brand-side migration of engine tables.

Promotion proposal reference:
    docs/promotion-protocol/proposals/2026-05-19-vitalia-adopt-luana-core-iam.md
    (state: accepted)

Tables created (idempotent — IF NOT EXISTS):
    tenants          — engine TenantModel (includes 014_vitalia columns inline)
    users            — engine UserModel
    user_tenants     — engine UserTenantModel (junction)

Migration 014_vitalia included 4 columns via ALTER TABLE ADD COLUMN IF NOT EXISTS.
Those columns are now also inline in CREATE TABLE IF NOT EXISTS tenants here,
making the schema consistent for fresh installs.

Migration 014_vitalia has been updated with a DO $ guard so it safely skips
if tenants table already exists (created by this migration).

Revision ID: 022_vitalia
Revises: 021_vitalia
Create Date: 2026-05-19
"""

from __future__ import annotations

from alembic import op

revision = "022_vitalia"
down_revision = "021_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create engine IAM tables idempotent (schema-mirror for vitalia brand)."""

    # ── pgcrypto (required for gen_random_uuid() if not available via uuid-ossp) ──
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")

    # ── tenants ───────────────────────────────────────────────────────────────────
    # Includes all columns from migration 014_vitalia inline so fresh installs
    # don't need the ALTER TABLE path. The 014 migration is guarded with DO $
    # to skip safely if this table already exists.
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.tenants (
            id uuid NOT NULL DEFAULT gen_random_uuid(),
            name character varying NOT NULL,
            slug character varying NOT NULL,
            config_json jsonb DEFAULT '{}'::jsonb,
            default_currency character varying DEFAULT 'USD',
            timezone character varying DEFAULT 'UTC',
            extraction_priority integer DEFAULT 0 NOT NULL,
            gemini_api_key character varying,
            webhook_secret character varying,
            can_use_platform_keys boolean DEFAULT false,
            tracking_config jsonb DEFAULT '{}'::jsonb,
            weekly_start_day integer DEFAULT 0,
            fiscal_year_start_month integer DEFAULT 1,
            fiscal_year_start_day integer DEFAULT 1,
            is_active boolean DEFAULT true,
            created_at timestamp with time zone DEFAULT now(),
            updated_at timestamp with time zone,
            is_onboarded boolean NOT NULL DEFAULT false,
            location_country character varying(2),
            location_city character varying(255),
            CONSTRAINT pk_tenants PRIMARY KEY (id),
            CONSTRAINT uq_tenants_slug UNIQUE (slug)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenants_slug ON tenants (slug);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tenants_is_onboarded ON tenants (is_onboarded);")

    # ── users ─────────────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.users (
            id uuid NOT NULL DEFAULT gen_random_uuid(),
            full_name character varying,
            email character varying NOT NULL,
            phone character varying,
            clerk_id character varying,
            role character varying DEFAULT 'admin',
            is_active boolean DEFAULT true,
            created_at timestamp with time zone DEFAULT now(),
            updated_at timestamp with time zone,
            CONSTRAINT pk_users PRIMARY KEY (id),
            CONSTRAINT uq_users_email UNIQUE (email),
            CONSTRAINT uq_users_clerk_id UNIQUE (clerk_id)
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_clerk_id ON users (clerk_id);")

    # ── user_tenants ──────────────────────────────────────────────────────────────
    op.execute("""
        CREATE TABLE IF NOT EXISTS public.user_tenants (
            user_id uuid NOT NULL,
            tenant_id uuid NOT NULL,
            role character varying DEFAULT 'member',
            is_active boolean DEFAULT true NOT NULL,
            created_at timestamp with time zone DEFAULT now(),
            CONSTRAINT pk_user_tenants PRIMARY KEY (user_id, tenant_id),
            CONSTRAINT fk_user_tenants_user FOREIGN KEY (user_id)
                REFERENCES public.users(id) ON DELETE CASCADE,
            CONSTRAINT fk_user_tenants_tenant FOREIGN KEY (tenant_id)
                REFERENCES public.tenants(id) ON DELETE CASCADE
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_tenants_tenant_id ON user_tenants (tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_user_tenants_user_id ON user_tenants (user_id);")


def downgrade() -> None:
    """Drop engine IAM tables (dev iteration only — NEVER run on prod)."""
    op.execute("DROP TABLE IF EXISTS public.user_tenants CASCADE;")
    op.execute("DROP TABLE IF EXISTS public.users CASCADE;")
    op.execute("DROP TABLE IF EXISTS public.tenants CASCADE;")
