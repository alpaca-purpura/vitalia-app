"""F2-S7 Vitalia lisa-marca: prohibited_phrases table + seed defaults PE.

Story: vitalia-fase2-lisa-marca
Ticket: T-1 — BE migration

Idempotent — uses IF NOT EXISTS / IF EXISTS. Safe to re-run.

Revision ID: 033_vitalia
Revises: 032_vitalia
Create Date: 2026-05-27

downstream-regression-na: brand-local prohibited phrases table; no engine modify.

Architecture notes:
- Table `vitalia_prohibited_phrases` is brand-local (NO engine mirror).
- `tenant_id IS NULL` = seed default (cross-tenant baseline).
- UUID tenant_id = tenant override.
- NO PHI in this table. Owner configuration (brand voice soft warnings).
- Anti-creep: this is NOT a `health_voice_validator` LLM validator.
  It is a configurable soft-warning blocklist per `.claude/rules/sales-agent-brand-voice.md`.
- Seed rows PE are idempotent via ON CONFLICT DO NOTHING.
- 3 composite partial indexes support tenant-override lookup + country seed lookup + phrase lookup.
"""

from __future__ import annotations

from alembic import op

revision = "033_vitalia"
down_revision = "032_vitalia"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ #
    # 1. vitalia_prohibited_phrases (brand-local soft warning blocklist)  #
    # ------------------------------------------------------------------ #
    # This is NOT an LLM health validator (anti-creep per sales-agent-brand-voice.md).
    # It is a configurable phrase list for soft UI warnings only.
    # `tenant_id IS NULL` = global seed default; UUID = per-tenant override.
    op.execute("""
        CREATE TABLE IF NOT EXISTS vitalia_prohibited_phrases (
            id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id           UUID,
            phrase              VARCHAR(200) NOT NULL,
            suggested_alternative VARCHAR(500) NOT NULL,
            severity            VARCHAR(16) NOT NULL DEFAULT 'medium',
            country_scope       VARCHAR(2),
            deleted_at          TIMESTAMPTZ,
            created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at          TIMESTAMPTZ
        );
    """)

    # Index 1: tenant overrides lookup + severity filter (fast fetch per tenant)
    # Partial: only active (non-deleted) rows
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_phrase_tenant_severity "
        "ON vitalia_prohibited_phrases (tenant_id, severity) "
        "WHERE deleted_at IS NULL;"
    )

    # Index 2: country seed defaults lookup (fetch cross-tenant seed per country)
    # Partial: only seed rows (tenant_id IS NULL) + active
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_phrase_country_severity "
        "ON vitalia_prohibited_phrases (country_scope, severity) "
        "WHERE deleted_at IS NULL AND tenant_id IS NULL;"
    )

    # Index 3: phrase text lookup (fast substring match for FE warning detection)
    # Partial: only active rows
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_vit_phrase_lookup "
        "ON vitalia_prohibited_phrases (phrase) "
        "WHERE deleted_at IS NULL;"
    )

    # ------------------------------------------------------------------ #
    # 2. Seed defaults PE — 10 rows (tenant_id IS NULL, country_scope=PE) #
    # ------------------------------------------------------------------ #
    # ON CONFLICT DO NOTHING ensures idempotency on re-run.
    # Phrases verified Spanish neutro LatAm (no voseo). Severity per 03-arch § 9.1.
    # NOTE: Other countries (AR/CL/CO/MX/BR) seeded via dedicated story
    #       `vitalia-fase2-lisa-marca-seed-countries` (state=idea).
    op.execute("""
        INSERT INTO vitalia_prohibited_phrases
            (phrase, suggested_alternative, severity, country_scope)
        VALUES
            ('curamos',                'acompañamos tu tratamiento',                    'high',   'PE'),
            ('garantizado',            'con protocolos avalados',                       'high',   'PE'),
            ('100% efectivo',          'con alta tasa de éxito clínico',               'high',   'PE'),
            ('sin riesgos',            'con protocolos de seguridad clínica',           'high',   'PE'),
            ('tratamiento milagroso',  'tratamiento basado en evidencia',               'medium', 'PE'),
            ('cura definitiva',        'solución duradera respaldada por protocolos',   'high',   'PE'),
            ('sin dolor',              'con técnicas de manejo del dolor',              'medium', 'PE'),
            ('resultados inmediatos',  'resultados visibles según protocolo',           'medium', 'PE'),
            ('los mejores del mercado','con experiencia reconocida en el sector',       'low',    'PE'),
            ('terapia exclusiva',      'terapia especializada',                         'low',    'PE')
        ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS vitalia_prohibited_phrases;")
