# migration_notes.md — ESC-6 prompt_versions.tenant_id (brand-authored)

> **Por qué acá y no en una migración:** no existe alembic en `core/` — las 4 marcas son dueñas de SUS migraciones
> (`target_metadata=None`, raw SQL idempotente). + constraint dura "cero marca en el worktree core". Por eso el lift
> entrega **el modelo** (`prompt_versions.tenant_id` en `core/luana-core-sales-agent`) y **estas notas**; cada brand
> consumer autorea la migración en SU worktree (`wip/{brand}`) al adoptar el engine hardened.
>
> **Verificado in-tree:** `prompt_versions` NO aparece en el alembic de ninguna marca (grep vacío) → la migración debe
> **crear la tabla** (IF NOT EXISTS) además de agregar la columna, para que el grafo en modo `HYBRID/DB` cargue prompts.

## DDL idempotente (a copiar en la migración de cada brand)

Patrón del repo (raw SQL `IF NOT EXISTS` · NUNCA `op.create_table()`/`sa.Enum(create_type=True)` · ver `.claude/rules/backend-migrations.md`):

```python
def upgrade() -> None:
    # 1. Tabla del engine sales_agent — crear si no existe (idempotente)
    op.execute("""
        CREATE TABLE IF NOT EXISTS prompt_versions (
            id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            key           VARCHAR NOT NULL,
            version       INTEGER NOT NULL,
            content       TEXT NOT NULL,
            is_active     BOOLEAN DEFAULT TRUE,
            change_reason VARCHAR,
            author_id     VARCHAR,
            metadata_info JSONB DEFAULT '{}'::jsonb,
            tenant_id     UUID,                      -- ESC-6: scoping por tenant (NULL = system default)
            created_at    TIMESTAMPTZ DEFAULT now()
        )
    """)
    # 2. Columna ESC-6 — para DBs donde la tabla YA existía sin tenant_id (idempotente)
    op.execute("ALTER TABLE prompt_versions ADD COLUMN IF NOT EXISTS tenant_id UUID")
    # 3. Índices (idempotente)
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompt_versions_key ON prompt_versions (key)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_prompt_versions_tenant_id ON prompt_versions (tenant_id)")

def downgrade() -> None:
    # Conservador: solo dropear la columna ESC-6 (no la tabla — puede tener defaults sembrados)
    op.execute("DROP INDEX IF EXISTS ix_prompt_versions_tenant_id")
    op.execute("ALTER TABLE prompt_versions DROP COLUMN IF EXISTS tenant_id")
```

> `gen_random_uuid()` requiere `pgcrypto` (vitalia ya lo habilita en migración 035 — `CREATE EXTENSION IF NOT EXISTS pgcrypto`). Si una brand no lo tiene, prepender `op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")`. Alternativa sin extensión: omitir el `DEFAULT` y dejar que el ORM genere el `id` (`default=uuid.uuid4` ya en el modelo).

## Backfill

**No-op.** Las filas existentes son system defaults → `tenant_id` queda `NULL`, que es exactamente la semántica del fallback
en `base.py` (`PromptVersion.tenant_id.is_(None)` = system default). No hay que migrar datos.

## Orden de adopción por brand

1. Merge del lift a `main` (engine hardened con el modelo `tenant_id`).
2. Sync `wip/{brand}` ← `main` (la brand ve el modelo nuevo).
3. La brand autorea esta migración en `wip/{brand}/backend/alembic/versions/NNN_{brand}_prompt_versions_tenant_id.py`
   (`down_revision` = `alembic current` de esa brand · HB-37) + `alembic upgrade head`.
4. Verificar: el grafo en modo `HYBRID/DB` carga prompts por tenant sin error (parte del efecto runtime).

## Brands que la necesitan

- **vitalia** — 1er consumidor (cierra el G de `vitalia-fase2-adrian-canal-inbound`). PRIORITARIA.
- **nicolify / comunify** — cuando cableen su agente de ventas.
- **lupulo** — al bootstrap (hereda el engine ya hardened).
