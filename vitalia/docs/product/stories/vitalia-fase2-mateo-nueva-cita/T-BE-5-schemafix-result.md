# T-BE-5-BUGFIX schemafix result

**Story:** vitalia-fase2-mateo-nueva-cita  
**Ticket:** T-BE-5 (BUGFIX — live 500 found during live-verify 2026-06-22)  
**Date:** 2026-06-22  
**Branch:** wip/vitalia

---

## Root cause

`vitalia/backend/src/modules/vitalia/crm/infrastructure/persistence/patient_repository.py` referenced columns `channel_first` and `notes` in:
- `create_minimal()` INSERT (line ~561)
- `search()` SELECT (line ~730)
- `find_by_phone()` SELECT (line ~652)

But those columns did NOT exist in `vitalia_patients`. Live error:
```
sqlalchemy.exc.ProgrammingError: column "channel_first" does not exist
```

GET /api/v1/crm/patients?q= → 500. POST /api/v1/crm/patients → 500.  
35/35 unit tests were green because they mock the repo/DB — never hit the real schema.

---

## Fix

### Migration 051 (idempotent raw SQL)

`vitalia/backend/alembic/versions/051_vitalia_patients_channel_first_notes.py`

```sql
ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS channel_first TEXT;
ALTER TABLE vitalia_patients ADD COLUMN IF NOT EXISTS notes TEXT;
```

**Notes column design choice:** Added nullable, always NULL in inline create flow (inline form sends only name+phone+channel). No PHI written to `notes` by T-BE-5 code path. `TODO(D10): encrypt notes if it ever carries PHI.`

`channel_first` is NOT PHI (acquisition channel metadata — plaintext OK).

Applied to:
- `vitalia_dev` (primary dev DB): migrations 046–051 applied
- `vitalia_test` (pytest DB): migrations 046–051 applied

### Regression tests (TDD — RED first, then GREEN)

`vitalia/backend/tests/modules/vitalia/crm/test_patient_schema_columns_regression.py`

4 integration tests (`pytestmark = pytest.mark.integration`):
1. `test_channel_first_column_exists_in_schema` — queries `information_schema.columns`
2. `test_notes_column_exists_in_schema` — same
3. `test_insert_with_channel_first_and_notes_succeeds` — INSERT referencing both columns, cleans up
4. `test_select_channel_first_from_vitalia_patients_succeeds` — reproduces exact SELECT that caused 500

All 4 were RED before migration 051. All 4 GREEN after.

---

## Gate output

```
# Regression tests (4 new)
vitalia/backend/tests/modules/vitalia/crm/test_patient_schema_columns_regression.py
4 passed in 0.22s

# Full CRM suite
365 passed  (was 361 before new tests)

# Ruff check
All checks passed!

# Ruff format
All files formatted.

# Migration idempotency (re-run upgrade = no-op)
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
(no migration ran — already at head)
```

**Pre-existing arch fitness failure (NOT caused by this PR):**
`test_pgcrypto_phi_columns.py` fails on `treatment_plans.notes defined as TEXT instead of BYTEA` — this failure exists on the clean tree before my changes (verified via git stash test). Out of scope for T-BE-5-BUGFIX.

---

## Files committed

1. `vitalia/backend/alembic/versions/051_vitalia_patients_channel_first_notes.py` — migration 051
2. `vitalia/backend/tests/modules/vitalia/crm/test_patient_schema_columns_regression.py` — regression tests
3. `vitalia/docs/product/stories/vitalia-fase2-mateo-nueva-cita/T-BE-5-schemafix-result.md` — this file
4. `vitalia/docs/product/stories/vitalia-fase2-mateo-nueva-cita/chris-input.md` — APLICADO note
