# T-be-admin-rewrite — Result

**Ticket:** T-be-admin-rewrite
**Title:** REWRITE admin/modules/{tenants,users}.py consumiendo engine repos (CERO SQL crudo)
**State:** DONE
**Builder:** builder-backend (Sonnet 4.6)
**Session:** 2026-05-19 autonomous E2E

## Summary

Rewrote `vitalia/backend/src/modules/vitalia/admin/modules/tenants.py` and
`vitalia/backend/src/modules/vitalia/admin/modules/users.py` to consume
engine IAM repositories from `luana_core_iam` instead of raw SQL via `session.execute()`.

Also created:
- `vitalia/backend/src/modules/vitalia/admin/modules/clinics.py` — new admin page for clinics
- `vitalia/backend/src/modules/vitalia/admin/pages/clinicas.py` — Streamlit page wrapper
- `vitalia/backend/src/modules/vitalia/admin/api/admin_helpers_router.py` — internal endpoints
  for Playwright DB verification (guarded by X-Internal-Token header)
- `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` — SSoT sync audit log helper

## Architecture changes

### tenants.py
- **Before:** `session.execute(select(text("*")).select_from(text("vitalia_clinics")))` (phantom table)
- **After:** `TenantRepository(session).list_all()` returning `Tenant` domain objects

Key features:
- `render_tenant_list()`: calls `TenantRepository.list_all()`, renders dataframe with Nombre/Slug/Estado
- `render_create_tenant()`: validates slug uniqueness → `TenantRepository.create()` → audit log
- `render_suspend_tenant()`: `TenantRepository.get_by_id()` → `update(is_active=not current)` → audit log
- Audit log: `write_audit_log_sync(action="tenant.create|tenant.suspend|tenant.activate", resource_type="tenant", ...)`

### users.py
- **Before:** Raw SQL joins or missing implementation
- **After:** `UserRepository(session)` + `UserTenantRepository(session)` from luana_core_iam

Key features:
- `render_user_list()`: `UserRepository.list_all()` with optional tenant filter via `UserTenantRepository`
- `render_create_user()`: `UserRepository.create()` → optionally `UserTenantRepository.link()` → audit log
- `render_ban_user()`: `UserRepository.update(is_active=False)` → audit log `user.ban`

### admin_helpers_router.py
FastAPI router (registered in vitalia `main.py`) exposing:
- `GET /api/v1/vitalia/admin/db-state` — returns row counts `{tenants, users, user_tenants, clinics}`
- `GET /api/v1/vitalia/admin/audit-log` — returns sanitized entries filtered by action/since
- Both guarded by `X-Internal-Token` header (value from `VITALIA_INTERNAL_API_TOKEN` env var)
- `response_model=DbStateResponse | list[AuditLogEntry]` (PII allowlist — no raw PHI)

### audit_writer.py
SSoT helper `write_audit_log_sync()` used by all admin modules and clinics service.
Per HIPAA-lite rule: sync write (not fire-and-forget), includes tenant_id + clinic_id (dual filter).

## Files touched

- `vitalia/backend/src/modules/vitalia/admin/modules/tenants.py` — REWRITE
- `vitalia/backend/src/modules/vitalia/admin/modules/users.py` — REWRITE
- `vitalia/backend/src/modules/vitalia/admin/modules/clinics.py` — NEW
- `vitalia/backend/src/modules/vitalia/admin/pages/clinicas.py` — NEW
- `vitalia/backend/src/modules/vitalia/admin/api/admin_helpers_router.py` — NEW
- `vitalia/backend/src/modules/vitalia/audit/audit_writer.py` — NEW
- `vitalia/backend/src/modules/vitalia/audit/__init__.py` — NEW
- `vitalia/backend/tests/modules/vitalia/admin/` — NEW (test files)
- `vitalia/backend/tests/modules/vitalia/audit/` — NEW (test files)

## Validators

- ✅ `val-be-arch-admin-1`: `test_admin_consumes_engine_repos.py` — admin imports from luana_core_iam
- ✅ `val-be-arch-admin-2`: `test_admin_no_raw_sql.py` — no `session.execute` in admin modules
- ✅ `val-be-unit-admin-1`: 37 unit tests in `tests/modules/vitalia/admin/` — all PASS
- ✅ `val-be-unit-audit-1`: audit writer tests — all PASS
- ✅ `val-be-lint`: ruff check 0 errors, ruff format 0 diffs

## Test results

```
vitalia/backend/tests/modules/vitalia/admin/ — 37 tests PASS
vitalia/backend/tests/modules/vitalia/audit/ — tests PASS
vitalia/backend/tests/architecture/test_admin_consumes_engine_repos.py — PASS
vitalia/backend/tests/architecture/test_admin_no_raw_sql.py — PASS
```
