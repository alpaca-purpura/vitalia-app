# Migrations — runbook operativo (vitalia-app)

> SSoT de la doctrina: `.claude/rules/backend-migrations.md` (idempotencia, prohibidos, patterns).
> Este runbook cubre la operación: correr, testear pre-prod y troubleshooting.

## Correr migraciones (dev)

```bash
# Dentro del contenedor backend (runtime Docker — único caso permitido junto a ci-parity):
docker exec luana-dev-vitalia_backend_dev-1 bash -c \
  "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"

# Ver revisión actual:
docker exec luana-dev-vitalia_backend_dev-1 bash -c \
  "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic current"
```

## Crear una migración nueva

1. `alembic current` para obtener `down_revision`.
2. Escribir raw SQL idempotente (`IF NOT EXISTS` / `IF EXISTS`) — NUNCA `op.create_table()` / `add_column()` / `create_index()` ni `sa.Enum()` en `create_table` (ver rule).
3. Aplicar + verificar en dev; correr arch tests de vitalia.

## Test pre-prod — clone DB workflow

```bash
# 1. Crear DB de prueba
createdb migration_test

# 2. Clonar schema de prod (solo schema, sin datos)
pg_dump --schema-only "$PROD_DB" | psql migration_test

# 3. Stampear la revisión actual de prod
${WS}/.venv/bin/alembic -c vitalia/backend/alembic.ini stamp <current_prod_rev>

# 4. Upgrade head contra el clone
${WS}/.venv/bin/alembic -c vitalia/backend/alembic.ini upgrade head

# 5. Limpieza
dropdb migration_test
```

`${WS}` = `$(git rev-parse --show-toplevel)`.

## Troubleshooting

- **Migración re-corre y falla** → no era idempotente. Corregir a `IF NOT EXISTS`/`IF EXISTS` (no revertir).
- **Enum "already exists"** → nunca `sa.Enum(..., create_type=True)`; referenciar el type existente con raw SQL.
- **Down migration** → downgrade no se usa en este flujo; fix-forward con migración nueva.
