# T-2 result · BE config-cuenta (clinics)

> Builder: `builder-backend` (Sonnet) · finalize by `/dev-team` orchestrator (builder stalled at finalize-only; impl complete + GREEN). Story `vitalia-fase2-config-cuenta` · autonomous_mode.

## Estado: pushed · GREEN

## Qué se construyó

**Domain** — `clinics/domain/`:
- `clinic.py` EXTEND: 7 campos nullable back-compat (`legal_name, fiscal_id, address, phone, email, language, currency`).
- `events.py` NEW: `ClinicSpecialtiesChanged` (subclass DomainEvent brand-local).
- `exceptions.py` NEW: `FiscalIdValidationError`, `SpecialtyValidationError`, `ForbiddenError` (field+message Spanish).

**Infrastructure** — `clinics/infrastructure/`:
- `models/clinic_model.py` EXTEND: 7 columnas (`Column()` style, coherente). `language` server_default `es-419`.
- `repositories/clinic_repository.py` EXTEND: `get_active_for_tenant`, `update_account` (tenant-scoped, soft-delete-aware).
- `repositories/clinic_config_repository.py` NEW: read/write `tenant.config_json.clinic_config.primary_specialties` JSONB (engine-boundary RMW · NO column nueva en engine).

**Application** — `clinics/application/clinic_account_service.py` NEW:
- `get_account` · `patch_account` (RBAC 403 · read-only reject 422 · fiscal 422 · specialty 422 · transaction atomic clinic+config_json · `AsyncAuditWriter.write` SYNC pre-response · `ClinicSpecialtiesChanged` best-effort) · `get_specialty_catalog` · `get_dpo_reference`.

**API** — `clinics/api/`:
- `account_router.py` NEW: `GET /` · `PATCH /` · `GET /specialties-catalog` · `GET /dpo` (prefix `/api/v1/clinics/account` · `response_model=` en cada una).
- `dtos.py` EXTEND: `ClinicAccountResponse`, `ClinicAccountPatchRequest`, `SpecialtyCatalogResponse`, `DpoReferenceResponse`.
- `main.py` wiring: `include_router(account_router, prefix="/api/v1/clinics/account")` (notarized · CONN).

**Shared** — `_shared/`:
- `validation/fiscal_id_validator.py` NEW: AR CUIT (mód-11) · UY RUT (mód-11) checksum; PE/MX/CL/CO formato+longitud; país no soportado → freetext degradado (Q1 resuelto).
- `catalogs/specialty_catalog.py` NEW: `SPECIALTY_CATALOG` por país (AR/PE/MX/CL/CO/UY · Tier 1-3 vision) + `FISCAL_ID_LABEL_BY_COUNTRY` + `LANGUAGE_BY_COUNTRY` + `validate_specialties` (Q2 resuelto).

**Migration** — `alembic/versions/039_vitalia_config_cuenta_fields.py`: raw SQL `IF NOT EXISTS` · `down_revision=038_vitalia`. Specialties = CERO migración (JSONB engine).

## Gates (verificado por orchestrator)

| Gate | Resultado |
|---|---|
| `ruff check` (clinics + _shared + tests) | ✅ All checks passed |
| pytest 5 suites nuevas (validator/catalog/repo/service/api) | ✅ 91 passed |
| `test_fe_be_contract_parity.py` (EXTEND CONTRACT_PAIRS · HB-42) | ✅ (FE-pending skip honrado hasta T-1) |
| `test_response_model_required` · `test_vitalia_no_query_without_tenant_filter` · `test_audit_log_sync_write` · `test_migrations_idempotent` | ✅ |
| Migration live `038→039` en dev DB | ✅ aplicada · 7 columnas confirmadas en `vitalia_clinic_branches` |
| Smoke endpoint mounted | ✅ `GET /api/v1/clinics/account/` → 422 (auth-missing, NO 404) |

## Notas para T-1 (FE) — contrato live exacto

- **Trailing slash:** `redirect_slashes=False` + router path `/` → URL canónica **`/api/v1/clinics/account/`** (con barra). FE debe llamar con barra exacta (lección embudo — match live, no imaginar).
- Paths: `GET/PATCH /api/v1/clinics/account/` · `GET /api/v1/clinics/account/specialties-catalog` · `GET /api/v1/clinics/account/dpo`.
- DTO `ClinicAccountResponse` = SSoT camelCase mirror (03-arch § 5). CONTRACT_PAIR registrado → el FE-side del gate pasa a HARD cuando exista `cuenta.types.ts`.

## Skills consulted (must_load enforcement v4.1)

| Skill / Rule | Status | When |
|---|---|---|
| backend-expert | ✅ | DDD/SQLA/Pydantic/migration |
| brand-expert | ✅ | specialties en config_json (no Clinic) |
| .claude/rules/backend-ddd.md | ✅ | domain purity + DTO thin |
| .claude/rules/tenant-isolation.md | ✅ | tenant_id en toda query |
| .claude/rules/backend-migrations.md | ✅ | IF NOT EXISTS · down_revision |
| .claude/rules/anti-duplication.md | ✅ | NEW justificado (no mirror) |
| .claude/rules/spanish-text.md | ✅ | error messages neutro |
| .claude/rules/pii-sanitisation.md | ✅ | response_model + audit sin PHI |
| vitalia/.claude/rules/hipaa-lite.md | ✅ | audit sync · clinic non-PHI rationale |

## Pre-existing red (NO de esta story · documentado anti-egoísmo)

`tests/architecture/test_pgcrypto_phi_columns.py::test_no_phi_column_uses_text_or_varchar_unencrypted` falla con `treatment_plans.notes defined as TEXT instead of BYTEA`. `treatment_plans` lo define migración **005** (módulo treatment/crm, committed mucho antes); config-cuenta NO lo toca; el test no está en los `architecture_gates` declarados de esta story. Deuda pgcrypto del módulo treatment → ruteo `/pm-vitalia` (fuera de scope clinics).

## Auto-fix loop iter 1 response (2026-06-12 · C9-1)

**Finding:** T-2-review.md § FAIL C9-1 — audit_log row rollback silencioso (sesión non-committing).

**Fix aplicado (Option A del auditor — restaura también atomicidad C1-2):**
- `account_router.py::_get_db` → `get_async_session_committing` (patrón marca_router; docstring explica el porqué)
- `clinic_repository.py::update_account` + `clinic_config_repository.py::update_specialties` → commits internos QUITADOS (caller-owned unit-of-work). Los commits de `create`/`soft_delete` (otros consumers) intactos — cambio mínimo.
- Resultado: clinic fields + specialties + audit row commitean ATÓMICOS al return; raise → rollback de los tres.
- C9-3: `get_dpo` con guard `UUID(tenant_id)` → 422 (consistencia siblings). C9-4: doble query colapsada.

**TDD:** `tests/modules/vitalia/clinics/test_account_audit_durability.py` NUEVO — integration (real session vs dev DB, `@pytest.mark.integration`): PATCH real → assert `COUNT(vitalia_audit_log WHERE action='clinic_account_patch') ≥ 1` + persist + atomicidad. RED pre-fix (0 rows) → GREEN post-fix.

**Gates (verificados por /auditor orchestrator):**
- ruff + format clean · clinics suite 0 FAILED (incl. integration test) · 5 arch gates 0 FAILED
- **LIVE re-verify:** `PATCH /api/v1/clinics/account/ → 200` → `SELECT COUNT(*) FROM vitalia_audit_log WHERE action='clinic_account_patch'` → **1** (antes del fix: 0 pese a PATCHes 200). La fila REAL existe — no la structlog line.

**Files touched:** account_router.py · clinic_repository.py · clinic_config_repository.py · test_account_audit_durability.py (NEW)
