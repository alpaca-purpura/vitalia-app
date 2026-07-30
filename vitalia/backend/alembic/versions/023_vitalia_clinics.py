"""Vitalia brand extension — vitalia_clinic_branches table.

Creates the brand-specific clinic branches table that extends the engine
IAM tenant with physical healthcare entity attributes.

Story: vitalia-adopt-luana-core-iam (T-be-clinics-extension)

Design notes:
  - NOT vitalia_clinics (that was the phantom table, never existed in migrations)
  - Table name: vitalia_clinic_branches (brand-specific extension)
  - FK to public.tenants(id) ON DELETE CASCADE (engine IAM table from 022)
  - HIPAA dual-filter: tenant_id + id (clinic_id) mandatory on all queries
  - Soft deletes: deleted_at column (no hard deletes)
  - Unique constraint: (tenant_id, slug) — slug unique per tenant

Revision ID: 023_vitalia
Revises: 022_vitalia
Create Date: 2026-05-19
"""

from __future__ import annotations

from alembic import op

revision = "023_vitalia"
down_revision = "022_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vitalia_clinic_branches table idempotent."""

    op.execute("""
        CREATE TABLE IF NOT EXISTS public.vitalia_clinic_branches (
            id uuid NOT NULL DEFAULT gen_random_uuid(),
            tenant_id uuid NOT NULL,
            name character varying NOT NULL,
            slug character varying NOT NULL,
            country character varying(2) NOT NULL,
            timezone character varying NOT NULL DEFAULT 'UTC',
            plan_tier character varying NOT NULL DEFAULT 'starter',
            is_active boolean NOT NULL DEFAULT true,
            onboarding_completed boolean NOT NULL DEFAULT false,
            created_at timestamp with time zone NOT NULL DEFAULT now(),
            updated_at timestamp with time zone,
            deleted_at timestamp with time zone,
            CONSTRAINT pk_vitalia_clinic_branches PRIMARY KEY (id),
            CONSTRAINT fk_vitalia_clinic_branches_tenant
                FOREIGN KEY (tenant_id)
                REFERENCES public.tenants(id)
                ON DELETE CASCADE,
            CONSTRAINT uq_vitalia_clinic_branches_tenant_slug
                UNIQUE (tenant_id, slug)
        );
    """)

    # Indexes for common query patterns
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_clinic_branches_tenant_id ON vitalia_clinic_branches (tenant_id);"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_vitalia_clinic_branches_slug ON vitalia_clinic_branches (slug);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_clinic_branches_is_active ON vitalia_clinic_branches (is_active);"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_vitalia_clinic_branches_deleted_at ON vitalia_clinic_branches (deleted_at);"
    )


def downgrade() -> None:
    """Drop vitalia_clinic_branches table (dev iteration only)."""
    op.execute("DROP TABLE IF EXISTS public.vitalia_clinic_branches CASCADE;")
