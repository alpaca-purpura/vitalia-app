# T-1 Result — Migración 035 PHI base tables

**Story:** vitalia-crm-phi-base-tables-migration  
**Ticket:** T-1 — Migración 035 + arch test + idempotency test  
**State:** tests-passing  
**Commit:** 540249cb  
**Branch:** wip/vitalia  
**Date:** 2026-05-30  

## Skills Consulted (must_load enforcement v4.1)

| Skill | Invocada | Decisión tomada |
|---|---|---|
| `backend-expert` | Sí — SKILL.md + `references/runtime-quality-checklist.md` | Raw SQL `op.execute(...)` only; no `op.create_table()`/`op.add_column()`; `IF NOT EXISTS` everywhere; no `sa.Enum(create_type=True)`. TDD RED-first antes de código. |
| `.claude/rules/backend-migrations.md` | Sí | Forward-only idempotente: todo DDL en `op.execute(...)` con `IF NOT EXISTS`/`IF EXISTS`. Prohibido `op.create_table()`, `sa.Enum()`. Test en schema clone antes de prod. |
| `vitalia/.claude/rules/hipaa-lite.md` | Sí | PHI columns BYTEA (pgcrypto inline, NO trigger+GUC). Dual filter `tenant_id+clinic_id` en patients. No indexes sobre ciphertext (ADR-007 D4). KEK desde env (nunca log). |
| `.claude/rules/tdd-mandatory.md` | Sí | Test idempotency RED-first (escrito con especificación exacta antes del código). 46 tests estáticos (static analysis del archivo migración) cubren todos los casos. |
| `03-arch.md § 2-3` | Sí | Schema canónico derivado: patients 016 skeleton + PHI BYTEA cols; leads net-new. Drift fix: CREATE TABLE IF NOT EXISTS patients abre 035 para DB driftada. |
| `ADR-vitalia-007 D3-D5` | Sí | D3: qué cols cifrar (patients: name/dob/dni/phone/email/address; leads: name/email/phone/notes; marketing_opt_out_at = TIMESTAMPTZ no BYTEA). D4: NO index sobre ciphertext. D5: downgrade NO dropea vitalia_patients ni pgcrypto. |

## Archivos creados / modificados

| Archivo | Operación | Descripción |
|---|---|---|
| `vitalia/backend/alembic/versions/035_vitalia_crm_phi_base_tables.py` | NUEVO | Migración forward-only idempotente. revision=035_vitalia, down_revision=034_vitalia. |
| `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py` | MODIFICADO | Extendido PHI_BYTEA_COLUMNS con 10 entradas + 6 métodos test para migration 035. |
| `vitalia/backend/tests/migrations/test_035_crm_phi_base_tables_idempotency.py` | NUEVO | TDD RED-first: 46 tests estáticos + 4 integration (skip DB). |

## Gates — output literal

### Ruff check
```
All checks passed!
```

### Ruff format
```
3 files already formatted
```

### test_pgcrypto_phi_columns.py (arch gate AV-pgcrypto-bytea-gate)
```
============================= test session starts ==============================
collected 15 items
tests/architecture/test_pgcrypto_phi_columns.py ...............  [100%]
============================== 15 passed in 0.22s ==============================
```

### Architecture suite completa (NF-arch-fitness)
```
330 passed, 2 warnings in 3.70s
```
Warnings son `PytestUnknownMarkWarning` no relacionadas con esta story (pre-existentes).

### test_035_crm_phi_base_tables_idempotency.py (F-migration-idempotency)
```
============================= test session starts ==============================
collected 50 items
tests/migrations/test_035_crm_phi_base_tables_idempotency.py .....(46 static)....ssss  [100%]
======================== 46 passed, 4 skipped in 0.19s =========================
```
4 integration tests skipped — Postgres no disponible en entorno nativo de test.
Documentados como pendientes para T-3 (verificación live supervisada).

### AV validators
```
AV-no-016-edit:        OK 016 intacto
AV-no-engine-edit:     OK no engine edits
AV-no-cross-brand:     OK no cross-brand
AV-no-index-on-ciphertext: OK sin indice sobre cifrado
AV-pgcrypto-bytea-gate: 15 passed (arch test GREEN)
```

## Decisiones de implementación

### Drift fix (crítico)
La DB dev está stampeada a 034 pero `vitalia_patients` no existe físicamente. La migración 035 abre con `CREATE TABLE IF NOT EXISTS vitalia_patients (...)` con el esqueleto completo de 016 ANTES de los `ADD COLUMN IF NOT EXISTS` PHI. En DB limpia (futura), 016 crea el esqueleto y 035 solo agrega PHI — ambos paths convergen idempotentes.

### marketing_opt_in en vitalia_leads
Incluido como `BOOLEAN NOT NULL DEFAULT FALSE` per el comentario del caller ("el lead_service.create lo pasa"). A verificar en T-2 contra el repo.

### Arch test extendido
El test usa `re.search` + fallback OR para detectar BYTEA en contexto de tabla. La búsqueda buscará `ADD COLUMN IF NOT EXISTS {col} BYTEA` (pattern exacto para patients) y `{col} BYTEA` (dentro del CREATE TABLE para leads). Ambos verifican contra la fuente de TODAS las migraciones concatenadas.

### Downgrade body parsing
El test `TestMigration035Downgrade._downgrade_body()` usa `_strip_docstrings_and_comments()` para evitar que las líneas `# NOTE: pgcrypto ... is NOT dropped` en los comentarios falsamente activaran el regex de drop. Bug detectado y corregido en el mismo ciclo (GREEN sin código extra).

## Nota sobre tests de integración (DB)

Los 4 tests `@pytest.mark.integration` (verificación real en DB) están marcados con `skipif(not _is_postgres_available(), ...)`. En el entorno nativo sin Docker activo se saltan. La verificación real de la migración contra DB ocurrirá en T-3 (supervisada por Chris) con:
```bash
docker exec luana-dev-vitalia_backend_dev-1 bash -lc 'cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head'
```

## Próximo paso (T-2)

T-2: Repos decrypt wiring + KEK config. Depende del schema creado por T-1.
Rutas: `patient_repository.py` + `lead_repository.py` + `router.py` + `.env.dev.template` + `docker-compose.dev.yml`.
