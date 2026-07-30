# 05-guidelines — vitalia-crm-phi-base-tables-migration

> Guía operativa para `builder-backend`. Lee 03-arch.md (schema canónico + decrypt pattern) + ADR-vitalia-007 ANTES de codear. TDD RED-first por capa.

## must_load_skills (verbatim — el builder los cita en T-{n}-result.md "Skills consulted")

- `backend-expert`
- `tessl__fastapi`
- `tessl__pytest-api-testing`
- `.claude/rules/backend-migrations.md`
- `.claude/rules/tenant-isolation.md`
- `.claude/rules/backend-ddd.md`
- `vitalia/.claude/rules/hipaa-lite.md`
- `.claude/rules/tdd-mandatory.md`
- `.claude/rules/test-design-doctrine.md`

## must_load_artifacts

- `vitalia/docs/product/stories/vitalia-crm-phi-base-tables-migration/01-spec.md` (§ Schema esperado + 5 scenarios)
- `vitalia/docs/product/stories/vitalia-crm-phi-base-tables-migration/03-arch.md` (§ 2 schema canónico + § 4 decrypt pattern + § 3 migración)
- `vitalia/docs/product/stories/vitalia-crm-phi-base-tables-migration/04-validators.yaml` (test_construction_plan + manual_audit)
- `vitalia/docs/architecture/ADR-vitalia-007-phi-pgcrypto-encryption.md` (decisión KEK + downgrade + cifrado)
- `vitalia/docs/learnings/2026-05-30-clerk-godmatrix-mint-live-verification.md` (mint JWT real para verificación live)

## Patterns REQUIRED

- **pgcrypto inline:** `pgp_sym_encrypt(:val, :kek)` al escribir PHI · `pgp_sym_decrypt(col, :kek)::text AS col` al leer. KEK = `KEKClient.get_key()` bindeada como `:kek`. NO trigger+GUC (ver ADR-007 D1).
- **Migración idempotente:** `op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")` + `CREATE TABLE IF NOT EXISTS` + `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` + `CREATE INDEX IF NOT EXISTS`. Raw SQL only. revision `035_vitalia`, down_revision `034_vitalia`.
- **KEK injection:** `PatientRepository(session, audit_repo, kek=KEKClient.from_env())` en el router; default param `kek=None` → `KEKClient.from_env()` interno (back-compat tests).
- **Dual filter:** patient queries filtran `tenant_id + clinic_id` (incl get_by_id) vía `validate_dual_filter`; leads filtra `tenant_id`. Ya existe — NO romper.
- **Audit sync write:** pre-response, `await audit_repo.write(...)`. Ya existe — NO romper.
- **structlog only** (no print/logging). KEK/PHI NUNCA en log args.
- **response_model=** en todo endpoint (ya está; NO ampliar el payload expuesto al descifrar — `PatientResponse` allowlist sin dni/dob/address).
- **date_of_birth:** cifrado BYTEA; al descifrar `pgp_sym_decrypt(...)::text` → parsear a `datetime` UTC-aware en el repo; NULL → None.
- **Seed cifrado:** INSERT con `pgp_sym_encrypt(%(val)s, %(kek)s)` (psycopg2), KEK desde `os.environ["VITALIA_PHI_KEK"]`, paciente Sanaré id determinístico, datos LatAm neutros realistas.
- **TDD RED-first** por capa: migration idempotency → repo round-trip → integration endpoints. RED antes de GREEN.

## Patterns FORBIDDEN

- ❌ Editar `016_vitalia_patients_columns.py` ni ninguna migración aplicada (forward-only).
- ❌ Editar `core/luana-core-*/src/`, `nicolify/`, `comunify/`, `lupulo/`, `vitalia/backend/src/modules/vitalia/{copilot,sales_agent}/`.
- ❌ Crear un nuevo KEK layer (EXTEND `_shared/encryption/kek_client.py` existente — NO-NEW-LAYER).
- ❌ Adoptar el trigger+GUC de 025 (KEK GUC nunca inyectada → roto en runtime).
- ❌ Índice sobre columna cifrada (`name/dni/email/phone/address/notes`).
- ❌ KEK hardcodeada en código o logueada (structlog/traces/transcript/print).
- ❌ `op.create_table()` / `sa.Enum(create_type=True)` / migración no idempotente.
- ❌ Downgrade que dropee `vitalia_patients` (016 la owna) o `DROP EXTENSION pgcrypto`.
- ❌ Monkeypatch del repo en integration (ejerce tablas reales; monkeypatch SOLO `verify_token_payload`).
- ❌ PHI plaintext en logs sin sanitize; PHI en URL/query params.
- ❌ Declarar "verificado" por un GET 200 sin ejercer write + leer logs (verification-real-not-200).

## Files in scope

| Path | Acción |
|---|---|
| `vitalia/backend/alembic/versions/035_vitalia_crm_phi_base_tables.py` | crear |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/patient_repository.py` | decrypt/encrypt + KEK |
| `vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/lead_repository.py` | decrypt + KEK (+ create/update si insert vive aquí) |
| `vitalia/backend/src/modules/vitalia/crm/api/router.py` | inyectar KEKClient en repos |
| `vitalia/backend/scripts/seed_test_users_link.py` | + paciente Sanaré cifrado |
| `vitalia/.env.dev.template` | + `VITALIA_PHI_KEK` (dev hex) |
| `vitalia/docker-compose.dev.yml` | passthrough `VITALIA_PHI_KEK` |
| `vitalia/backend/tests/migrations/test_035_crm_phi_base_tables_idempotency.py` | crear |
| `vitalia/backend/tests/integration/test_crm_phi_real_tables.py` | crear |
| `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py` | extender PHI_BYTEA_COLUMNS |

## Files explicitly OUT of scope (no tocar)

- `016_vitalia_patients_columns.py` y toda migración ≤034.
- `_shared/encryption/kek_client.py` (consumir, NO modificar salvo bugfix trivial documentado).
- `_shared/repositories/{phi_repository,audit_log_repository}.py` (reusar, NO modificar).
- `crm/domain/{patient,lead}.py` (entidades sin cambio — cifrado es infra).
- Las 5 migraciones legacy en `src/modules/vitalia/persistence/migrations/` (documentar arqueológicas, NO limpiar inline — OQ-2 follow-up).

## Quality gates pre-cierre (native, root venv)

```bash
WS=$(git rev-parse --show-toplevel)
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff check src/modules/vitalia/crm/ alembic/versions/035_*.py scripts/seed_test_users_link.py
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/ruff format --check .
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/architecture/ -x -q
cd ${WS}/vitalia/backend && ${WS}/.venv/bin/pytest tests/migrations/test_035_crm_phi_base_tables_idempotency.py tests/integration/test_crm_phi_real_tables.py tests/modules/vitalia/crm/ -v
# Aplicar + verificación live (supervisada):
docker exec luana-dev-vitalia_backend_dev-1 bash -lc "cd /workspace/vitalia/backend && /workspace/.venv/bin/alembic upgrade head"
# → re-god-matrix mint (ver 04-validators § manual_audit)
```
