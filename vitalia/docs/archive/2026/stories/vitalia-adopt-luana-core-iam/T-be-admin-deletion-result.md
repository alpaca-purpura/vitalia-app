# T-be-admin-deletion — Result

**Ticket:** T-be-admin-deletion
**Title:** DELETE phantom code residual (vitalia_clinics queries, imports stub, refs a tablas inexistentes)
**State:** DONE
**Builder:** builder-backend (Sonnet 4.6)
**Session:** 2026-05-19 autonomous E2E

## Summary

Removed all phantom table references from the vitalia admin modules. The original
`tenants.py` and `users.py` contained raw SQL queries against non-existent tables
(`vitalia_clinics`, `vitalia_admin_users`) that caused `OperationalError: no such table`
on every page render post-bcrypt-login.

## Phantom code removed

### vitalia_clinics table references
- `session.execute(select(text("*")).select_from(text("vitalia_clinics")))` — DELETED
- `session.execute(text("SELECT id, name FROM vitalia_clinics WHERE ..."))` — DELETED
- Import `from sqlalchemy import text` no longer needed — REMOVED

### vitalia_admin_users stub
- Raw `session.execute(text("INSERT INTO vitalia_admin_users ..."))` — DELETED
- Direct session queries bypassing any repository — DELETED

### Orphaned imports
- `from sqlalchemy.orm import Session` (was used by raw query) — REMOVED where not needed
- `from vitalia.modules.vitalia.admin._shared.db import get_session` stub — replaced by DI

## Architecture test verification

`test_phantom_tables_zero_refs.py` (NEW arch test) verifies:
1. `test_no_phantom_table_refs_in_admin()` — no references to `vitalia_clinics` table
2. `test_no_session_execute_select_in_admin_modules()` — no `session.execute(...SELECT...)`
3. `test_no_session_execute_insert_in_admin_modules()` — no `session.execute(...INSERT...)`

## Files touched

- `vitalia/backend/src/modules/vitalia/admin/modules/tenants.py` — phantom refs DELETED (same rewrite as T-be-admin-rewrite)
- `vitalia/backend/src/modules/vitalia/admin/modules/users.py` — phantom refs DELETED
- `vitalia/backend/tests/architecture/test_phantom_tables_zero_refs.py` — NEW arch test

## Validators

- ✅ `val-be-arch-phantom-1`: `test_phantom_tables_zero_refs.py::test_no_phantom_table_refs_in_admin` PASS
- ✅ `val-be-arch-phantom-2`: `test_phantom_tables_zero_refs.py::test_no_session_execute_select_in_admin_modules` PASS
- ✅ `val-be-arch-phantom-3`: `test_phantom_tables_zero_refs.py::test_no_session_execute_insert_in_admin_modules` PASS
- ✅ All 256 architecture tests pass

## Impact

Before this ticket: admin panel crashed with `OperationalError: relation "vitalia_clinics" does not exist`
immediately after bcrypt login. After: all 3 admin sections (Tenants, Usuarios, Clínicas) render
without DB errors.
