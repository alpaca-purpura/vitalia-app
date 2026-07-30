# cap: lisa.servicios
"""Migration 045 — offer service brand-projection tables (Lisa medical catalog).

Net-new ``offer`` module (story vitalia-fase2-lisa-servicios T-1). Five brand-level
tables that project over the engine Offer (offer_id → products.id). The offer-core
itself persists as an engine ProductModel row created by the application layer
(keystone D-1 = T-2/T-4), NOT here.

FK note: ``offer_id`` is a plain UUID column WITHOUT a constraint to ``products`` —
the engine ``products`` table is not present in the vitalia schema at T-1 (its
creation is a T-2/keystone concern). This mirrors the assets.offer_id hotfix
decision (043 · proposal 2026-06-12-assets-offer-fk-hotfix): brand projections
reference the offer by id without a hard FK. tenant_id keeps the FK to tenants.

PHI: offer_service_cases holds before/after patient photos (PHI · HIPAA-lite) →
clinic_id column for the dual filter. Catalog tables (ext/links/testimonials/brief)
are NOT PHI (RN-13).

DDL is idempotent: CREATE TABLE/INDEX IF NOT EXISTS. Re-running upgrade = no-op.

Revision ID: 045_vitalia
Revises: 044_vitalia
"""

from alembic import op

revision = "045_vitalia"
down_revision = "044_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- offer_service_ext — brand projection over engine Offer (1:1 per offer) ---
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_service_ext (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            offer_id UUID NOT NULL,
            modality VARCHAR NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT false,
            canonical_service_ref VARCHAR,
            category VARCHAR,
            clinic_scope UUID,
            description_long TEXT,
            includes TEXT,
            excludes TEXT,
            warranty TEXT,
            variants JSONB NOT NULL DEFAULT '[]'::jsonb,
            procedure_steps TEXT,
            anesthesia_pain TEXT,
            prep TEXT,
            aftercare TEXT,
            downtime TEXT,
            expected_result TEXT,
            result_timing TEXT,
            result_lifespan TEXT,
            realistic_expectations TEXT,
            risks TEXT,
            red_flags TEXT,
            session_interval JSONB,
            recurrence_interval JSONB,
            initial_appt_duration_minutes INTEGER,
            initial_appt_type VARCHAR,
            pricing JSONB,
            candidate_for_library BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_offer_service_ext_tenant ON offer_service_ext (tenant_id)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_offer_service_ext_offer "
        "ON offer_service_ext (offer_id) WHERE deleted_at IS NULL"
    )

    # --- offer_service_specialist_links — offer ↔ doctor (vitalia_doctors roster) ---
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_service_specialist_links (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            offer_id UUID NOT NULL,
            doctor_id UUID NOT NULL REFERENCES vitalia_doctors(id),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_offer_service_links_tenant ON offer_service_specialist_links (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_offer_service_links_offer ON offer_service_specialist_links (offer_id)")
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_offer_service_links_offer_doctor "
        "ON offer_service_specialist_links (offer_id, doctor_id) WHERE deleted_at IS NULL"
    )

    # --- offer_service_cases — before/after patient photos (PHI · HIPAA-lite) ---
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_service_cases (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            offer_id UUID NOT NULL,
            clinic_id UUID,
            before_asset_url VARCHAR NOT NULL,
            after_asset_url VARCHAR NOT NULL,
            consent_signed BOOLEAN NOT NULL DEFAULT false,
            consent_ref VARCHAR,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_offer_service_cases_tenant ON offer_service_cases (tenant_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_offer_service_cases_offer ON offer_service_cases (offer_id)")

    # --- offer_service_testimonials — manual marketing testimonials (NOT PHI) ---
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_service_testimonials (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            offer_id UUID NOT NULL,
            rating INTEGER NOT NULL,
            text TEXT NOT NULL,
            author VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_service_testimonials_tenant ON offer_service_testimonials (tenant_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_service_testimonials_offer ON offer_service_testimonials (offer_id)"
    )

    # --- offer_service_sales_brief — Adrián-facing sales material (1:1 per offer) ---
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS offer_service_sales_brief (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL REFERENCES tenants(id),
            offer_id UUID NOT NULL,
            candidate_ideal TEXT,
            contraindications TEXT,
            qualification_questions TEXT,
            escalation_conditions TEXT,
            requires_evaluation BOOLEAN NOT NULL DEFAULT false,
            emotional_benefits TEXT,
            pain_of_not_treating TEXT,
            differentiators TEXT,
            promos TEXT,
            faq JSONB NOT NULL DEFAULT '[]'::jsonb,
            objections JSONB NOT NULL DEFAULT '[]'::jsonb,
            keywords JSONB NOT NULL DEFAULT '[]'::jsonb,
            problems_solved TEXT,
            language_to_avoid TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_offer_service_sales_brief_tenant ON offer_service_sales_brief (tenant_id)"
    )
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_offer_service_sales_brief_offer "
        "ON offer_service_sales_brief (offer_id) WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS offer_service_sales_brief")
    op.execute("DROP TABLE IF EXISTS offer_service_testimonials")
    op.execute("DROP TABLE IF EXISTS offer_service_cases")
    op.execute("DROP TABLE IF EXISTS offer_service_specialist_links")
    op.execute("DROP TABLE IF EXISTS offer_service_ext")
