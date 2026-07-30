"""F2-S7.bis Vitalia lisa-marca hotfix: personality_profiles engine table.

Story: vitalia-fase2-lisa-marca (hotfix aparte — 500 reportado por Chris 2026-05-29)
Origen: F2-S7 (033) shippeó código que consulta la tabla engine `personality_profiles`
(via luana_core_brand_studio) pero NUNCA creó la tabla en la DB vitalia → 500
`UndefinedTableError: relation "personality_profiles" does not exist` en
GET /api/v1/lisa/marca/personality (lo consumen las sub-secciones Identidad/Voz-y-Tono).

Idempotent — usa IF NOT EXISTS. Safe to re-run.

Revision ID: 034_vitalia
Revises: 033_vitalia
Create Date: 2026-05-29

downstream-regression-na: schema-mirror de tabla engine (backend-ddd.md § schema-mirror
exception). El modelo SSoT vive en
core/luana-core-brand-studio/src/luana_core_brand_studio/infrastructure/models/personality_model.py
::PersonalityProfileModel. Esta migración solo crea el espejo de la tabla en la DB de la
brand (no modifica el engine). NO PHI (config de personalidad de marca, no datos de paciente).

Architecture notes:
- Columnas espejan PersonalityProfileModel verbatim (id, tenant_id, offer_id, avatar_id,
  name, profile_type, preset_key, is_active, dimensions, linguistic_patterns,
  sample_exchanges, negative_constraints, system_instruction, source_metadata,
  qdrant_collection, anchor_count, llm_provider, llm_model, created_at, updated_at, deleted_at).
- Index tenant_id (lookup por tenant) + partial index (tenant_id, is_active) WHERE deleted_at
  IS NULL (soporta el query de get_active_for_tenant: tenant_id + is_active IS true + deleted_at IS NULL).
- Sin seed: get_personality() retorna placeholder vacío si no hay profile activo (200 OK).
"""

from __future__ import annotations

from alembic import op

revision = "034_vitalia"
down_revision = "033_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # personality_profiles (engine table — schema-mirror de               #
    # luana_core_brand_studio.PersonalityProfileModel)                    #
    # ------------------------------------------------------------------ #
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS personality_profiles (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            offer_id UUID,
            avatar_id UUID,
            name VARCHAR(255) NOT NULL,
            profile_type VARCHAR(20) NOT NULL DEFAULT 'preset',
            preset_key VARCHAR(50),
            is_active BOOLEAN NOT NULL DEFAULT false,
            dimensions JSONB NOT NULL DEFAULT '{}'::jsonb,
            linguistic_patterns JSONB NOT NULL DEFAULT '{}'::jsonb,
            sample_exchanges JSONB NOT NULL DEFAULT '[]'::jsonb,
            negative_constraints JSONB NOT NULL DEFAULT '[]'::jsonb,
            system_instruction TEXT,
            source_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
            qdrant_collection VARCHAR(100),
            anchor_count INTEGER NOT NULL DEFAULT 0,
            llm_provider VARCHAR(50),
            llm_model VARCHAR(100),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            deleted_at TIMESTAMPTZ
        );
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_personality_profiles_tenant_id ON personality_profiles (tenant_id);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_personality_profiles_active_lookup "
        "ON personality_profiles (tenant_id, is_active) WHERE deleted_at IS NULL;"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_personality_profiles_active_lookup;")
    op.execute("DROP INDEX IF EXISTS ix_personality_profiles_tenant_id;")
    op.execute("DROP TABLE IF EXISTS personality_profiles;")
