<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 -->
# Backend Code Review: T-4 BE fideliz domain + infrastructure

**Date:** 2026-05-20
**Brand:** vitalia
**Ticket:** T-4
**Files Reviewed:** 13 (4 VOs + 3 entities + 1 events file + 3 models + 3 repos + 6 test files)
**Verdict:** **WARN**

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | Inside-Out estricto: domain pure pydantic+stdlib; infrastructure SA 2.0+repos; correcta separación |
| 2 | Tenant Isolation | PASS | `CompoundScopeRepositoryBase(scope_field="clinic_id")` + dual filter `tenant_id + clinic_id` en TODA query (verificado en `re_engagement_event_repository.py` line 94-95, 127-128, 162-163, 202-203). HIPAA-lite refuerzo aplicado |
| 3 | Soft Deletes | PASS | `deleted_at: Mapped[datetime \| None]` en 3 modelos + soft-delete consistente |
| 4 | Code Quality | PASS | ruff `vitalia/backend/src/modules/vitalia/fidelizacion/` 0 errors. Format check clean |
| 5 | SQLAlchemy 2.0 | PASS | `mapped_column()` + `Mapped[]` + `select()` — no Column() ni session.query(). Composite PK `(id, trigger_at)` para RANGE partitioning |
| 6 | Async Consistency | PASS | Todos los repos `async def`, `AsyncSession` injected, `await session.execute(stmt)` |
| 7 | Pydantic v2 / PII | PASS | `ConfigDict(from_attributes=True)` en las 3 entidades. PHI fields tipados `bytes \| None` (notes/payload_phi/comment) |
| 8 | Migration Quality | WARN | Ver finding § F2 — `nps_responses.comment` BYTEA presente pero migration 022 sin `pgcrypto` trigger/funciones encrypt; cifrado deferred a deployment runbook (arch test `test_pgcrypto_phi_columns.py` no cubre nps_responses.comment — gap allowlist) |
| 9 | Security | WARN | `nps_response_model.comment` recibe plaintext bytes vía `.encode("utf-8")` desde NPSService — verdadero cifrado pgcrypto NO está implementado en ninguna capa. Spec hipaa-lite.md exige `pgcrypto symmetric encryption` para PHI columnas. Ver § F2 |
| 10 | Tests / TDD | PASS | 67 unit tests (55 domain + 12 infra contract) RED→GREEN documentado. Cross-tenant query test cubre SC-04 |
| 11 | Cross-cutting | PASS | `TIMESTAMPTZ` (`DateTime(timezone=True)`) en todas las columnas datetime. UTC consistente. structlog only |
| 12 | Mirror detection | PASS | `CompoundScopeRepositoryBase` consumido del engine (`luana_core_platform.repositories.compound_scope_repository`). `DomainEvent` consumido del engine. NO mirror cross-brand (verified grep) |

## Findings

### WARN F2 — `nps_responses.comment` PHI plaintext en BYTEA sin pgcrypto

**Category:** 8 (Migration Quality) + 9 (Security)
**Files:**
- `vitalia/backend/src/modules/vitalia/persistence/migrations/022_slice1_nps_responses.py` (no `EXTENSION pgcrypto` ni `pgp_sym_encrypt/decrypt` trigger)
- `vitalia/backend/src/modules/vitalia/fidelizacion/application/services/nps_service.py:129` — `comment_bytes = comment_plain.encode("utf-8")` (plaintext bytes)
- `vitalia/backend/tests/architecture/test_pgcrypto_phi_columns.py:20-24` — `PHI_BYTEA_COLUMNS` allowlist NO incluye `("nps_responses", "comment")` (gap arch coverage)

**Issue:** El campo `comment` (free-text del paciente, PHI per hipaa-lite.md § PHI fields canónicos) usa BYTEA pero el contenido es plaintext UTF-8, NO pgcrypto-encrypted. Spec hipaa-lite.md § Encryption at rest exige: "Tabla `patient_medical_records` columnas `diagnosis`, `treatment_plan`, `medical_notes` → `pgcrypto` symmetric encryption con KEK rotada anualmente". NPS comment es PHI free-text equivalente. El docstring de `nps_service.py:127-128` afirma "El cifrado real ocurre en la DB mediante pgcrypto trigger (migration 022)" — afirmación FALSA, no existe trigger.

**Fix sugerido (Slice 2 deferral aceptable si documentado):**
1. Migration 024 (Slice 2): habilitar `CREATE EXTENSION IF NOT EXISTS pgcrypto;` + trigger `BEFORE INSERT/UPDATE ON vitalia_nps_responses` que aplica `pgp_sym_encrypt(NEW.comment_plain, current_setting('app.kek'))`.
2. Mientras tanto: **eliminar afirmación falsa en docstring nps_service.py:127-128** (riesgo de aceptar PR a prod con afirmación incorrecta). Reemplazar por: "PHI comment stored as BYTEA — encryption at rest deferred to deployment-level Postgres TDE (transparent disk encryption) per Slice 1 acceptable risk. Slice 2 migrates to pgcrypto symmetric column-level."
3. Agregar `("nps_responses", "comment")` a `PHI_BYTEA_COLUMNS` en `test_pgcrypto_phi_columns.py` (mínimo cierre del gate; cierra escape).

**Skill ref:** `vitalia/.claude/rules/hipaa-lite.md` § Encryption at rest

**Severity:** WARN (no es leak inmediato — BYTEA + disk encryption sirve mientras esté en infra cloud con disk encryption; pero contradice el contrato cementado y arch test no enforce).

### info — Repository PARTITIONED model PK

**File:** `vitalia/backend/src/modules/vitalia/fidelizacion/infrastructure/models/re_engagement_event_model.py`
**Issue:** Composite PK `(id, trigger_at)` correcto para RANGE partitioning (migración 021 `PARTITION BY RANGE (trigger_at)`). T-4-result.md cita explícitamente esta decisión. **No es finding** — es correctness note.

## Allowlist Movement

- `test_compound_scope_repository_used.py` baseline=2 — sin growth, 3 nuevos repos (treatment_plan, re_engagement_event, nps_response) PASS sin allowlist (inherit engine base directly).
- `test_phi_dual_filter.py` — sin growth.

## Gherkin coverage verification

| Scenario | Mapping | Status |
|---|---|---|
| SC-04 Adversarial cross-tenant query 404 | `test_re_engagement_event_repository.py::test_cross_tenant_query_returns_404` | EXISTS (smoke-marked integration; runs in clinic dual-filter contract) |

## Verdict Math

- 10 PASS + 2 WARN (Cat 8 + Cat 9 cohesivos en F2) + 0 FAIL → **WARN**
- WARN no bloquea merge per ratchet (Cat 9 deferral aceptable si commit body lo documenta); F2 fix sugerido a Slice 2 + docstring fix puede ir self-fix iter

## Skills Consulted Trace

✓ backend-expert (runtime-quality-checklist) ✓ tessl__fastapi (Pydantic v2 patterns) ✓ tessl__pytest-api-testing (fixture scoping)
