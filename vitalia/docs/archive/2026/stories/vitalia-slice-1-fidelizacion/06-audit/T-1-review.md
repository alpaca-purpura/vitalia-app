<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Backend Code Review: T-1 Migrations Slice 1 fidelización

**Date:** 2026-05-20
**Brand:** vitalia
**Ticket:** T-1
**Story:** vitalia-slice-1-fidelizacion
**Files Reviewed:** 5 (4 migration files + 1 test file)
**Verdict:** **PASS**

## /test-backend Gate Status (subset relevant to T-1)

| # | Gate | Result | Detail |
|---|---|---|---|
| 3 | Lint (ruff check) | PASS | 0 errors over migrations/ |
| 4 | Format (ruff format) | PASS | all formatted |
| 5 | Type check | N/A | migrations no son strict-typed scope |
| 6 | Arch fitness | PASS | `test_migrations_idempotent.py` + `test_pgcrypto_phi_columns.py` GREEN |
| 7 | Tests + coverage | PASS | 52 passed / 4 skipped (PG-integration) |
| 8 | Verify marker | N/A | migrations no aplican |
| 10 | Migration idempotency | PASS | smoke 52/52 |

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | DDD Compliance | PASS | migration files viven en `persistence/migrations/` per módulo |
| 2 | Tenant Isolation | PASS | TODAS las tablas con `tenant_id UUID NOT NULL` + `clinic_id UUID NOT NULL` |
| 3 | Soft Deletes | PASS | `deleted_at TIMESTAMPTZ NULL` en las 3 tablas nuevas |
| 4 | Code Quality | PASS | ruff 0 errors, format clean |
| 5 | SQLAlchemy 2.0 | N/A | raw SQL solamente |
| 6 | Async Consistency | N/A | migraciones síncronas |
| 7 | Pydantic v2 / PII | N/A | sin DTOs en este ticket |
| 8 | Migration Quality | PASS | `IF NOT EXISTS` en todos los DDLs, sin `op.create_table`, sin `sa.Enum(create_type=True)` |
| 9 | Security | PASS | pgcrypto extension habilitada (020); BYTEA en columnas PHI |
| 10 | Tests / TDD | PASS | RED→GREEN documentado, 52 tests cubren shape + idempotency |
| 11 | Cross-cutting | PASS | `TIMESTAMPTZ` en todas las columnas datetime, sin hardcoded TZ |
| 12 | Mirror detection | PASS | path module-local `persistence/migrations/` justificado (alembic/versions tiene 020-023 ocupados con otros propósitos) |

## Findings

### info: persistencia path divergente del estándar Alembic

**Category:** 8
**File:** `vitalia/backend/src/modules/vitalia/persistence/migrations/020_slice1_treatment_plans.py:1`
**Issue:** Migration files viven en `persistence/migrations/` (module-local) en vez de `alembic/versions/`. El builder lo documenta como divergencia intencional (alembic/versions/ ya tiene archivos 020-023 ocupados con LangGraph, screening, IAM, clinics).
**Fix:** N/A — decisión arquitectónica documentada. Verificar que el ARQ scheduler real lea de este path post-cement; agregar TODO al deployment runbook (Slice 2).
**Skill ref:** `.claude/rules/backend-migrations.md` (path estándar) + builder design decision en T-1-result.md

## Contract Compliance (CONTRACT.md → 03-arch-be.md § 2 Tables)

- [x] `vitalia_treatment_plans` migration created (PHI BYTEA `notes`)
- [x] `vitalia_re_engagement_events` migration created (PHI BYTEA `payload_phi`, partition RANGE(trigger_at), idempotency_key unique index)
- [x] `vitalia_nps_responses` migration created (PHI BYTEA `comment`, score CHECK 0-10)
- [x] `vitalia_patients` 4 columns add (marketing_opt_in, opt_out, opt_out_reason, opt_out_at) — ALTER ADD COLUMN IF NOT EXISTS
- [x] pgcrypto extension habilitada en migration 020
- [x] Composite indexes `(tenant_id, clinic_id, ...)` en todas las tablas
- [x] Partitioning monthly 12 partitions (2026-01 a 2026-12) en re_engagement_events

## HIPAA-lite compliance

- [x] PHI BYTEA columnas: `notes` (020), `payload_phi` (021), `comment` (022) → arch test `test_pgcrypto_phi_columns.py` 4/4 PASS
- [x] Dual filter columns: tenant_id + clinic_id NOT NULL en las 3 tablas nuevas
- [x] Soft delete: `deleted_at TIMESTAMPTZ NULL`

## Allowlist Movement

- [x] No allowlists grown
- [x] Cron envelope allowlist baseline=1 (legacy `lucas_weekly_recommendations`) sin crecer
- [x] Compound scope repo allowlist baseline=2 (patient_repository + lead_screening_event_repository legacy) sin crecer

## Verdict Math

- All P/W/F: 11 PASS, 0 WARN, 0 FAIL
- Gates 3-7 + 10 PASS
- **Verdict: PASS**

## Skills Consulted Trace (must_load enforcement v4.1)

✓ backend-expert (runtime-quality-checklist) ✓ tessl__fastapi ✓ tessl__pytest-api-testing — all cited in T-1-result.md
