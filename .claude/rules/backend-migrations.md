# Migrations

> **Always-on DEFINITIVO (decisión 2026-06-09 — sesión integración, Tier-2 evaluado y DESCARTADO).** El read-trigger `paths:` NO cubre el flujo real: una migración nueva puede nacer vía `Write` from-scratch con `down_revision` obtenido por `alembic current` (bash, HB-37) — cero `Read` de `alembic/versions/**` → la rule no cargaría justo en el write que debe proteger (#23478: `paths:` es read-only). El flujo autogenerate+Edit SÍ leería, pero la cobertura parcial no alcanza para un gate de DDL idempotente (riesgo = prod). Backstops existentes (builder-backend prompt verbatim + arch tests) son defensa-en-profundidad, no reemplazo. El `globs:` previo era frontmatter MUERTO (mecanismo confirmado ignorado).

Idempotentes. Raw SQL `IF NOT EXISTS`.

## Patterns
```python
op.execute("CREATE TABLE IF NOT EXISTS ...")
op.execute("ALTER TABLE x ADD COLUMN IF NOT EXISTS ...")
op.execute("CREATE INDEX IF NOT EXISTS ...")
# Enums: raw SQL ref existing types. NUNCA sa.Enum()/postgresql.ENUM() en op.create_table()
```

## Prohibido
`op.create_table()`/`add_column()`/`create_index()` (no idempotentes). `sa.Enum(..., create_type=True)` (broken SA 2.0.27).

## Test pre-prod
Clone DB workflow — runbook `docs/domains/migrations.md` (MISSING — runbook pendiente). Steps manuales mientras no existe:
1. Crear `migration_test` DB (`createdb migration_test`)
2. `pg_dump --schema-only $PROD_DB | psql migration_test`
3. `alembic -c {brand}/backend/alembic.ini stamp <current_prod_rev>`
4. `${WS}/.venv/bin/alembic -c {brand}/backend/alembic.ini upgrade head`
5. `dropdb migration_test`
