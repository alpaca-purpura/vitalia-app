# cap: clinics.lisa.doctores
"""Migration 043 — delta v3 D3-B/D3-D: assets table (engine luana-core-assets).

La tabla del modelo engine ``Asset`` nunca se creó en vitalia: el router proxy se
montó en la story original pero la migración faltó (el upload FE apuntaba a una URL
inexistente → la superficie jamás se ejerció y el hueco quedó latente). Primer uso
real (bio-docs delta v3) lo destapó: ``relation "assets" does not exist``.

DDL espejo de ``core/luana-core-assets/.../asset_model.py`` (post hotfix FK:
``offer_id`` SIN constraint a products — proposal 2026-06-12-assets-offer-fk-hotfix).
Idempotente: IF NOT EXISTS en tabla + índices.

Revision ID: 043_vitalia
Revises: 042_vitalia
"""

from alembic import op

revision = "043_vitalia"
down_revision = "042_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS assets (
            id UUID PRIMARY KEY,
            tenant_id UUID REFERENCES tenants(id),
            offer_id UUID,
            type VARCHAR NOT NULL DEFAULT 'image',
            filename VARCHAR NOT NULL,
            mime_type VARCHAR,
            storage_provider VARCHAR DEFAULT 'local',
            storage_path VARCHAR,
            public_url VARCHAR NOT NULL,
            user_description TEXT,
            ai_metadata JSONB DEFAULT '{}'::jsonb,
            ai_description TEXT,
            ai_colors JSONB DEFAULT '[]'::jsonb,
            status VARCHAR DEFAULT 'processing',
            error_message TEXT,
            scope VARCHAR DEFAULT 'ephemeral',
            purpose VARCHAR DEFAULT 'context_extract',
            extracted_text TEXT,
            extracted_summary VARCHAR,
            extracted_at TIMESTAMPTZ,
            extraction_status VARCHAR DEFAULT 'pending',
            extraction_error TEXT,
            expires_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ DEFAULT now(),
            updated_at TIMESTAMPTZ,
            deleted_at TIMESTAMPTZ
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_offer_id ON assets (offer_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_scope ON assets (scope)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_assets_tenant_id ON assets (tenant_id)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS assets")
